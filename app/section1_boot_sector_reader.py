from app.drive_reader import DriveReader, FAT32ReaderError


class BootSectorInfo:
    def __init__(self, source_display, bytes_per_sector, sectors_per_cluster,
                 sectors_before_fat, fat_count, sectors_per_fat,
                 RDET_sectors, total_sectors, RDET_start_cluster):
        self.source_display = source_display
        self.bytes_per_sector = bytes_per_sector
        self.sectors_per_cluster = sectors_per_cluster
        self.sectors_before_fat = sectors_before_fat
        self.fat_count = fat_count
        self.sectors_per_fat = sectors_per_fat
        self.RDET_sectors = RDET_sectors  # thường là 0 trong FAT32
        self.total_sectors = total_sectors
        self.RDET_start_cluster = RDET_start_cluster  # thường là 2

    def table_rows(self):
        return [
            ("Bytes per sector", str(self.bytes_per_sector)),
            ("Sectors per cluster", str(self.sectors_per_cluster)),
            ("Number of sectors in Boot Sector region", str(self.sectors_before_fat)),
            ("Number of FAT tables", str(self.fat_count)),
            ("Number of sectors per FAT table", str(self.sectors_per_fat)),
            ("Number of sectors for the RDET", str(self.RDET_sectors)),
            ("Total number of sectors on the disk", str(self.total_sectors)),
        ]


class BootSectorReader:
    def __init__(self, drive_reader=None):
        if drive_reader is None:
            drive_reader = DriveReader()
        self.drive_reader = drive_reader

    def read_boot_sector(self, source):
        source_display = self.drive_reader.set_source(source)
        raw = self.drive_reader.get_boot_sector_bytes(source)
        info = self._parse(raw, source_display)
        self.drive_reader.remember_boot_sector_info(source, info)
        return info

    def _parse(self, raw, source_display):
        if len(raw) < 512:  # 512 = boot sector size
            raise FAT32ReaderError("Boot Sector khong du 512 bytes.")

        if raw[510:512] != b"\x55\xAA":  # 0x55AA = valid boot signature
            raise FAT32ReaderError("Sai Boot Sector signature (khong phai 0x55AA).")

        bytes_per_sector = int.from_bytes(raw[11:13], "little")
        sectors_per_cluster = raw[13]
        sectors_before_fat = int.from_bytes(raw[14:16], "little")
        fat_count = raw[16]
        # FAT32: total sectors luôn ở offset 32, sectors/FAT luôn ở offset 36
        total_sectors = int.from_bytes(raw[32:36], "little")
        sectors_per_fat = int.from_bytes(raw[36:40], "little")
        RDET_start_cluster = int.from_bytes(raw[44:48], "little")
        RDET_entry_count = int.from_bytes(raw[17:19], "little")  # FAT32 luôn = 0
        
        RDET_bytes = RDET_entry_count * 32  # 32 = directory entry size (bytes)
        RDET_sectors = (RDET_bytes + bytes_per_sector - 1) // bytes_per_sector  # thường = 0

        return BootSectorInfo(
            source_display, bytes_per_sector, sectors_per_cluster,
            sectors_before_fat, fat_count, sectors_per_fat,
            RDET_sectors, total_sectors, RDET_start_cluster,
        )
