from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.section1_boot_sector_reader import FAT32ReaderError, BootSectorInfo, BootSectorReader
from app.section2_txt_scanner import TxtFileEntry, TxtFileScanner


APP_STYLE = """
QWidget {
    background: #f5f1e8;
    color: #22313d;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMainWindow {
    background: #efe8dc;
}
QFrame#windowHeader {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #fbf7ee,
        stop: 0.55 #f0e7d8,
        stop: 1 #eadfcf
    );
    border: 1px solid #cfbea0;
    border-radius: 24px;
}
QLabel#windowHeaderEyebrow {
    background: transparent;
    color: #7a6544;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 0.08em;
}
QLabel#windowHeaderTitle {
    background: transparent;
    color: #183b37;
    font-family: "Georgia";
    font-size: 16pt;
    font-weight: 700;
}
QLabel#windowHeaderText {
    background: transparent;
    color: #50606d;
    font-size: 9.2pt;
}
QTabWidget::pane {
    border: 1px solid #d5c7ae;
    border-radius: 18px;
    background: #fcfaf4;
    top: -1px;
}
QTabBar::tab {
    background: #ddd0ba;
    color: #4c5b66;
    padding: 12px 22px;
    margin-right: 8px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    min-width: 170px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #fcfaf4;
    color: #173d38;
    font-weight: 700;
}
QTabBar::tab:hover:!selected {
    background: #e6dac7;
}
QFrame#heroCard {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #faf5ea,
        stop: 1 #efe5d1
    );
    border: 1px solid #d1c09e;
    border-radius: 20px;
}
QLabel#heroEyebrow {
    background: transparent;
    color: #7c6644;
    font-size: 9pt;
    font-weight: 700;
}
QLabel#heroTitle {
    background: transparent;
    color: #173d38;
    font-family: "Georgia";
    font-size: 19pt;
    font-weight: 700;
}
QLabel#heroSubtitle {
    background: transparent;
    color: #52616d;
    font-size: 10pt;
}
QGroupBox {
    background: #fffdf8;
    border: 1px solid #d7c9b0;
    border-radius: 16px;
    margin-top: 14px;
    color: #263540;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    font-family: "Georgia";
    font-size: 11pt;
    font-weight: 700;
}
QLineEdit, QPlainTextEdit, QTableWidget {
    background: #fffaf2;
    border: 1px solid #d8ccb8;
    border-radius: 12px;
    padding: 8px;
    selection-background-color: #d7c19d;
    selection-color: #1d2c36;
}
QLineEdit:focus, QPlainTextEdit:focus, QTableWidget:focus {
    border: 1px solid #8e7550;
}
QTableWidget {
    gridline-color: #e7ddcf;
    alternate-background-color: #f8f3ea;
}
QTableWidget::item {
    padding: 4px;
}
QHeaderView::section {
    background: #ebe0cf;
    color: #31424f;
    padding: 9px;
    border: none;
    border-bottom: 1px solid #d7c9b0;
    font-weight: 700;
}
QPushButton {
    background: #e6d8c2;
    border: 1px solid #ccb997;
    border-radius: 11px;
    padding: 9px 16px;
    font-weight: 700;
    color: #31424f;
}
QPushButton:hover {
    background: #dfcfb6;
}
QPushButton:disabled {
    background: #efe6d8;
    color: #8a8d92;
    border-color: #ddd0bd;
}
QPushButton#primaryButton {
    background: #234d45;
    border-color: #1b3f39;
    color: white;
}
QPushButton#primaryButton:hover {
    background: #1f443d;
}
QPushButton#primaryButton:disabled {
    background: #8fa19b;
    border-color: #8fa19b;
    color: #f7f4ef;
}
QLabel#sectionNote {
    color: #5b6974;
    background: transparent;
}
QFrame#emptyStateCard {
    background: #faf6ee;
    border: 1px dashed #d3c5ae;
    border-radius: 14px;
}
QLabel#emptyStateTitle {
    background: transparent;
    color: #2f3d49;
    font-family: "Georgia";
    font-size: 11pt;
    font-weight: 700;
}
QLabel#emptyStateText {
    background: transparent;
    color: #5d6b76;
}
QSplitter::handle {
    background: #ddd1bf;
    border-radius: 3px;
    margin: 4px;
}
QStatusBar {
    background: #ece4d6;
    color: #3f4f5b;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
"""


