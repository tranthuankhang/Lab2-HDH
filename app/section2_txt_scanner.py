from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Iterator

from app.section1_boot_sector_reader import (
    FAT32Layout,
    FAT32ReaderError,
    BootSectorReader,
    format_bytes,
)


@dataclass(slots=True)
class DirectoryEntry:
    name: str
    is_directory: bool
    starting_cluster: int
    file_size: int


@dataclass(slots=True)
class TxtFileEntry:
    file_name: str
    directory_path: str
    file_size: int
    starting_cluster: int

    @property
    def directory_display(self) -> str:
        return self.directory_path or "/"

    @property
    def size_display(self) -> str:
        return f"{self.file_size:,} bytes ({format_bytes(self.file_size)})"


class TxtFileScanner(BootSectorReader):
    FAT_ENTRY_SIZE = 4
    FAT32_CLUSTER_MASK = 0x0FFFFFFF
    FAT32_BAD_CLUSTER = 0x0FFFFFF7
    FAT32_END_OF_CHAIN = 0x0FFFFFF8
    ATTR_LONG_FILE_NAME = 0x0F
    ATTR_DIRECTORY = 0x10
    ATTR_VOLUME_ID = 0x08

    def list_txt_files(self, source: str) -> list[TxtFileEntry]:
        resolved_source = self._resolve_source(source)

        with self._open_source(resolved_source) as stream:
            raw_data = self._read_bytes_from_stream(stream, 0, self.BOOT_SECTOR_SIZE)
            boot_sector_info = self._parse_boot_sector(raw_data, resolved_source)
            layout = self._build_layout(boot_sector_info)
            fat_table = self._read_primary_fat(stream, layout)
            txt_files = self._walk_txt_files(stream, layout, fat_table)

        txt_files.sort(key=lambda item: (item.directory_path.casefold(), item.file_name.casefold()))
        return txt_files

    def _read_primary_fat(self, stream: BinaryIO, layout: FAT32Layout) -> bytes:
        fat_size_in_bytes = layout.sectors_per_fat * layout.bytes_per_sector
        return self._read_bytes_from_stream(stream, layout.fat_offset_bytes, fat_size_in_bytes)

    def _walk_txt_files(
        self,
        stream: BinaryIO,
        layout: FAT32Layout,
        fat_table: bytes,
    ) -> list[TxtFileEntry]:
        txt_files: list[TxtFileEntry] = []
        visited_directories: set[int] = set()

        def walk_directory(cluster_number: int, parent_directories: list[str]) -> None:
            if cluster_number < 2 or cluster_number in visited_directories:
                return

            visited_directories.add(cluster_number)

            for entry in self._iter_directory_entries(stream, layout, fat_table, cluster_number):
                if entry.is_directory:
                    if entry.name in {".", ".."} or entry.starting_cluster < 2:
                        continue
                    walk_directory(entry.starting_cluster, parent_directories + [entry.name])
                    continue

                if not entry.name.lower().endswith(".txt"):
                    continue

                txt_files.append(
                    TxtFileEntry(
                        file_name=entry.name,
                        directory_path=self._format_directory_path(parent_directories),
                        file_size=entry.file_size,
                        starting_cluster=entry.starting_cluster,
                    )
                )

        walk_directory(layout.root_cluster, [])
        return txt_files

    def _iter_directory_entries(
        self,
        stream: BinaryIO,
        layout: FAT32Layout,
        fat_table: bytes,
        starting_cluster: int,
    ) -> Iterator[DirectoryEntry]:
        long_name_parts: list[str] = []

        for cluster_number in self._iter_cluster_chain(layout, fat_table, starting_cluster):
            cluster_data = self._read_cluster(stream, layout, cluster_number)

            for offset in range(0, len(cluster_data), self.DIRECTORY_ENTRY_SIZE):
                entry = cluster_data[offset : offset + self.DIRECTORY_ENTRY_SIZE]
                if len(entry) < self.DIRECTORY_ENTRY_SIZE:
                    return

                first_byte = entry[0]
                if first_byte == 0x00:
                    return

                if first_byte == 0xE5:
                    long_name_parts.clear()
                    continue

                attributes = entry[11]
                if attributes == self.ATTR_LONG_FILE_NAME:
                    long_name_parts.insert(0, self._parse_lfn_fragment(entry))
                    continue

                entry_name = "".join(long_name_parts).strip() if long_name_parts else self._parse_short_name(entry)
                long_name_parts.clear()

                if not entry_name or attributes & self.ATTR_VOLUME_ID:
                    continue

                yield DirectoryEntry(
                    name=entry_name,
                    is_directory=bool(attributes & self.ATTR_DIRECTORY),
                    starting_cluster=self._read_entry_starting_cluster(entry),
                    file_size=int.from_bytes(entry[28:32], byteorder="little"),
                )

    def _iter_cluster_chain(
        self, layout: FAT32Layout, fat_table: bytes, starting_cluster: int
    ) -> Iterator[int]:
        current_cluster = starting_cluster
        visited_clusters: set[int] = set()

        while True:
            self._validate_cluster_number(current_cluster, layout)

            if current_cluster in visited_clusters:
                raise FAT32ReaderError("Detected a loop while following a FAT32 cluster chain.")

            visited_clusters.add(current_cluster)
            yield current_cluster

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

    def _read_entry_starting_cluster(self, entry: bytes) -> int:
        high_word = int.from_bytes(entry[20:22], byteorder="little")
        low_word = int.from_bytes(entry[26:28], byteorder="little")
        return (high_word << 16) | low_word

    def _parse_short_name(self, entry: bytes) -> str:
        raw_name = entry[0:8]
        raw_extension = entry[8:11]
        name = raw_name.decode("ascii", errors="ignore").rstrip()
        extension = raw_extension.decode("ascii", errors="ignore").rstrip()

        if not name:
            return ""
        if extension:
            return f"{name}.{extension}"
        return name

    def _parse_lfn_fragment(self, entry: bytes) -> str:
        raw_name = entry[1:11] + entry[14:26] + entry[28:32]
        characters: list[str] = []

        for index in range(0, len(raw_name), 2):
            raw_character = raw_name[index : index + 2]
            if raw_character in {b"\x00\x00", b"\xff\xff"}:
                break
            characters.append(raw_character.decode("utf-16le", errors="ignore"))

        return "".join(characters)

    def _format_directory_path(self, parent_directories: list[str]) -> str:
        if not parent_directories:
            return "/"
        return "/" + "/".join(parent_directories)
