from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import BinaryIO, Iterator


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


class FAT32ReaderError(Exception):
    """Raised when a FAT32 source cannot be read or parsed."""


@dataclass(slots=True)
class ResolvedSource:
    display_path: str
    open_path: str
    source_type: str


@dataclass(slots=True)
class FAT32Layout:
    bytes_per_sector: int
    sectors_per_cluster: int
    reserved_sector_count: int
    fat_count: int
    sectors_per_fat: int
    root_dir_sectors: int
    total_sectors: int
    root_cluster: int

    @property
    def cluster_size(self) -> int:
        return self.bytes_per_sector * self.sectors_per_cluster

    @property
    def fat_offset_bytes(self) -> int:
        return self.reserved_sector_count * self.bytes_per_sector

    @property
    def first_data_sector(self) -> int:
        return self.reserved_sector_count + (self.fat_count * self.sectors_per_fat) + self.root_dir_sectors

    @property
    def data_sector_count(self) -> int:
        return max(self.total_sectors - self.first_data_sector, 0)

    @property
    def total_clusters(self) -> int:
        if self.sectors_per_cluster <= 0:
            return 0
        return self.data_sector_count // self.sectors_per_cluster

    @property
    def max_cluster_number(self) -> int:
        return self.total_clusters + 1


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


