from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.drive_reader import DriveReader
from app.section1_boot_sector_reader import FAT32ReaderError, BootSectorInfo, BootSectorReader
from app.section2_txt_scanner import TxtFileEntry, TxtFileScanner


APP_STYLE = """
QWidget {
    background-color: #faf7f0;
    font-family: "Segoe UI";
    font-size: 11pt;
    color: #4f3d30;
}
QLabel {
    background: transparent;
}
QMainWindow {
    background-color: #f8f5ee;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #ddd2c1;
    border-radius: 6px;
    margin-top: 10px;
    background-color: #fffdf9;
}
QGroupBox::title {
    left: 10px;
    padding: 0 4px;
}
QLineEdit, QTableWidget {
    border: 1px solid #dfd4c4;
    background-color: #fffefa;
    selection-background-color: #d7c4a8;
    selection-color: #463428;
}
QLineEdit:focus {
    border: 1px solid #b29472;
}
QTableWidget {
    alternate-background-color: #fcf8f1;
    gridline-color: #ece2d6;
}
QPushButton {
    padding: 6px 14px;
    background-color: #efe5d6;
    color: #5f4a39;
    border: 1px solid #d8cab6;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #e8dccb;
}
QPushButton:pressed {
    background-color: #deceb8;
}
QLabel#noteLabel {
    color: #8b725d;
}
QHeaderView::section {
    background-color: #f3ebde;
    color: #5f4a39;
    border: 1px solid #e0d4c3;
    padding: 6px;
    font-weight: bold;
}
QTabWidget::pane {
    border: 1px solid #ddd2c1;
    background: #fffdf9;
}
QTabBar::tab {
    background: #efe6d8;
    color: #786250;
    padding: 8px 16px;
    margin-right: 3px;
    border: 1px solid #ddd2c1;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #fffdf9;
    color: #5f4a39;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background: #f3eadf;
}
QScrollArea {
    border: none;
    background: #faf7f0;
}
QScrollArea > QWidget > QWidget {
    background: #faf7f0;
}
QStatusBar {
    background: #f3ece0;
    color: #786250;
}
"""


