from __future__ import annotations

from app.drive_reader import DriveReader, FAT32Layout, FAT32ReaderError, format_bytes
from app.section1_boot_sector_reader import BootSectorReader


class TxtFileEntry:
    def __init__(self, file_name: str, directory_path: str, file_size: int, starting_cluster: int) -> None:
        self.file_name = file_name
        self.directory_path = directory_path
        self.file_size = file_size
        self.starting_cluster = starting_cluster

    def get_directory_display(self) -> str:
        if self.directory_path:
            return self.directory_path
        return "/"

    def get_size_display(self) -> str:
        return f"{self.file_size:,} bytes ({format_bytes(self.file_size)})"


class TxtFileScanner:
    FAT_ENTRY_SIZE = 4
    FAT32_CLUSTER_MASK = 0x0FFFFFFF
    FAT32_BAD_CLUSTER = 0x0FFFFFF7
    FAT32_END_OF_CHAIN = 0x0FFFFFF8
    ATTR_LONG_FILE_NAME = 0x0F
    ATTR_DIRECTORY = 0x10
    ATTR_VOLUME_ID = 0x08

    def __init__(self, drive_reader: DriveReader | None = None) -> None:
        if drive_reader is None:
            drive_reader = DriveReader()
        self.drive_reader = drive_reader
        self.boot_sector_reader = BootSectorReader(drive_reader)

    def list_txt_files(self, source: str) -> list[TxtFileEntry]:
        boot_sector_info = self.drive_reader.get_boot_sector_info(source)
        if boot_sector_info is None:
            boot_sector_info = self.boot_sector_reader.read_boot_sector(source)

        layout = self.drive_reader.build_layout(source, boot_sector_info)
        fat_table = self.drive_reader.get_fat_table(source, layout)
        txt_files = []
        visited_directories = set()
        self._scan_directory(source, layout, fat_table, layout.root_cluster, [], visited_directories, txt_files)
        txt_files.sort(key=lambda item: (item.directory_path.casefold(), item.file_name.casefold()))
        return txt_files

    def _scan_directory(
        self,
        source: str,
        layout: FAT32Layout,
        fat_table: bytes,
        directory_cluster: int,
        parent_directories: list[str],
        visited_directories: set[int],
        txt_files: list[TxtFileEntry],
    ) -> None:
        if directory_cluster < 2:
            return
        if directory_cluster in visited_directories:
            return

        visited_directories.add(directory_cluster)

        long_name_parts = []
        visited_clusters = set()
        current_cluster = directory_cluster

        while True:
            self.drive_reader.validate_cluster_number(current_cluster, layout)
            if current_cluster in visited_clusters:
                raise FAT32ReaderError("Detected a loop while following a FAT32 cluster chain.")

            visited_clusters.add(current_cluster)
            cluster_data = self.drive_reader.read_cluster(source, layout, current_cluster)

            for offset in range(0, len(cluster_data), self.drive_reader.DIRECTORY_ENTRY_SIZE):
                entry_data = cluster_data[offset : offset + self.drive_reader.DIRECTORY_ENTRY_SIZE]
                if len(entry_data) < self.drive_reader.DIRECTORY_ENTRY_SIZE:
                    return

                first_byte = entry_data[0]
                if first_byte == 0x00:
                    return

                if first_byte == 0xE5:
                    long_name_parts = []
                    continue

                attributes = entry_data[11]
                if attributes == self.ATTR_LONG_FILE_NAME:
                    long_name_parts.insert(0, self._parse_lfn_fragment(entry_data))
                    continue

                if long_name_parts:
                    entry_name = "".join(long_name_parts).strip()
                else:
                    entry_name = self._parse_short_name(entry_data)

                long_name_parts = []

                if not entry_name:
                    continue
                if attributes & self.ATTR_VOLUME_ID:
                    continue

                starting_cluster = self._read_starting_cluster(entry_data)
                file_size = int.from_bytes(entry_data[28:32], byteorder="little")

                if attributes & self.ATTR_DIRECTORY:
                    if entry_name == "." or entry_name == "..":
                        continue
                    if starting_cluster < 2:
                        continue

                    self._scan_directory(
                        source,
                        layout,
                        fat_table,
                        starting_cluster,
                        parent_directories + [entry_name],
                        visited_directories,
                        txt_files,
                    )
                    continue

                if not entry_name.lower().endswith(".txt"):
                    continue

                if parent_directories:
                    directory_path = "/" + "/".join(parent_directories)
                else:
                    directory_path = "/"

                txt_files.append(
                    TxtFileEntry(
                        file_name=entry_name,
                        directory_path=directory_path,
                        file_size=file_size,
                        starting_cluster=starting_cluster,
                    )
                )

            next_cluster = self._read_fat_entry(fat_table, current_cluster)
            if next_cluster >= self.FAT32_END_OF_CHAIN:
                return
            if next_cluster == 0:
                raise FAT32ReaderError(
                    f"Cluster {current_cluster} points to a free cluster, so the FAT32 chain looks invalid."
                )
            if next_cluster == self.FAT32_BAD_CLUSTER:
                raise FAT32ReaderError(f"Cluster {current_cluster} points to a bad cluster.")

            current_cluster = next_cluster

    def _read_fat_entry(self, fat_table: bytes, cluster_number: int) -> int:
        fat_entry_offset = cluster_number * self.FAT_ENTRY_SIZE
        end_offset = fat_entry_offset + self.FAT_ENTRY_SIZE

        if end_offset > len(fat_table):
            raise FAT32ReaderError(
                f"Cluster {cluster_number} points outside the FAT table, so the FAT32 chain looks invalid."
            )

        raw_value = fat_table[fat_entry_offset:end_offset]
        return int.from_bytes(raw_value, byteorder="little") & self.FAT32_CLUSTER_MASK

    def _read_starting_cluster(self, entry_data: bytes) -> int:
        high_word = int.from_bytes(entry_data[20:22], byteorder="little")
        low_word = int.from_bytes(entry_data[26:28], byteorder="little")
        return (high_word << 16) | low_word

    def _parse_short_name(self, entry_data: bytes) -> str:
        raw_name = entry_data[0:8]
        raw_extension = entry_data[8:11]
        name = raw_name.decode("ascii", errors="ignore").rstrip()
        extension = raw_extension.decode("ascii", errors="ignore").rstrip()

        if not name:
            return ""
        if extension:
            return f"{name}.{extension}"
        return name

    def _parse_lfn_fragment(self, entry_data: bytes) -> str:
        raw_name = entry_data[1:11] + entry_data[14:26] + entry_data[28:32]
        characters = []

        for index in range(0, len(raw_name), 2):
            raw_character = raw_name[index : index + 2]
            if raw_character == b"\x00\x00" or raw_character == b"\xff\xff":
                break
            characters.append(raw_character.decode("utf-16le", errors="ignore"))

        return "".join(characters)
