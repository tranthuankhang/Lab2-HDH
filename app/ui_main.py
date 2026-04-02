from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
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
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.fat32_reader import FAT32Reader, FAT32ReaderError
from app.models import BootSectorInfo


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
    def __init__(self, status_callback) -> None:
        super().__init__()
        self._status_callback = status_callback
        self.reader = FAT32Reader()
        self.summary_labels: dict[str, QLabel] = {}

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter E: or a path to a .img / .bin / .ima file")
        self.source_input.returnPressed.connect(self.load_boot_sector)

        self.browse_button = QPushButton("Choose Image...")
        self.browse_button.clicked.connect(self.pick_image_file)

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
                "Review the first sector of a FAT32 drive or disk image and inspect the key structural fields in a clean academic layout.",
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
            "Enter a FAT32 drive letter such as E: or select a disk image file. Direct USB access on Windows may require Administrator privileges."
        )
        hint.setObjectName("sectionNote")
        hint.setWordWrap(True)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self.source_input, stretch=1)
        row.addWidget(self.browse_button)
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

    def pick_image_file(self) -> None:
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a Disk Image or Binary Dump",
            "",
            "Disk images (*.img *.ima *.bin *.dd);;All files (*.*)",
        )
        if selected_file:
            self.source_input.setText(selected_file)
            self._status_callback("Disk image selected. Ready to read the Boot Sector.")

    def load_boot_sector(self) -> None:
        source = self.source_input.text().strip()
        if not source:
            QMessageBox.information(
                self,
                "Missing Input",
                "Please enter a FAT32 drive letter such as E: or choose a disk image before reading.",
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
        self.detail_labels: dict[str, QLabel] = {}

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter E: or a path to a FAT32 disk image")

        self.browse_button = QPushButton("Choose Image...")
        self.browse_button.clicked.connect(self.pick_image_file)

        self.scan_button = QPushButton("List TXT Files")
        self.scan_button.setObjectName("primaryButton")
        self.scan_button.clicked.connect(self.show_scan_placeholder)

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
                "Text File Workflow",
                "A single workspace for listing FAT32 text files, reviewing the selected file details, and preparing the future scheduling output area.",
            )
        )
        layout.addWidget(self._build_source_group())
        layout.addWidget(self._build_content_grid(), stretch=1)

    def _build_source_group(self) -> QWidget:
        group = QGroupBox("TXT Discovery Source")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(12)

        hint = QLabel(
            "This source bar is reserved for the future FAT32 TXT scan. The UI is ready for drive or image input, while the scan logic will be connected later."
        )
        hint.setObjectName("sectionNote")
        hint.setWordWrap(True)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self.source_input, stretch=1)
        row.addWidget(self.browse_button)
        row.addWidget(self.scan_button)

        layout.addWidget(hint)
        layout.addLayout(row)
        return group

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
            "When the FAT32 scan is implemented, every .txt file found in the selected source will be listed here. Clicking a row will open the full detail panel on the right."
        )
        note.setObjectName("sectionNote")
        note.setWordWrap(True)

        layout.addWidget(note)
        layout.addWidget(self.catalog_table, stretch=1)
        layout.addWidget(
            build_empty_state_card(
                "Awaiting TXT Scan",
                "The future directory traversal will populate this catalog with every eligible .txt file, including nested folders.",
            )
        )
        return group

    def _build_detail_group(self) -> QWidget:
        group = QGroupBox("File Details")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(12)

        note = QLabel(
            "Selecting a TXT file will reveal the full metadata from Section 3 here, followed by the action that launches the scheduling view."
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
            "The selected TXT file will be runnable from this button once the parser and scheduler integration are connected."
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
            "Once a TXT file is selected, its process definitions will appear here so the scheduling configuration can be reviewed before execution."
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
            "Section 4 will render inside this panel after the selected TXT file is executed from the detail view."
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

    def pick_image_file(self) -> None:
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a Disk Image or Binary Dump",
            "",
            "Disk images (*.img *.ima *.bin *.dd);;All files (*.*)",
        )
        if selected_file:
            self.source_input.setText(selected_file)
            self._status_callback("TXT workflow source selected. Scan integration is ready to be connected later.")

    def show_scan_placeholder(self) -> None:
        message = (
            "This button is intentionally UI-only in the current revision. "
            "The FAT32 TXT scan logic will be connected later."
        )
        self._status_callback("TXT scan action is reserved for future integration.")
        QMessageBox.information(self, "TXT Scan Reserved", message)

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

        tabs = QTabWidget()
        tabs.addTab(build_scroll_page(BootSectorTab(self.show_status_message)), "Boot Sector")
        tabs.addTab(build_scroll_page(TextFilesTab(self.show_status_message)), "Text Files")

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
            "Boot Sector analysis is available in the first tab, while the second tab prepares the future TXT scheduling workflow."
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