def create_note(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("noteLabel")
    label.setWordWrap(True)
    return label


def create_value_label() -> QLabel:
    label = QLabel("-")
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return label


def create_table(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    return table


def set_table_text(table: QTableWidget, row: int, column: int, text: str) -> None:
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
    table.setItem(row, column, item)


def create_scroll_page(content: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    return scroll


class BootSectorTab(QWidget):
    def __init__(self, status_callback, txt_scan_callback=None, drive_reader: DriveReader | None = None) -> None:
        super().__init__()
        self.status_callback = status_callback
        self.txt_scan_callback = txt_scan_callback
        self.reader = BootSectorReader(drive_reader)

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter a FAT32 USB drive letter such as E:")
        self.source_input.returnPressed.connect(self.load_boot_sector)

        self.read_button = QPushButton("Read")
        self.read_button.clicked.connect(self.load_boot_sector)

        self.info_table = create_table(["Field", "Value"])
        self.info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Section 1 - Boot Sector")
        title.setStyleSheet("font-size: 15pt; font-weight: bold;")
        main_layout.addWidget(title)
        main_layout.addWidget(create_note("Read the Boot Sector of a FAT32 USB drive and show the required fields."))
        main_layout.addWidget(self._build_source_group())
        main_layout.addWidget(self._build_table_group())

    def _build_source_group(self) -> QGroupBox:
        group = QGroupBox("Source")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(
            create_note("Enter a drive letter like E:. The same source will be used for the TXT tab.")
        )

        row = QHBoxLayout()
        row.addWidget(self.source_input, 1)
        row.addWidget(self.read_button)
        layout.addLayout(row)
        return group

    def _build_table_group(self) -> QGroupBox:
        group = QGroupBox("Boot Sector Information")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.info_table)
        return group

    def load_boot_sector(self) -> None:
        source = self.source_input.text().strip()
        if not source:
            QMessageBox.information(self, "Missing Input", "Please enter a FAT32 USB drive letter such as E:.")
            return

        try:
            info = self.reader.read_boot_sector(source)
        except FAT32ReaderError as exc:
            self.status_callback("Boot Sector read failed.")
            QMessageBox.critical(self, "Unable to Read Boot Sector", str(exc))
            return

        self.show_boot_sector(info)
        self.status_callback(f"Boot Sector loaded from {info.source_display}.")

        if self.txt_scan_callback is not None:
            self.txt_scan_callback(info.source_display)

    def show_boot_sector(self, info: BootSectorInfo) -> None:
        rows = info.table_rows()
        self.info_table.setRowCount(len(rows))

        for row_index, (field_name, value) in enumerate(rows):
            set_table_text(self.info_table, row_index, 0, field_name)
            set_table_text(self.info_table, row_index, 1, value)


class TextFilesTab(QWidget):
    def __init__(self, status_callback, drive_reader: DriveReader | None = None) -> None:
        super().__init__()
        self.status_callback = status_callback
        self.reader = TxtFileScanner(drive_reader)
        self.catalog_entries: list[TxtFileEntry] = []
        self.current_source: str | None = None
        self.detail_labels: dict[str, QLabel] = {}

        self.status_label = create_note("Read the Boot Sector in the first tab to load TXT files automatically.")

        self.catalog_table = create_table(["TXT File", "Directory", "Size"])
        self.catalog_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.catalog_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.catalog_table.itemSelectionChanged.connect(self.show_selected_file_details)

        self.process_table = create_table(
            [
                "Process ID",
                "Arrival Time",
                "CPU Burst Time",
                "Priority Queue ID",
                "Time Slice",
                "Scheduling Algorithm Name",
            ]
        )
        self.process_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.process_table.horizontalHeader().setStretchLastSection(False)
        self.process_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.process_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.process_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.process_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.process_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.process_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Sections 2, 3 and 4 - TXT Files")
        title.setStyleSheet("font-size: 15pt; font-weight: bold;")
        main_layout.addWidget(title)
        main_layout.addWidget(
            create_note("Section 2 is active. After reading Boot Sector, the app scans all .txt files on the USB.")
        )
        main_layout.addWidget(self._build_catalog_group())

        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(12)
        detail_group = self._build_detail_group()
        process_group = self._build_process_group()
        process_group.setMinimumWidth(820)
        lower_layout.addWidget(detail_group, 1)
        lower_layout.addWidget(process_group, 3)
        main_layout.addLayout(lower_layout)

        main_layout.addWidget(self._build_section4_group())

    def _build_catalog_group(self) -> QGroupBox:
        group = QGroupBox("Section 2 - TXT File List")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addWidget(self.catalog_table)
        return group

    def _build_detail_group(self) -> QGroupBox:
        group = QGroupBox("Section 3 - Selected TXT File")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(
            create_note(
                "This panel only keeps the required fields for Section 3. Date created and time created "
                "will be filled when Section 3 is implemented."
            )
        )

        form = QFormLayout()
        form.setSpacing(10)

        for key, label_text in (
            ("name", "Name"),
            ("date_created", "Date created"),
            ("time_created", "Time created"),
            ("total_size", "Total Size"),
        ):
            value_label = create_value_label()
            self.detail_labels[key] = value_label
            form.addRow(f"{label_text}:", value_label)

        layout.addLayout(form)
        return group

    def _build_process_group(self) -> QGroupBox:
        group = QGroupBox("Section 3 - Process Information Table")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(
            create_note(
                "This table is reserved for process information parsed from the selected TXT file, "
                "including the scheduling algorithm name for each process row."
            )
        )
        layout.addWidget(self.process_table)
        return group

    def _build_section4_group(self) -> QGroupBox:
        group = QGroupBox("Section 4 - Scheduling")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(
            create_note("Section 4 is still reserved. The scheduling algorithm output will be added later.")
        )
        return group

    def load_txt_files_for_source(self, source: str) -> None:
        source = source.strip()
        if not source:
            self.reset_waiting_state()
            return

        try:
            txt_files = self.reader.list_txt_files(source)
        except FAT32ReaderError as exc:
            self.current_source = source
            self.catalog_entries = []
            self.catalog_table.clearContents()
            self.catalog_table.setRowCount(0)
            self.clear_section3()
            self.status_label.setText(f"TXT scan failed for {source}. Please read the Boot Sector again.")
            self.status_callback("TXT scan failed.")
            QMessageBox.critical(self, "Unable to Scan TXT Files", str(exc))
            return

        self.current_source = source
        self.catalog_entries = txt_files
        self.show_txt_files(txt_files)
        self.clear_section3()

        file_count = len(txt_files)
        if file_count == 0:
            self.status_label.setText(f"Finished scanning {source}. No .txt files were found.")
            self.status_callback(f"No TXT files were found on {source.upper()}.")
            return

        if file_count == 1:
            self.status_label.setText(f"Finished scanning {source}. Found 1 .txt file.")
            self.status_callback(f"Found 1 TXT file on {source.upper()}.")
        else:
            self.status_label.setText(f"Finished scanning {source}. Found {file_count} .txt files.")
            self.status_callback(f"Found {file_count} TXT files on {source.upper()}.")

        self.catalog_table.selectRow(0)

    def reset_waiting_state(self) -> None:
        self.current_source = None
        self.catalog_entries = []
        self.catalog_table.clearContents()
        self.catalog_table.setRowCount(0)
        self.clear_section3()
        self.status_label.setText("Read the Boot Sector in the first tab to load TXT files automatically.")

    def sync_with_boot_sector_input(self, source_text: str) -> None:
        normalized_source = source_text.strip().upper()
        current_source = (self.current_source or "").strip().upper()

        if normalized_source != current_source:
            self.reset_waiting_state()

    def show_txt_files(self, txt_files: list[TxtFileEntry]) -> None:
        self.catalog_table.clearContents()
        self.catalog_table.setRowCount(len(txt_files))

        for row_index, txt_file in enumerate(txt_files):
            set_table_text(self.catalog_table, row_index, 0, txt_file.file_name)
            set_table_text(self.catalog_table, row_index, 1, txt_file.get_directory_display())
            set_table_text(self.catalog_table, row_index, 2, txt_file.get_size_display())

    def show_selected_file_details(self) -> None:
        selected_rows = self.catalog_table.selectionModel().selectedRows()
        if not selected_rows:
            self.clear_section3()
            return

        row = selected_rows[0].row()
        if row < 0 or row >= len(self.catalog_entries):
            self.clear_section3()
            return

        selected_file = self.catalog_entries[row]
        self.detail_labels["name"].setText(selected_file.file_name)
        self.detail_labels["date_created"].setText("Reserved for Section 3")
        self.detail_labels["time_created"].setText("Reserved for Section 3")
        self.detail_labels["total_size"].setText(selected_file.get_size_display())

        self.process_table.clearContents()
        self.process_table.setRowCount(0)

    def clear_section3(self) -> None:
        for label in self.detail_labels.values():
            label.setText("-")

        self.process_table.clearContents()
        self.process_table.setRowCount(0)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FAT32 Explorer")
        self.resize(1420, 860)
        self.setMinimumSize(1320, 760)

        self.drive_reader = DriveReader()
        self.text_files_tab = TextFilesTab(self.show_status_message, self.drive_reader)
        self.boot_sector_tab = BootSectorTab(
            self.show_status_message,
            self.text_files_tab.load_txt_files_for_source,
            self.drive_reader,
        )

        tabs = QTabWidget()
        tabs.addTab(create_scroll_page(self.boot_sector_tab), "Boot Sector")
        tabs.addTab(create_scroll_page(self.text_files_tab), "Text Files")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("FAT32 Explorer")
        title.setStyleSheet("font-size: 17pt; font-weight: bold; color: #5c4331;")

        layout.addWidget(title)
        layout.addWidget(tabs)
        self.setCentralWidget(container)

        status_bar = QStatusBar()
        status_bar.showMessage("Ready.")
        self.setStatusBar(status_bar)

        self.boot_sector_tab.source_input.textChanged.connect(self.text_files_tab.sync_with_boot_sector_input)

    def show_status_message(self, message: str) -> None:
        self.statusBar().showMessage(message, 5000)


def run() -> int:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("FAT32 Explorer")
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()
    return app.exec()
