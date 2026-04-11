import re


def format_bytes(size):
    if size <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    val = float(size)
    i = 0
    while val >= 1024 and i < len(units) - 1:
        val /= 1024
        i += 1
    if i == 0:
        return f"{int(val)} B"
    return f"{val:.2f} {units[i]}"


class FAT32ReaderError(Exception):
    pass


class DriveReader:
    DRIVE_PATTERN = re.compile(r"^[A-Za-z]:\\?$")

    def __init__(self):
        self.current_source = ""
        self.stream = None
        self.boot_sector_bytes = None
        self.boot_sector_info = None
        self.fat_table = None

    def __del__(self):
        self.close()

    def close(self):
        if self.stream is not None:
            try:
                self.stream.close()
            except OSError:
                pass
        self.stream = None
        self.current_source = ""
        self.boot_sector_bytes = None
        self.boot_sector_info = None
        self.fat_table = None

    def set_source(self, source):
        normalized = self._normalize_source(source)

        if self.stream is not None and self.current_source == normalized:
            return normalized

        self.close()
        path = rf"\\.\{normalized}"

        try:
            self.stream = open(path, "rb", buffering=0)
        except PermissionError:
            raise FAT32ReaderError("Cannot access USB drive. Please run as Administrator.")
        except FileNotFoundError:
            raise FAT32ReaderError("USB drive not found.")
        except OSError as e:
            raise FAT32ReaderError(f"USB read error: {e}")

        self.current_source = normalized
        return normalized

    def get_boot_sector_bytes(self, source): #get/set
        self.set_source(source)
        if self.boot_sector_bytes is None:
            self.boot_sector_bytes = self._read_raw(0, 512)  # 512 = boot sector size
        return self.boot_sector_bytes

    def set_boot_sector_info(self, source, info):
        self.set_source(source)
        self.boot_sector_info = info

    def get_boot_sector_info(self, source):
        self.set_source(source)
        return self.boot_sector_info

    def get_fat_table(self, source, info): #get/set
        self.set_source(source)
        self._validate_boot_sector_info(info)
        if self.fat_table is None:
            self.fat_table = self._read_raw(info.fat_offset_bytes, info.fat_size_bytes)
        return self.fat_table

    def read_cluster(self, source, info, cluster_number):
        self.set_source(source)
        self.validate_cluster_number(cluster_number, info) #first_sector la sector dau tien cua cluster
        first_sector = info.first_data_sector + ((cluster_number - 2) * info.sectors_per_cluster)
        offset = first_sector * info.bytes_per_sector
        return self._read_raw(offset, info.cluster_size_bytes)

    def _read_raw(self, offset, size):
        if self.stream is None:
            raise FAT32ReaderError("No USB drive is open.")

        self.stream.seek(offset)
        data = self.stream.read(size)
        if len(data) != size:
            raise FAT32ReaderError(f"Incomplete read at offset {offset}: {len(data)}/{size} bytes")
        return data

    def _normalize_source(self, source):
        cleaned = source.strip().strip('"')
        if not cleaned:
            raise FAT32ReaderError("Drive letter is required, e.g.: E:")

        if not self.DRIVE_PATTERN.match(cleaned):
            raise FAT32ReaderError("Invalid drive letter format, e.g.: E:")

        return cleaned[0].upper() + ":"

    def validate_cluster_number(self, cluster_number, info):
        self._validate_boot_sector_info(info)
        if cluster_number < 2 or cluster_number > info.max_cluster_number:
            raise FAT32ReaderError(f"Cluster {cluster_number} is out of valid range.")

    def _validate_boot_sector_info(self, info):
        if info is None:
            raise FAT32ReaderError("Boot Sector info is not available.")
        if info.bytes_per_sector <= 0:
            raise FAT32ReaderError("bytes_per_sector must be > 0")
        if info.sectors_per_cluster <= 0:
            raise FAT32ReaderError("sectors_per_cluster must be > 0")
        if info.sectors_per_fat <= 0:
            raise FAT32ReaderError("sectors_per_fat must be > 0")
        if info.RDET_start_cluster < 2:
            raise FAT32ReaderError("RDET_start_cluster must be >= 2")
        if info.total_clusters <= 0:
            raise FAT32ReaderError("Data region contains no clusters.")