def make_value_label(initial_text: str = "-") -> QLabel:
    label = QLabel(initial_text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return label


def build_hero_card(eyebrow: str, title: str, description: str) -> QFrame:
    card = QFrame()
    card.setObjectName("heroCard")

    layout = QVBoxLayout(card)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(6)

    eyebrow_label = QLabel(eyebrow.upper())
    eyebrow_label.setObjectName("heroEyebrow")

    title_label = QLabel(title)
    title_label.setObjectName("heroTitle")

    description_label = QLabel(description)
    description_label.setObjectName("heroSubtitle")
    description_label.setWordWrap(True)

    layout.addWidget(eyebrow_label)
    layout.addWidget(title_label)
    layout.addWidget(description_label)
    return card


def build_empty_state_card(title: str, description: str) -> QFrame:
    card = QFrame()
    card.setObjectName("emptyStateCard")

    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(6)

    title_label = QLabel(title)
    title_label.setObjectName("emptyStateTitle")

    description_label = QLabel(description)
    description_label.setObjectName("emptyStateText")
    description_label.setWordWrap(True)

    layout.addWidget(title_label)
    layout.addWidget(description_label)
    return card


def build_scroll_page(content: QWidget) -> QScrollArea:
    container = QWidget()
    container_layout = QVBoxLayout(container)
    container_layout.setContentsMargins(0, 0, 0, 0)
    container_layout.setSpacing(0)
    container_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
    container_layout.addWidget(content)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setWidget(container)
    return scroll_area


class BootSectorTab(QWidget):
    def __init__(self, status_callback, txt_scan_callback=None) -> None:
        super().__init__()
        self._status_callback = status_callback
        self._txt_scan_callback = txt_scan_callback
        self.reader = BootSectorReader()
        self.summary_labels: dict[str, QLabel] = {}

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter a FAT32 USB drive letter such as E:")
        self.source_input.returnPressed.connect(self.load_boot_sector)

        self.load_button = QPushButton("Read Boot Sector")
        self.load_button.setObjectName("primaryButton")
        self.load_button.clicked.connect(self.load_boot_sector)

        self.info_table = QTableWidget(0, 2)
        self.info_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.setAlternatingRowColors(True)
        self.info_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.info_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.info_table.setSelectionMode(QTableWidget.SingleSelection)
        self.info_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.info_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.info_table.setMinimumHeight(260)
        self.info_table.setWordWrap(True)
        self.info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.validation_box = QPlainTextEdit()
        self.validation_box.setReadOnly(True)
        self.validation_box.setPlaceholderText("Validation notes and quick diagnostics will appear here.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        layout.addWidget(
            build_hero_card(
                "Section 1",
                "Boot Sector Analysis",
                "Review the first sector of a FAT32 USB drive and inspect the key structural fields in a clean academic layout.",
            )
        )
        layout.addWidget(self._build_source_group())
        layout.addWidget(self._build_content_grid(), stretch=1)

    def _build_source_group(self) -> QWidget:
        group = QGroupBox("Source Selection")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(12)

        hint = QLabel(
            "Enter a FAT32 USB drive letter such as E:. This source will also be used to load TXT files in the other tab."
        )
        hint.setObjectName("sectionNote")
        hint.setWordWrap(True)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self.source_input, stretch=1)
        row.addWidget(self.load_button)

        layout.addWidget(hint)
        layout.addLayout(row)
        return group

    def _build_content_grid(self) -> QWidget:
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)

        table_group = self._build_table_group()
        validation_group = self._build_validation_group()
        summary_group = self._build_summary_group()

        summary_group.setMinimumWidth(350)
        validation_group.setMinimumHeight(140)
        self.validation_box.setMinimumHeight(72)

        layout.addWidget(table_group, 0, 0)
        layout.addWidget(validation_group, 1, 0)
        layout.addWidget(summary_group, 0, 1, 2, 1)
        layout.setColumnStretch(0, 5)
        layout.setColumnStretch(1, 3)
        layout.setRowStretch(0, 3)
        layout.setRowStretch(1, 2)
        return container

    def _build_table_group(self) -> QWidget:
        group = QGroupBox("Boot Sector Field Table")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(12)

        note = QLabel(
            "Each row corresponds to a core FAT32 field that can be checked against the assignment requirements."
        )
        note.setObjectName("sectionNote")
        note.setWordWrap(True)

        layout.addWidget(note)
        layout.addWidget(self.info_table)
        return group

    def _build_summary_group(self) -> QWidget:
        group = QGroupBox("At a Glance")

        layout = QFormLayout(group)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setLabelAlignment(Qt.AlignLeft)
        layout.setFormAlignment(Qt.AlignTop)
        layout.setSpacing(12)

        for key, label_text in (
            ("source", "Source"),
            ("source_type", "Source Type"),
            ("filesystem", "File System"),
            ("label", "Volume Label"),
            ("signature", "Boot Signature"),
        ):
            value_label = make_value_label()
            self.summary_labels[key] = value_label
            layout.addRow(f"{label_text}:", value_label)

        return group

    def _build_validation_group(self) -> QWidget:
        group = QGroupBox("Validation Notes")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(10)

        note = QLabel(
            "Warnings and quick observations are collected here so the Boot Sector can be reviewed without scanning the full table."
        )
        note.setObjectName("sectionNote")
        note.setWordWrap(True)

        layout.addWidget(note)
        layout.addWidget(self.validation_box)
        return group

    def load_boot_sector(self) -> None:
        source = self.source_input.text().strip()
        if not source:
            QMessageBox.information(
                self,
                "Missing Input",
                "Please enter a FAT32 USB drive letter such as E: before reading.",
            )
            return

        try:
            info = self.reader.read_boot_sector(source)
        except FAT32ReaderError as exc:
            self._status_callback("Boot Sector read failed.")
            QMessageBox.critical(self, "Unable to Read the Boot Sector", str(exc))
            return

        self._populate_boot_sector(info)
        self._status_callback(f"Boot Sector loaded successfully from {info.source_display}.")
        if self._txt_scan_callback is not None:
            self._txt_scan_callback(info.source_display)

    def _populate_boot_sector(self, info: BootSectorInfo) -> None:
        self.summary_labels["source"].setText(info.source_display)
        self.summary_labels["source_type"].setText(info.source_type_label)
        self.summary_labels["filesystem"].setText(info.filesystem_type or "(unknown)")
        self.summary_labels["label"].setText(info.volume_label or "(empty)")
        self.summary_labels["signature"].setText(info.boot_signature)

        rows = info.table_rows()
        self.info_table.setRowCount(len(rows))
        for row_index, (field_name, value) in enumerate(rows):
            field_item = QTableWidgetItem(field_name)
            value_item = QTableWidgetItem(value)
            field_item.setFlags(field_item.flags() ^ Qt.ItemIsEditable)
            value_item.setFlags(value_item.flags() ^ Qt.ItemIsEditable)
            self.info_table.setItem(row_index, 0, field_item)
            self.info_table.setItem(row_index, 1, value_item)

        self._resize_info_table_to_contents()

        if info.validation_messages:
            self.validation_box.setPlainText("\n".join(f"- {item}" for item in info.validation_messages))
        else:
            self.validation_box.setPlainText(
                "No major warnings were detected. The Boot Sector appears structurally consistent for the selected source."
            )

    def _resize_info_table_to_contents(self) -> None:
        # Let the outer page handle scrolling, so this table grows downward
        # instead of showing its own vertical scrollbar.
        self.info_table.resizeRowsToContents()

        total_height = self.info_table.frameWidth() * 2
        total_height += self.info_table.horizontalHeader().height()

        for row_index in range(self.info_table.rowCount()):
            total_height += self.info_table.rowHeight(row_index)

        if self.info_table.horizontalScrollBar().isVisible():
            total_height += self.info_table.horizontalScrollBar().height()

        self.info_table.setFixedHeight(max(total_height + 4, 260))


