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


class FAT32Layout:
    def __init__(self, bytes_per_sector, sectors_per_cluster, sectors_before_fat,
                 fat_count, sectors_per_fat, RDET_sectors, total_sectors, RDET_start_cluster):
        self.bytes_per_sector = bytes_per_sector
        self.sectors_per_cluster = sectors_per_cluster
        self.sectors_before_fat = sectors_before_fat
        self.fat_count = fat_count
        self.sectors_per_fat = sectors_per_fat
        self.RDET_sectors = RDET_sectors  # thường là 0 trong FAT32
        self.total_sectors = total_sectors
        self.RDET_start_cluster = RDET_start_cluster  # thường là 2

        self.cluster_size_bytes = bytes_per_sector * sectors_per_cluster
        self.fat_offset_bytes = sectors_before_fat * bytes_per_sector
        self.first_data_sector = sectors_before_fat + (fat_count * sectors_per_fat) + RDET_sectors
        self.data_sector_count = max(total_sectors - self.first_data_sector, 0)

        if sectors_per_cluster > 0:
            self.total_clusters = self.data_sector_count // sectors_per_cluster
        else:
            self.total_clusters = 0

        self.max_cluster_number = self.total_clusters + 1


class DriveReader:
    DRIVE_PATTERN = re.compile(r"^[A-Za-z]:\\?$")

    def __init__(self):
        self.current_source = ""
        self.open_path = ""
        self.stream = None
        self.boot_sector_bytes = None
        self.boot_sector_info = None
        self.layout = None
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
        self.open_path = ""
        self.boot_sector_bytes = None
        self.boot_sector_info = None
        self.layout = None
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
            raise FAT32ReaderError("Khong the truy cap USB. Hay chay voi quyen Admin.")
        except FileNotFoundError:
            raise FAT32ReaderError("Khong tim thay o USB nay.")
        except OSError as e:
            raise FAT32ReaderError(f"Loi doc USB: {e}")

        self.current_source = normalized
        self.open_path = path
        return normalized

    def read_bytes(self, source, offset, size):
        self.set_source(source)
        return self._read_raw(offset, size)

    def read_sector(self, source, sector_index, bytes_per_sector=512):
        return self.read_bytes(source, sector_index * bytes_per_sector, bytes_per_sector)

    def get_boot_sector_bytes(self, source):
        self.set_source(source)
        if self.boot_sector_bytes is None:
            self.boot_sector_bytes = self._read_raw(0, 512)  # 512 = boot sector size
        return self.boot_sector_bytes

    def remember_boot_sector_info(self, source, info):
        self.set_source(source)
        self.boot_sector_info = info

    def get_boot_sector_info(self, source):
        self.set_source(source)
        return self.boot_sector_info

    def build_layout(self, source, info):
        self.set_source(source)

        if info.bytes_per_sector <= 0:
            raise FAT32ReaderError("bytes_per_sector phai > 0")
        if info.sectors_per_cluster <= 0:
            raise FAT32ReaderError("sectors_per_cluster phai > 0")
        if info.sectors_per_fat <= 0:
            raise FAT32ReaderError("sectors_per_fat phai > 0")
        if info.RDET_start_cluster < 2:
            raise FAT32ReaderError("RDET_start_cluster phai >= 2")

        if self.layout is None:
            self.layout = FAT32Layout(
                info.bytes_per_sector,
                info.sectors_per_cluster,
                info.sectors_before_fat,
                info.fat_count,
                info.sectors_per_fat,
                info.RDET_sectors,
                info.total_sectors,
                info.RDET_start_cluster,
            )

        if self.layout.total_clusters <= 0:
            raise FAT32ReaderError("Vung du lieu khong co cluster nao.")

        return self.layout

    def get_fat_table(self, source, layout):
        self.set_source(source)
        if self.fat_table is None:
            fat_size = layout.sectors_per_fat * layout.bytes_per_sector
            self.fat_table = self._read_raw(layout.fat_offset_bytes, fat_size)
        return self.fat_table

    def read_cluster(self, source, layout, cluster_number):
        self.set_source(source)
        self.validate_cluster_number(cluster_number, layout)
        first_sector = layout.first_data_sector + ((cluster_number - 2) * layout.sectors_per_cluster)
        offset = first_sector * layout.bytes_per_sector
        return self._read_raw(offset, layout.cluster_size_bytes)

    def _read_raw(self, offset, size):
        if self.stream is None:
            raise FAT32ReaderError("Chua mo USB nao.")

        self.stream.seek(offset)
        data = self.stream.read(size)
        if len(data) != size:
            raise FAT32ReaderError(f"Doc thieu du lieu tai offset {offset}: {len(data)}/{size} bytes")
        return data

    def _normalize_source(self, source):
        cleaned = source.strip().strip('"')
        if not cleaned:
            raise FAT32ReaderError("Hay nhap ki tu o dia, vd: E:")

        if not self.DRIVE_PATTERN.match(cleaned):
            raise FAT32ReaderError("Sai dinh dang o dia, vd: E:")

        return cleaned[0].upper() + ":"

    def validate_cluster_number(self, cluster_number, layout):
        if cluster_number < 2 or cluster_number > layout.max_cluster_number:
            raise FAT32ReaderError(f"Cluster {cluster_number} nam ngoai vung hop le.")
