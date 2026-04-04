from app.section2_txt_scanner import TxtFileEntry, TxtFileScanner


class TxtFileInfoReader(TxtFileScanner):
    """Placeholder for Section 3: read metadata and process info from a selected TXT file."""

    def read_txt_file_info(self, source: str, selected_file: TxtFileEntry) -> dict[str, object]:
        if not source.strip():
            raise ValueError("A FAT32 USB drive letter is required before reading TXT file details.")
        if not selected_file.file_name:
            raise ValueError("A TXT file must be selected before reading its details.")

        raise NotImplementedError(
            "Section 3 is reserved for reading TXT file details, timestamps, size, and process data."
        )
