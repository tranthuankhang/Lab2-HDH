from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.models import BootSectorInfo


class FAT32ReaderError(Exception):
    """Raised when a FAT32 source cannot be read or parsed."""


@dataclass(slots=True)
class ResolvedSource:
    display_path: str
    open_path: str
    source_type: str


class FAT32Reader:
    BOOT_SECTOR_SIZE = 512
    DIRECTORY_ENTRY_SIZE = 32
    VALID_BOOT_SIGNATURE = b"\x55\xAA"
    DRIVE_PATTERN = re.compile(r"^[A-Za-z]:\\?$")

    def read_boot_sector(self, source: str) -> BootSectorInfo:
        resolved_source = self._resolve_source(source)
        raw_data = self.read_bytes(resolved_source.display_path, 0, self.BOOT_SECTOR_SIZE)
        return self._parse_boot_sector(raw_data, resolved_source)

    def read_bytes(self, source: str, offset: int, size: int) -> bytes:
        resolved_source = self._resolve_source(source)

        try:
            with open(resolved_source.open_path, "rb", buffering=0) as stream:
                stream.seek(offset)
                raw_data = stream.read(size)
        except PermissionError as exc:
            raise FAT32ReaderError(
                "Unable to access the selected source. If you are reading a USB drive directly, "
                "please try running the application with Administrator privileges."
            ) from exc
        except FileNotFoundError as exc:
            raise FAT32ReaderError("The selected path or drive could not be found.") from exc
        except OSError as exc:
            raise FAT32ReaderError(f"An error occurred while reading the source: {exc}") from exc

        if len(raw_data) != size:
            raise FAT32ReaderError(
                f"Unable to read {size} bytes at offset {offset}. Only {len(raw_data)} bytes were returned."
            )

        return raw_data

    def read_sector(self, source: str, sector_index: int, bytes_per_sector: int = 512) -> bytes:
        return self.read_bytes(source, sector_index * bytes_per_sector, bytes_per_sector)

    def list_txt_files(self, source: str) -> list[str]:
        raise NotImplementedError("FAT32 TXT file discovery will be added in a future step.")

    def _resolve_source(self, source: str) -> ResolvedSource:
        cleaned_source = source.strip().strip('"')
        if not cleaned_source:
            raise FAT32ReaderError("Please enter a FAT32 drive letter such as E: or a disk image path.")

        if self.DRIVE_PATTERN.match(cleaned_source):
            drive_letter = cleaned_source[0].upper()
            normalized_drive = f"{drive_letter}:"
            return ResolvedSource(
                display_path=normalized_drive,
                open_path=rf"\\.\{normalized_drive}",
                source_type="drive",
            )

        candidate = Path(cleaned_source).expanduser()
        if not candidate.exists():
            raise FAT32ReaderError("The selected disk image path does not exist.")

        return ResolvedSource(
            display_path=str(candidate.resolve()),
            open_path=str(candidate.resolve()),
            source_type="image",
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
        # FAT stores total sector count in the 16-bit slot for small volumes.
        # Larger FAT32 volumes usually put the real value in the 32-bit slot.
        if total_sectors_16 != 0:
            return total_sectors_16
        return total_sectors_32

    def _pick_sectors_per_fat(self, sectors_per_fat_16: int, sectors_per_fat_32: int) -> int:
        # FAT32 normally uses the 32-bit field at offset 36.
        # We still keep the 16-bit fallback so the UI can show "something sensible"
        # even if the source is unusual or not actually FAT32.
        if sectors_per_fat_32 != 0:
            return sectors_per_fat_32
        return sectors_per_fat_16

    def _calculate_root_dir_sectors(self, root_entry_count: int, bytes_per_sector: int) -> int:
        # FAT directory entries are 32 bytes each.
        # This formula rounds up so a partially used sector still counts as 1 full sector.
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