class TextFilesTab(QWidget):
    def __init__(self, status_callback) -> None:
        super().__init__()
        self._status_callback = status_callback
        self.reader = TxtFileScanner()
        self.catalog_entries: list[TxtFileEntry] = []
        self.detail_labels: dict[str, QLabel] = {}
        self.current_source: str | None = None
        self.catalog_status_label = QLabel(
            "Read the Boot Sector in the first tab to load TXT files here automatically."
        )
        self.catalog_status_label.setObjectName("sectionNote")
        self.catalog_status_label.setWordWrap(True)

        self.catalog_table = QTableWidget(0, 3)
        self.catalog_table.setHorizontalHeaderLabels(["TXT File", "Directory", "Size"])
        self.catalog_table.verticalHeader().setVisible(False)
        self.catalog_table.setAlternatingRowColors(True)
        self.catalog_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.catalog_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.catalog_table.setSelectionMode(QTableWidget.SingleSelection)
        self.catalog_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.catalog_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.process_table = QTableWidget(0, 5)
        self.process_table.setHorizontalHeaderLabels(
            ["Process", "Arrival Time", "CPU Burst", "Queue / Priority", "Time Slice"]
        )
        self.process_table.verticalHeader().setVisible(False)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.process_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.process_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.process_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.process_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.process_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.run_button = QPushButton("Run Selected TXT File")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self.show_run_placeholder)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        layout.addWidget(
            build_hero_card(
                "Sections 2 to 4",
                "TXT Listing Workspace",
                "Section 2 is active here: after Boot Sector is read in the first tab, the app automatically scans the FAT32 USB drive and lists every .txt file.",
            )
        )
        layout.addWidget(self._build_content_grid(), stretch=1)

    def _build_content_grid(self) -> QWidget:
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)

        catalog_group = self._build_catalog_group()
        detail_group = self._build_detail_group()
        process_group = self._build_process_group()
        output_group = self._build_output_group()

        catalog_group.setMinimumWidth(320)
        detail_group.setMinimumHeight(240)
        process_group.setMinimumHeight(210)
        output_group.setMinimumHeight(180)

        layout.addWidget(catalog_group, 0, 0, 2, 1)
        layout.addWidget(detail_group, 0, 1)
        layout.addWidget(process_group, 1, 1)
        layout.addWidget(output_group, 2, 0, 1, 2)
        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 3)
        layout.setRowStretch(0, 3)
        layout.setRowStretch(1, 3)
        layout.setRowStretch(2, 2)
        return container

    def _build_catalog_group(self) -> QWidget:
        group = QGroupBox("TXT File Catalog")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(12)

        note = QLabel(
            "Every .txt file discovered on the FAT32 USB drive will be listed here after Boot Sector is read in the first tab."
        )
        note.setObjectName("sectionNote")
        note.setWordWrap(True)

        self.catalog_empty_state = build_empty_state_card(
            "Awaiting Boot Sector Read",
            "Go to the Boot Sector tab, enter the USB drive letter, and press Read Boot Sector. TXT files will appear here automatically.",
        )

        layout.addWidget(note)
        layout.addWidget(self.catalog_status_label)
        layout.addWidget(self.catalog_table, stretch=1)
        layout.addWidget(self.catalog_empty_state)
        return group

    def _build_detail_group(self) -> QWidget:
        group = QGroupBox("File Details")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(12)

        note = QLabel(
            "Section 3 is intentionally left for a separate implementation. This panel is kept ready, but the metadata logic is not connected here."
        )
        note.setObjectName("sectionNote")
        note.setWordWrap(True)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setSpacing(12)

        for key, label_text in (
            ("file_name", "File Name"),
            ("directory", "Directory"),
            ("created_at", "Created At"),
            ("modified_at", "Modified At"),
            ("starting_cluster", "Starting Cluster"),
            ("file_size", "File Size"),
        ):
            value_label = make_value_label()
            self.detail_labels[key] = value_label
            form.addRow(f"{label_text}:", value_label)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        action_row.addWidget(self.run_button, alignment=Qt.AlignLeft)

        action_note = QLabel(
            "This handoff to Sections 3 and 4 is intentionally reserved for the remaining work."
        )
        action_note.setObjectName("sectionNote")
        action_note.setWordWrap(True)
        action_row.addWidget(action_note, stretch=1)

        layout.addWidget(note)
        layout.addLayout(form)
        layout.addLayout(action_row)
        return group

    def _build_process_group(self) -> QWidget:
        group = QGroupBox("Parsed Process Table")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(12)

        note = QLabel(
            "This table is reserved for Section 3 and is intentionally not populated in this revision."
        )
        note.setObjectName("sectionNote")
        note.setWordWrap(True)

        layout.addWidget(note)
        layout.addWidget(self.process_table)
        return group

    def _build_output_group(self) -> QWidget:
        group = QGroupBox("Scheduling Output")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(12)

        note = QLabel(
            "Section 4 remains reserved here and is intentionally not implemented in this revision."
        )
        note.setObjectName("sectionNote")
        note.setWordWrap(True)

        layout.addWidget(note)
        layout.addWidget(
            build_empty_state_card(
                "Reserved for Scheduling Results",
                "The Gantt chart, waiting time, turnaround time, and related scheduling summaries will appear here in a future implementation.",
            )
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
            self.catalog_status_label.setText(
                f"TXT scan for {source} failed. Please verify the USB drive and try reading Boot Sector again."
            )
            self.catalog_empty_state.setVisible(True)
            self.catalog_table.clearContents()
            self.catalog_table.setRowCount(0)
            self._status_callback("TXT scan failed.")
            QMessageBox.critical(self, "Unable to Scan TXT Files", str(exc))
            return

        self.current_source = source
        self.catalog_entries = txt_files
        self._populate_catalog_table(txt_files)
        self._clear_reserved_panels()

        file_count = len(txt_files)
        if file_count == 0:
            self.catalog_status_label.setText(f"Automatic TXT scan completed for {source}. No .txt files were found.")
        elif file_count == 1:
            self.catalog_status_label.setText(f"Automatic TXT scan completed for {source}. Found 1 .txt file.")
        else:
            self.catalog_status_label.setText(
                f"Automatic TXT scan completed for {source}. Found {file_count} .txt files."
            )

        if file_count == 0:
            self._status_callback(f"No TXT files were found on {source.upper()}.")
        elif file_count == 1:
            self._status_callback(f"Found 1 TXT file on {source.upper()}.")
        else:
            self._status_callback(f"Found {file_count} TXT files on {source.upper()}.")

    def reset_waiting_state(self) -> None:
        self.current_source = None
        self.catalog_entries = []
        self.catalog_status_label.setText(
            "Read the Boot Sector in the first tab to load TXT files here automatically."
        )
        self.catalog_empty_state.setVisible(True)
        self.catalog_table.clearContents()
        self.catalog_table.setRowCount(0)
        self._clear_reserved_panels()

    def sync_with_boot_sector_input(self, source_text: str) -> None:
        normalized_source = source_text.strip().upper()
        current_source = (self.current_source or "").strip().upper()
        if normalized_source == current_source:
            return

        self.reset_waiting_state()

    def _populate_catalog_table(self, txt_files: list[TxtFileEntry]) -> None:
        self.catalog_table.clearContents()
        self.catalog_table.setRowCount(len(txt_files))

        for row_index, txt_file in enumerate(txt_files):
            for column_index, value in enumerate(
                (txt_file.file_name, txt_file.directory_display, txt_file.size_display)
            ):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.catalog_table.setItem(row_index, column_index, item)

        self.catalog_empty_state.setVisible(not txt_files)

    def _clear_reserved_panels(self) -> None:
        for value_label in self.detail_labels.values():
            value_label.setText("-")
        self.process_table.clearContents()
        self.process_table.setRowCount(0)

    def show_run_placeholder(self) -> None:
        message = (
            "This button marks the future handoff from Section 3 to Section 4. "
            "The scheduling execution logic has intentionally not been implemented in this UI revision."
        )
        self._status_callback("TXT run action is reserved for future integration.")
        QMessageBox.information(self, "Scheduling Action Reserved", message)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lab 02 | FAT32 Academic Explorer")
        self.resize(1280, 820)
        self.setMinimumSize(1100, 720)

        self.text_files_tab = TextFilesTab(self.show_status_message)
        self.boot_sector_tab = BootSectorTab(self.show_status_message, self.text_files_tab.load_txt_files_for_source)

        tabs = QTabWidget()
        tabs.addTab(build_scroll_page(self.boot_sector_tab), "Boot Sector")
        tabs.addTab(build_scroll_page(self.text_files_tab), "Text Files")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)
        layout.addWidget(self._build_window_header())
        layout.addWidget(tabs, stretch=1)
        self.setCentralWidget(container)

        status_bar = QStatusBar()
        status_bar.showMessage("Ready for Boot Sector review.")
        self.setStatusBar(status_bar)
        self.boot_sector_tab.source_input.textChanged.connect(self.text_files_tab.sync_with_boot_sector_input)

    def _build_window_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("windowHeader")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(3)

        eyebrow = QLabel("OPERATING SYSTEMS LABORATORY")
        eyebrow.setObjectName("windowHeaderEyebrow")
        eyebrow.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        title = QLabel("FAT32 Inspection and TXT Scheduling Workspace")
        title.setObjectName("windowHeaderTitle")
        title.setWordWrap(True)
        title.setMaximumWidth(700)
        title.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        description = QLabel(
            "Boot Sector analysis and TXT file listing are available, while Sections 3 and 4 remain reserved for the remaining implementation."
        )
        description.setObjectName("windowHeaderText")
        description.setWordWrap(True)
        description.setMaximumWidth(760)
        description.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(description)
        return card

    def show_status_message(self, message: str) -> None:
        self.statusBar().showMessage(message, 5000)


def run() -> int:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("Lab 02 | FAT32 Academic Explorer")
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()
    return app.exec()
