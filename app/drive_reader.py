from __future__ import annotations

import re


def format_bytes(size_in_bytes: int) -> str:
    if size_in_bytes <= 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_in_bytes)
    unit_index = 0

    while value >= 1024 and unit_index < len(units) - 1:
        value = value / 1024
        unit_index = unit_index + 1

    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"

    return f"{value:.2f} {units[unit_index]}"


class FAT32ReaderError(Exception):
    """Raised when a FAT32 source cannot be read or parsed."""


class FAT32Layout:
    def __init__(
        self,
        bytes_per_sector: int,
        sectors_per_cluster: int,
        reserved_sector_count: int,
        fat_count: int,
        sectors_per_fat: int,
        root_dir_sectors: int,
        total_sectors: int,
        root_cluster: int,
    ) -> None:
        self.bytes_per_sector = bytes_per_sector
        self.sectors_per_cluster = sectors_per_cluster
        self.reserved_sector_count = reserved_sector_count
        self.fat_count = fat_count
        self.sectors_per_fat = sectors_per_fat
        self.root_dir_sectors = root_dir_sectors
        self.total_sectors = total_sectors
        self.root_cluster = root_cluster
        self.cluster_size = self.bytes_per_sector * self.sectors_per_cluster
        self.fat_offset_bytes = self.reserved_sector_count * self.bytes_per_sector
        self.first_data_sector = self.reserved_sector_count + (self.fat_count * self.sectors_per_fat) + self.root_dir_sectors
        self.data_sector_count = max(self.total_sectors - self.first_data_sector, 0)

        if self.sectors_per_cluster <= 0:
            self.total_clusters = 0
        else:
            self.total_clusters = self.data_sector_count // self.sectors_per_cluster

        self.max_cluster_number = self.total_clusters + 1


class DriveReader:
    BOOT_SECTOR_SIZE = 512
    DIRECTORY_ENTRY_SIZE = 32
    DRIVE_PATTERN = re.compile(r"^[A-Za-z]:\\?$")

    def __init__(self) -> None:
        self.current_source = ""
        self.open_path = ""
        self.stream = None
        self.boot_sector_bytes = None
        self.boot_sector_info = None
        self.layout = None
        self.fat_table = None

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
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

    def set_source(self, source: str) -> str:
        normalized_source = self._normalize_source(source)

        if self.stream is not None and self.current_source == normalized_source:
            return normalized_source

        self.close()
        open_path = rf"\\.\{normalized_source}"

        try:
            self.stream = open(open_path, "rb", buffering=0)
        except PermissionError as exc:
            raise FAT32ReaderError(
                "Unable to access the selected USB drive. Please try running the application with "
                "Administrator privileges."
            ) from exc
        except FileNotFoundError as exc:
            raise FAT32ReaderError("The selected USB drive could not be found.") from exc
        except OSError as exc:
            raise FAT32ReaderError(f"An error occurred while reading the USB drive: {exc}") from exc

        self.current_source = normalized_source
        self.open_path = open_path
        return normalized_source

    def read_bytes(self, source: str, offset: int, size: int) -> bytes:
        self.set_source(source)
        return self._read_bytes_from_current_stream(offset, size)

    def read_sector(self, source: str, sector_index: int, bytes_per_sector: int = 512) -> bytes:
        return self.read_bytes(source, sector_index * bytes_per_sector, bytes_per_sector)

    def get_boot_sector_bytes(self, source: str) -> bytes:
        self.set_source(source)

        if self.boot_sector_bytes is None:
            self.boot_sector_bytes = self._read_bytes_from_current_stream(0, self.BOOT_SECTOR_SIZE)

        return self.boot_sector_bytes

    def remember_boot_sector_info(self, source: str, boot_sector_info) -> None:
        self.set_source(source)
        self.boot_sector_info = boot_sector_info

    def get_boot_sector_info(self, source: str):
        self.set_source(source)
        return self.boot_sector_info

    def build_layout(self, source: str, boot_sector_info) -> FAT32Layout:
        self.set_source(source)

        if boot_sector_info.bytes_per_sector <= 0:
            raise FAT32ReaderError("Invalid FAT32 source: bytes per sector must be greater than 0.")
        if boot_sector_info.sectors_per_cluster <= 0:
            raise FAT32ReaderError("Invalid FAT32 source: sectors per cluster must be greater than 0.")
        if boot_sector_info.sectors_per_fat <= 0:
            raise FAT32ReaderError("Invalid FAT32 source: sectors per FAT must be greater than 0.")
        if boot_sector_info.root_cluster < 2:
            raise FAT32ReaderError("Invalid FAT32 source: root cluster must be at least 2.")

        if self.layout is None:
            self.layout = FAT32Layout(
                bytes_per_sector=boot_sector_info.bytes_per_sector,
                sectors_per_cluster=boot_sector_info.sectors_per_cluster,
                reserved_sector_count=boot_sector_info.reserved_sector_count,
                fat_count=boot_sector_info.fat_count,
                sectors_per_fat=boot_sector_info.sectors_per_fat,
                root_dir_sectors=boot_sector_info.root_dir_sectors,
                total_sectors=boot_sector_info.total_sectors,
                root_cluster=boot_sector_info.root_cluster,
            )

        if self.layout.total_clusters <= 0:
            raise FAT32ReaderError("Invalid FAT32 source: the data region does not contain any clusters.")

        return self.layout

    def get_fat_table(self, source: str, layout: FAT32Layout) -> bytes:
        self.set_source(source)

        if self.fat_table is None:
            fat_size_in_bytes = layout.sectors_per_fat * layout.bytes_per_sector
            self.fat_table = self._read_bytes_from_current_stream(layout.fat_offset_bytes, fat_size_in_bytes)

        return self.fat_table

    def read_cluster(self, source: str, layout: FAT32Layout, cluster_number: int) -> bytes:
        self.set_source(source)
        self.validate_cluster_number(cluster_number, layout)
        first_sector_of_cluster = layout.first_data_sector + ((cluster_number - 2) * layout.sectors_per_cluster)
        cluster_offset = first_sector_of_cluster * layout.bytes_per_sector
        return self._read_bytes_from_current_stream(cluster_offset, layout.cluster_size)

    def _read_bytes_from_current_stream(self, offset: int, size: int) -> bytes:
        if self.stream is None:
            raise FAT32ReaderError("No FAT32 USB drive is currently open.")

        self.stream.seek(offset)
        raw_data = self.stream.read(size)

        if len(raw_data) != size:
            raise FAT32ReaderError(
                f"Unable to read {size} bytes at offset {offset}. Only {len(raw_data)} bytes were returned."
            )

        return raw_data

    def _normalize_source(self, source: str) -> str:
        cleaned_source = source.strip().strip('"')
        if not cleaned_source:
            raise FAT32ReaderError("Please enter a FAT32 USB drive letter such as E:.")

        if not self.DRIVE_PATTERN.match(cleaned_source):
            raise FAT32ReaderError(
                "This revision only supports direct FAT32 USB access. Please enter a drive letter such as E:."
            )

        drive_letter = cleaned_source[0].upper()
        return f"{drive_letter}:"

    def validate_cluster_number(self, cluster_number: int, layout: FAT32Layout) -> None:
        if cluster_number < 2 or cluster_number > layout.max_cluster_number:
            raise FAT32ReaderError(
                f"Encountered cluster {cluster_number}, which is outside the valid FAT32 data range."
            )
