from app.drive_reader import DriveReader, FAT32ReaderError, format_bytes
from app.section1_boot_sector_reader import BootSectorReader


class TxtFileEntry:
    def __init__(self, file_name, directory_path, file_size, starting_cluster):
        self.file_name = file_name
        self.directory_path = directory_path
        self.file_size = file_size
        self.starting_cluster = starting_cluster

    def get_directory_display(self):
        if self.directory_path:
            return self.directory_path
        return "/"

    def get_size_display(self):
        return f"{self.file_size:,} bytes ({format_bytes(self.file_size)})"


class TxtFileScanner:
    def __init__(self, drive_reader=None):
        if drive_reader is None:
            drive_reader = DriveReader()
        self.drive_reader = drive_reader
        self.boot_sector_reader = BootSectorReader(drive_reader)

    def list_txt_files(self, source):
        boot_info = self.drive_reader.get_boot_sector_info(source)
        if boot_info is None:
            boot_info = self.boot_sector_reader.read_boot_sector(source)

        layout = self.drive_reader.build_layout(source, boot_info)
        fat_table = self.drive_reader.get_fat_table(source, layout)

        txt_files = []
        visited_dirs = set()
        self._scan_dir(source, layout, fat_table, layout.RDET_start_cluster, [], visited_dirs, txt_files)
        txt_files.sort(key=lambda f: (f.directory_path.casefold(), f.file_name.casefold()))
        return txt_files

    def _scan_dir(self, source, layout, fat_table, dir_cluster, parent_dirs, visited_dirs, txt_files):
        if dir_cluster < 2:
            return
        if dir_cluster in visited_dirs:
            return
        visited_dirs.add(dir_cluster)

        lfn_parts = []
        visited_clusters = set()
        cur_cluster = dir_cluster

        while True:
            self.drive_reader.validate_cluster_number(cur_cluster, layout)
            if cur_cluster in visited_clusters:
                raise FAT32ReaderError("Phat hien vong lap trong FAT chain.")
            visited_clusters.add(cur_cluster)

            cluster_data = self.drive_reader.read_cluster(source, layout, cur_cluster)

            for offset in range(0, len(cluster_data), 32):  # 32 = directory entry size (bytes)
                entry = cluster_data[offset:offset + 32]  # 32 = directory entry size (bytes)
                if len(entry) < 32:  # 32 = directory entry size (bytes)
                    return

                first_byte = entry[0]
                if first_byte == 0x00:
                    return
                if first_byte == 0xE5:
                    lfn_parts = []
                    continue

                attr = entry[11]
                if attr == 0x0F:  # ATTR_LONG_FILE_NAME
                    lfn_parts.insert(0, self._get_lfn_text(entry))
                    continue

                if lfn_parts:
                    name = "".join(lfn_parts).strip()
                else:
                    name = self._get_short_name(entry)
                lfn_parts = []

                if not name:
                    continue
                if attr & 0x08:  # ATTR_VOLUME_ID
                    continue

                start_cluster = self._get_start_cluster(entry)
                size = int.from_bytes(entry[28:32], "little")

                if attr & 0x10:  # ATTR_DIRECTORY
                    if name == "." or name == "..":
                        continue
                    if start_cluster < 2:
                        continue
                    self._scan_dir(source, layout, fat_table, start_cluster,
                                   parent_dirs + [name], visited_dirs, txt_files)
                    continue

                if not name.lower().endswith(".txt"):
                    continue

                if parent_dirs:
                    dir_path = "/" + "/".join(parent_dirs)
                else:
                    dir_path = "/"

                txt_files.append(TxtFileEntry(name, dir_path, size, start_cluster))

            next_cluster = self._read_fat_entry(fat_table, cur_cluster)
            if next_cluster >= 0x0FFFFFF8:  # FAT32 end of chain marker
                return
            if next_cluster == 0:
                raise FAT32ReaderError(f"Cluster {cur_cluster} tro den cluster trong.")
            if next_cluster == 0x0FFFFFF7:  # FAT32 bad cluster marker
                raise FAT32ReaderError(f"Cluster {cur_cluster} tro den bad cluster.")

            cur_cluster = next_cluster

    def _read_fat_entry(self, fat_table, cluster_num):
        offset = cluster_num * 4  # 4 = FAT32 entry size (bytes)
        end = offset + 4  # 4 = FAT32 entry size (bytes)
        if end > len(fat_table):
            raise FAT32ReaderError(f"Cluster {cluster_num} vuot qua bang FAT.")
        raw = fat_table[offset:end]
        return int.from_bytes(raw, "little") & 0x0FFFFFFF  # FAT32 cluster number mask

    def _get_start_cluster(self, entry):
        high = int.from_bytes(entry[20:22], "little")
        low = int.from_bytes(entry[26:28], "little")
        return (high << 16) | low

    def _get_short_name(self, entry):
        raw_name = entry[0:8]
        raw_ext = entry[8:11]
        name = raw_name.decode("ascii", errors="ignore").rstrip()
        ext = raw_ext.decode("ascii", errors="ignore").rstrip()
        if not name:
            return ""
        if ext:
            return f"{name}.{ext}"
        return name

    def _get_lfn_text(self, entry):
        raw = entry[1:11] + entry[14:26] + entry[28:32]
        chars = []
        for i in range(0, len(raw), 2):
            c = raw[i:i + 2]
            if c == b"\x00\x00" or c == b"\xff\xff":
                break
            chars.append(c.decode("utf-16le", errors="ignore"))
        return "".join(chars)
