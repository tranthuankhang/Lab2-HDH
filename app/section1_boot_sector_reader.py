from __future__ import annotations

from app.drive_reader import DriveReader, FAT32ReaderError


class BootSectorInfo:
    def __init__(
        self,
        source_display: str,
        bytes_per_sector: int,
        sectors_per_cluster: int,
        reserved_sector_count: int,
        fat_count: int,
        sectors_per_fat: int,
        root_dir_sectors: int,
        total_sectors: int,
        root_cluster: int,
    ) -> None:
        self.source_display = source_display
        self.bytes_per_sector = bytes_per_sector
        self.sectors_per_cluster = sectors_per_cluster
        self.reserved_sector_count = reserved_sector_count
        self.fat_count = fat_count
        self.sectors_per_fat = sectors_per_fat
        self.root_dir_sectors = root_dir_sectors
        self.total_sectors = total_sectors
        self.root_cluster = root_cluster

    def table_rows(self) -> list[tuple[str, str]]:
        return [
            ("Bytes per sector", str(self.bytes_per_sector)),
            ("Sectors per cluster", str(self.sectors_per_cluster)),
            ("Number of sectors in Boot Sector region", str(self.reserved_sector_count)),
            ("Number of FAT tables", str(self.fat_count)),
            ("Number of sectors per FAT table", str(self.sectors_per_fat)),
            ("Number of sectors for the RDET", str(self.root_dir_sectors)),
            ("Total number of sectors on the disk", str(self.total_sectors)),
        ]


class BootSectorReader:
    VALID_BOOT_SIGNATURE = b"\x55\xAA"

    def __init__(self, drive_reader: DriveReader | None = None) -> None:
        if drive_reader is None:
            drive_reader = DriveReader()
        self.drive_reader = drive_reader

    def read_boot_sector(self, source: str) -> BootSectorInfo:
        source_display = self.drive_reader.set_source(source)
        raw_data = self.drive_reader.get_boot_sector_bytes(source)
        boot_sector_info = self._parse_boot_sector(raw_data, source_display)
        self.drive_reader.remember_boot_sector_info(source, boot_sector_info)
        return boot_sector_info

    def _parse_boot_sector(self, raw_data: bytes, source_display: str) -> BootSectorInfo:
        if len(raw_data) < self.drive_reader.BOOT_SECTOR_SIZE:
            raise FAT32ReaderError("Invalid Boot Sector: the source returned fewer than 512 bytes.")

        if raw_data[510:512] != self.VALID_BOOT_SIGNATURE:
            raise FAT32ReaderError("Invalid Boot Sector signature. The last two bytes are not 0x55AA.")

        bytes_per_sector = int.from_bytes(raw_data[11:13], "little")
        sectors_per_cluster = raw_data[13]
        reserved_sector_count = int.from_bytes(raw_data[14:16], "little")
        fat_count = raw_data[16]
        root_entry_count = int.from_bytes(raw_data[17:19], "little")
        total_sectors_16 = int.from_bytes(raw_data[19:21], "little")
        sectors_per_fat_16 = int.from_bytes(raw_data[22:24], "little")
        total_sectors_32 = int.from_bytes(raw_data[32:36], "little")
        sectors_per_fat_32 = int.from_bytes(raw_data[36:40], "little")
        root_cluster = int.from_bytes(raw_data[44:48], "little")

        if total_sectors_16 != 0:
            total_sectors = total_sectors_16
        else:
            total_sectors = total_sectors_32

        if sectors_per_fat_32 != 0:
            sectors_per_fat = sectors_per_fat_32
        else:
            sectors_per_fat = sectors_per_fat_16

        if bytes_per_sector <= 0:
            root_dir_sectors = 0
        else:
            root_dir_size_in_bytes = root_entry_count * self.drive_reader.DIRECTORY_ENTRY_SIZE
            root_dir_sectors = (root_dir_size_in_bytes + bytes_per_sector - 1) // bytes_per_sector

        return BootSectorInfo(
            source_display=source_display,
            bytes_per_sector=bytes_per_sector,
            sectors_per_cluster=sectors_per_cluster,
            reserved_sector_count=reserved_sector_count,
            fat_count=fat_count,
            sectors_per_fat=sectors_per_fat,
            root_dir_sectors=root_dir_sectors,
            total_sectors=total_sectors,
            root_cluster=root_cluster,
        )