class BootSectorReader:
    BOOT_SECTOR_SIZE = 512
    DIRECTORY_ENTRY_SIZE = 32
    VALID_BOOT_SIGNATURE = b"\x55\xAA"
    DRIVE_PATTERN = re.compile(r"^[A-Za-z]:\\?$")

    def read_boot_sector(self, source: str) -> BootSectorInfo:
        resolved_source = self._resolve_source(source)
        with self._open_source(resolved_source) as stream:
            raw_data = self._read_bytes_from_stream(stream, 0, self.BOOT_SECTOR_SIZE)
        return self._parse_boot_sector(raw_data, resolved_source)

    def read_bytes(self, source: str, offset: int, size: int) -> bytes:
        resolved_source = self._resolve_source(source)
        with self._open_source(resolved_source) as stream:
            return self._read_bytes_from_stream(stream, offset, size)

    def read_sector(self, source: str, sector_index: int, bytes_per_sector: int = 512) -> bytes:
        return self.read_bytes(source, sector_index * bytes_per_sector, bytes_per_sector)

    @contextmanager
    def _open_source(self, resolved_source: ResolvedSource) -> Iterator[BinaryIO]:
        try:
            with open(resolved_source.open_path, "rb", buffering=0) as stream:
                yield stream
        except PermissionError as exc:
            raise FAT32ReaderError(
                "Unable to access the selected USB drive. Please try running the application with "
                "Administrator privileges."
            ) from exc
        except FileNotFoundError as exc:
            raise FAT32ReaderError("The selected USB drive could not be found.") from exc
        except OSError as exc:
            raise FAT32ReaderError(f"An error occurred while reading the USB drive: {exc}") from exc

    def _read_bytes_from_stream(self, stream: BinaryIO, offset: int, size: int) -> bytes:
        stream.seek(offset)
        raw_data = stream.read(size)

        if len(raw_data) != size:
            raise FAT32ReaderError(
                f"Unable to read {size} bytes at offset {offset}. Only {len(raw_data)} bytes were returned."
            )

        return raw_data

    def _resolve_source(self, source: str) -> ResolvedSource:
        cleaned_source = source.strip().strip('"')
        if not cleaned_source:
            raise FAT32ReaderError("Please enter a FAT32 USB drive letter such as E:.")

        if not self.DRIVE_PATTERN.match(cleaned_source):
            raise FAT32ReaderError(
                "This revision only supports direct FAT32 USB access. Please enter a drive letter such as E:."
            )

        drive_letter = cleaned_source[0].upper()
        normalized_drive = f"{drive_letter}:"
        return ResolvedSource(
            display_path=normalized_drive,
            open_path=rf"\\.\{normalized_drive}",
            source_type="drive",
        )

    def _build_layout(self, boot_sector_info: BootSectorInfo) -> FAT32Layout:
        if boot_sector_info.bytes_per_sector <= 0:
            raise FAT32ReaderError("Invalid FAT32 source: bytes per sector must be greater than 0.")
        if boot_sector_info.sectors_per_cluster <= 0:
            raise FAT32ReaderError("Invalid FAT32 source: sectors per cluster must be greater than 0.")
        if boot_sector_info.sectors_per_fat <= 0:
            raise FAT32ReaderError("Invalid FAT32 source: sectors per FAT must be greater than 0.")
        if boot_sector_info.root_cluster < 2:
            raise FAT32ReaderError("Invalid FAT32 source: root cluster must be at least 2.")

        layout = FAT32Layout(
            bytes_per_sector=boot_sector_info.bytes_per_sector,
            sectors_per_cluster=boot_sector_info.sectors_per_cluster,
            reserved_sector_count=boot_sector_info.reserved_sector_count,
            fat_count=boot_sector_info.fat_count,
            sectors_per_fat=boot_sector_info.sectors_per_fat,
            root_dir_sectors=boot_sector_info.root_dir_sectors,
            total_sectors=boot_sector_info.total_sectors,
            root_cluster=boot_sector_info.root_cluster,
        )

        if layout.total_clusters <= 0:
            raise FAT32ReaderError("Invalid FAT32 source: the data region does not contain any clusters.")

        return layout

    def _read_cluster(self, stream: BinaryIO, layout: FAT32Layout, cluster_number: int) -> bytes:
        self._validate_cluster_number(cluster_number, layout)
        cluster_offset = self._cluster_offset(layout, cluster_number)
        return self._read_bytes_from_stream(stream, cluster_offset, layout.cluster_size)

    def _cluster_offset(self, layout: FAT32Layout, cluster_number: int) -> int:
        first_sector_of_cluster = layout.first_data_sector + ((cluster_number - 2) * layout.sectors_per_cluster)
        return first_sector_of_cluster * layout.bytes_per_sector

    def _validate_cluster_number(self, cluster_number: int, layout: FAT32Layout) -> None:
        if cluster_number < 2 or cluster_number > layout.max_cluster_number:
            raise FAT32ReaderError(
                f"Encountered cluster {cluster_number}, which is outside the valid FAT32 data range."
            )

    def _parse_boot_sector(self, raw_data: bytes, resolved_source: ResolvedSource) -> BootSectorInfo:
        if len(raw_data) < self.BOOT_SECTOR_SIZE:
            raise FAT32ReaderError("Invalid Boot Sector: the source returned fewer than 512 bytes.")

        # Note for beginners:
        # - `offset` means "start reading at this byte index".
        # - FAT32 stores multi-byte integers in little-endian order.
        #   Example: b"\x00\x02" means 0x0200 = 512.
        # - We intentionally read each field one by one so the layout is easy to follow.

        # Standard BIOS Parameter Block (shared by FAT variants).
        oem_name = self._read_text(raw_data, 3, 8, "OEM Name")
        bytes_per_sector = self._read_uint16_le(raw_data, 11, "Bytes per sector")
        sectors_per_cluster = self._read_uint8(raw_data, 13, "Sectors per cluster")
        reserved_sector_count = self._read_uint16_le(raw_data, 14, "Reserved sector count")
        fat_count = self._read_uint8(raw_data, 16, "Number of FAT tables")
        root_entry_count = self._read_uint16_le(raw_data, 17, "Root entry count")
        total_sectors_16 = self._read_uint16_le(raw_data, 19, "Total sectors (16-bit)")
        media_descriptor = self._read_uint8(raw_data, 21, "Media descriptor")
        sectors_per_fat_16 = self._read_uint16_le(raw_data, 22, "Sectors per FAT (16-bit)")
        hidden_sectors = self._read_uint32_le(raw_data, 28, "Hidden sectors")
        total_sectors_32 = self._read_uint32_le(raw_data, 32, "Total sectors (32-bit)")

        # FAT32 extended fields.
        sectors_per_fat_32 = self._read_uint32_le(raw_data, 36, "Sectors per FAT (32-bit)")
        root_cluster = self._read_uint32_le(raw_data, 44, "Root cluster")
        volume_serial_number = self._read_uint32_le(raw_data, 67, "Volume serial number")
        volume_label = self._read_text(raw_data, 71, 11, "Volume label")
        filesystem_type = self._read_text(raw_data, 82, 8, "File system type")

        # The last two bytes of a valid boot sector should be 0x55AA.
        raw_boot_signature = self._read_slice(raw_data, 510, 2, "Boot sector signature")
        boot_signature = self._format_boot_signature(raw_boot_signature)

        # Some values exist in both an older FAT field and a FAT32 field.
        # For FAT32, prefer the FAT32-sized version when it is available.
        total_sectors = self._pick_total_sector_count(total_sectors_16, total_sectors_32)
        sectors_per_fat = self._pick_sectors_per_fat(sectors_per_fat_16, sectors_per_fat_32)
        root_dir_sectors = self._calculate_root_dir_sectors(root_entry_count, bytes_per_sector)
        total_size_bytes = total_sectors * bytes_per_sector

        validation_messages = self._build_validation_messages(
            raw_boot_signature=raw_boot_signature,
            bytes_per_sector=bytes_per_sector,
            sectors_per_cluster=sectors_per_cluster,
            sectors_per_fat_16=sectors_per_fat_16,
            sectors_per_fat_32=sectors_per_fat_32,
            filesystem_type=filesystem_type,
            root_entry_count=root_entry_count,
        )

        return BootSectorInfo(
            source_display=resolved_source.display_path,
            source_type=resolved_source.source_type,
            oem_name=oem_name,
            filesystem_type=filesystem_type,
            volume_label=volume_label,
            volume_serial_number=volume_serial_number,
            boot_signature=boot_signature,
            bytes_per_sector=bytes_per_sector,
            sectors_per_cluster=sectors_per_cluster,
            reserved_sector_count=reserved_sector_count,
            fat_count=fat_count,
            sectors_per_fat=sectors_per_fat,
            root_dir_sectors=root_dir_sectors,
            total_sectors=total_sectors,
            hidden_sectors=hidden_sectors,
            root_cluster=root_cluster,
            media_descriptor=media_descriptor,
            total_size_bytes=total_size_bytes,
            validation_messages=tuple(validation_messages),
        )

    @staticmethod
    def _decode_ascii(raw_data: bytes) -> str:
        return raw_data.decode("ascii", errors="ignore").replace("\x00", "").strip()

    def _read_slice(self, data: bytes, offset: int, size: int, field_name: str) -> bytes:
        end_offset = offset + size
        if end_offset > len(data):
            raise FAT32ReaderError(
                f"Invalid Boot Sector: field '{field_name}' needs bytes {offset}..{end_offset - 1}, "
                f"but the source only returned {len(data)} bytes."
            )
        return data[offset:end_offset]

    def _read_uint8(self, data: bytes, offset: int, field_name: str) -> int:
        raw_value = self._read_slice(data, offset, 1, field_name)
        return raw_value[0]

    def _read_uint16_le(self, data: bytes, offset: int, field_name: str) -> int:
        raw_value = self._read_slice(data, offset, 2, field_name)
        return int.from_bytes(raw_value, byteorder="little")

    def _read_uint32_le(self, data: bytes, offset: int, field_name: str) -> int:
        raw_value = self._read_slice(data, offset, 4, field_name)
        return int.from_bytes(raw_value, byteorder="little")

    def _read_text(self, data: bytes, offset: int, size: int, field_name: str) -> str:
        raw_value = self._read_slice(data, offset, size, field_name)
        return self._decode_ascii(raw_value)

    def _pick_total_sector_count(self, total_sectors_16: int, total_sectors_32: int) -> int:
        if total_sectors_16 != 0:
            return total_sectors_16
        return total_sectors_32

    def _pick_sectors_per_fat(self, sectors_per_fat_16: int, sectors_per_fat_32: int) -> int:
        if sectors_per_fat_32 != 0:
            return sectors_per_fat_32
        return sectors_per_fat_16

    def _calculate_root_dir_sectors(self, root_entry_count: int, bytes_per_sector: int) -> int:
        if bytes_per_sector <= 0:
            return 0

        root_dir_size_in_bytes = root_entry_count * self.DIRECTORY_ENTRY_SIZE
        return (root_dir_size_in_bytes + bytes_per_sector - 1) // bytes_per_sector

    def _format_boot_signature(self, raw_boot_signature: bytes) -> str:
        if raw_boot_signature == self.VALID_BOOT_SIGNATURE:
            return "0x55AA"
        return raw_boot_signature.hex(" ").upper()

    def _build_validation_messages(
        self,
        *,
        raw_boot_signature: bytes,
        bytes_per_sector: int,
        sectors_per_cluster: int,
        sectors_per_fat_16: int,
        sectors_per_fat_32: int,
        filesystem_type: str,
        root_entry_count: int,
    ) -> list[str]:
        validation_messages: list[str] = []

        if raw_boot_signature != self.VALID_BOOT_SIGNATURE:
            validation_messages.append("The Boot Sector signature is not 0x55AA.")
        if bytes_per_sector == 0:
            validation_messages.append("Bytes per sector is 0, so the Boot Sector may be corrupted.")
        if sectors_per_cluster == 0:
            validation_messages.append("Sectors per cluster is 0, so the Boot Sector may be corrupted.")
        if sectors_per_fat_32 == 0 and sectors_per_fat_16 != 0:
            validation_messages.append(
                "The sectors-per-FAT value looks closer to FAT12/FAT16 than FAT32."
            )
        if filesystem_type and "FAT32" not in filesystem_type.upper():
            validation_messages.append(
                f"The file system type string is '{filesystem_type}', so the device should be checked again."
            )
        if root_entry_count != 0:
            validation_messages.append(
                "Root entry count is not 0. In FAT32, the RDET sector count is typically 0."
            )

        return validation_messages
