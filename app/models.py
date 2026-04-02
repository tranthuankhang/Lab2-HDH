from __future__ import annotations

from dataclasses import dataclass, field


def format_bytes(size_in_bytes: int) -> str:
    if size_in_bytes <= 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_in_bytes)
    unit_index = 0

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"

    return f"{value:.2f} {units[unit_index]}"


@dataclass(slots=True)
class BootSectorInfo:
    source_display: str
    source_type: str
    oem_name: str
    filesystem_type: str
    volume_label: str
    volume_serial_number: int
    boot_signature: str
    bytes_per_sector: int
    sectors_per_cluster: int
    reserved_sector_count: int
    fat_count: int
    sectors_per_fat: int
    root_dir_sectors: int
    total_sectors: int
    hidden_sectors: int
    root_cluster: int
    media_descriptor: int
    total_size_bytes: int
    validation_messages: tuple[str, ...] = ()

    @property
    def source_type_label(self) -> str:
        if self.source_type == "drive":
            return "Drive / USB"
        return "Image file"

    @property
    def volume_serial_display(self) -> str:
        return f"0x{self.volume_serial_number:08X}"

    @property
    def media_descriptor_display(self) -> str:
        return f"0x{self.media_descriptor:02X}"

    @property
    def size_display(self) -> str:
        return f"{self.total_size_bytes:,} bytes ({format_bytes(self.total_size_bytes)})"

    def table_rows(self) -> list[tuple[str, str]]:
        return [
            ("Bytes per sector", str(self.bytes_per_sector)),
            ("Sectors per cluster", str(self.sectors_per_cluster)),
            ("Number of sectors in Boot Sector region", str(self.reserved_sector_count)),
            ("Number of FAT tables", str(self.fat_count)),
            ("Number of sectors per FAT table", str(self.sectors_per_fat)),
            ("Number of sectors for the RDET", str(self.root_dir_sectors)),
            ("Total number of sectors on the disk", str(self.total_sectors)),
            ("Estimated total size", self.size_display),
            ("Root cluster", str(self.root_cluster)),
            ("Hidden sectors", str(self.hidden_sectors)),
            ("Media descriptor", self.media_descriptor_display),
            ("Volume serial number", self.volume_serial_display),
            ("Volume label", self.volume_label or "(empty)"),
            ("File system type", self.filesystem_type or "(unknown)"),
            ("OEM Name", self.oem_name or "(unknown)"),
            ("Boot sector signature", self.boot_signature),
        ]


@dataclass(slots=True)
class ProcessInfo:
    process_id: str
    arrival_time: int
    cpu_burst_time: int
    priority_queue_id: int | None = None
    time_slice: int | None = None


@dataclass(slots=True)
class ScheduledSlice:
    process_id: str
    start_time: int
    end_time: int


@dataclass(slots=True)
class SchedulingResult:
    algorithm_name: str
    slices: list[ScheduledSlice] = field(default_factory=list)
    turnaround_times: dict[str, int] = field(default_factory=dict)
    waiting_times: dict[str, int] = field(default_factory=dict)
