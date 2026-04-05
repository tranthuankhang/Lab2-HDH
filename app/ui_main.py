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
from app.section1_boot_sector_reader import FAT32ReaderError, BootSectorReader
from app.section3_txt_info_reader import TxtFileInfoReader
from app.section4_scheduler_runner import SchedulingRunner


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


# tạo label ghi chú nhỏ
def create_note(text):
    label = QLabel(text)
    label.setObjectName("noteLabel")
    label.setWordWrap(True)
    return label


# tạo label hiển thị giá trị, cho phép bôi đen copy
def create_value_label():
    label = QLabel("-")
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return label


# tạo bảng với các cột theo danh sách header
def create_table(headers):
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    return table


# set text vào 1 ô trong bảng, không cho chỉnh sửa
def set_table_text(table, row, col, text):
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
    table.setItem(row, col, item)


# bọc widget vào scroll area
def create_scroll_page(content):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    return scroll


class BootSectorTab(QWidget):
    def __init__(self, status_callback, txt_scan_callback=None, drive_reader=None):
        super().__init__()
        self.status_callback = status_callback
        self.txt_scan_callback = txt_scan_callback
        self.reader = BootSectorReader(drive_reader)

        # ô nhập ổ đĩa
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter a FAT32 USB drive letter such as E:")
        self.source_input.returnPressed.connect(self.load_boot_sector)

        # nút đọc boot sector
        self.read_button = QPushButton("Read")
        self.read_button.clicked.connect(self.load_boot_sector)

        # bảng hiển thị thông tin boot sector
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

    def _build_source_group(self):
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

    def _build_table_group(self):
        group = QGroupBox("Boot Sector Information")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.info_table)
        return group

    def load_boot_sector(self):
        source = self.source_input.text().strip()
        if source == "":
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

    def show_boot_sector(self, info):
        rows = info.table_rows()
        self.info_table.setRowCount(len(rows))

        for i, (field_name, value) in enumerate(rows):
            set_table_text(self.info_table, i, 0, field_name)
            set_table_text(self.info_table, i, 1, value)


class TextFilesTab(QWidget):
    def __init__(self, status_callback, drive_reader=None):
        super().__init__()
        self.status_callback = status_callback
        self.reader = TxtFileInfoReader(drive_reader)
        self.scheduler = SchedulingRunner()
        self.catalog_entries = []
        self.current_source = None
        self.detail_labels = {}
        self.last_parsed_info = None

        self.status_label = create_note("Read the Boot Sector in the first tab to load TXT files automatically.")

        # bảng danh sách file txt tìm được
        self.catalog_table = create_table(["TXT File", "Directory", "Size"])
        self.catalog_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.catalog_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.catalog_table.itemSelectionChanged.connect(self.show_selected_file_details)

        # bảng thông tin process đọc từ file txt
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

    def _build_catalog_group(self):
        group = QGroupBox("Section 2 - TXT File List")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addWidget(self.catalog_table)
        return group

    def _build_detail_group(self):
        group = QGroupBox("Section 3 - Selected TXT File")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(
            create_note(
                "File metadata extracted from the FAT32 directory entry."
            )
        )

        form = QFormLayout()
        form.setSpacing(10)

        name_label = create_value_label()
        self.detail_labels["name"] = name_label
        form.addRow("Name:", name_label)

        date_label = create_value_label()
        self.detail_labels["date_created"] = date_label
        form.addRow("Date created:", date_label)

        time_label = create_value_label()
        self.detail_labels["time_created"] = time_label
        form.addRow("Time created:", time_label)

        size_label = create_value_label()
        self.detail_labels["total_size"] = size_label
        form.addRow("Total Size:", size_label)

        layout.addLayout(form)
        return group

    def _build_process_group(self):
        group = QGroupBox("Section 3 - Process Information Table")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(
            create_note(
                "Process information parsed from the selected TXT file."
            )
        )
        layout.addWidget(self.process_table)
        return group

    def _build_section4_group(self):
        group = QGroupBox("Section 4 - Scheduling")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        # nút chạy scheduling
        self.run_scheduling_button = QPushButton("Run Scheduling")
        self.run_scheduling_button.setEnabled(False)
        self.run_scheduling_button.clicked.connect(self.run_scheduling)
        layout.addWidget(self.run_scheduling_button)

        # bảng Gantt chart (scheduling diagram)
        gantt_label = QLabel("CPU Scheduling Diagram")
        gantt_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(gantt_label)

        self.gantt_table = create_table(["[Start - End]", "Queue", "Process"])
        self.gantt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.gantt_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.gantt_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.gantt_table)

        # bảng thống kê Turnaround & Waiting
        stats_label = QLabel("Process Statistics")
        stats_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(stats_label)

        self.stats_table = create_table(
            ["Process", "Arrival", "Burst", "Finish", "Turnaround", "Waiting"]
        )
        for col in range(6):
            self.stats_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        layout.addWidget(self.stats_table)

        # label trung bình
        form = QFormLayout()
        form.setSpacing(6)
        self.avg_turnaround_label = create_value_label()
        self.avg_waiting_label = create_value_label()
        form.addRow("Average Turnaround Time:", self.avg_turnaround_label)
        form.addRow("Average Waiting Time:", self.avg_waiting_label)
        layout.addLayout(form)

        return group

    def load_txt_files_for_source(self, source):
        source = source.strip()
        if source == "":
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

    def reset_waiting_state(self):
        self.current_source = None
        self.catalog_entries = []
        self.catalog_table.clearContents()
        self.catalog_table.setRowCount(0)
        self.clear_section3()
        self.status_label.setText("Read the Boot Sector in the first tab to load TXT files automatically.")

    def sync_with_boot_sector_input(self, source_text):
        normalized_source = source_text.strip().upper()

        if self.current_source is not None:
            current_source = self.current_source.strip().upper()
        else:
            current_source = ""

        if normalized_source != current_source:
            self.reset_waiting_state()

    def show_txt_files(self, txt_files):
        self.catalog_table.clearContents()
        self.catalog_table.setRowCount(len(txt_files))

        for i, txt_file in enumerate(txt_files):
            set_table_text(self.catalog_table, i, 0, txt_file.file_name)
            set_table_text(self.catalog_table, i, 1, txt_file.get_directory_display())
            set_table_text(self.catalog_table, i, 2, txt_file.get_size_display())

    def show_selected_file_details(self):
        selected_rows = self.catalog_table.selectionModel().selectedRows()
        if len(selected_rows) == 0:
            self.clear_section3()
            return

        row = selected_rows[0].row()
        if row < 0 or row >= len(self.catalog_entries):
            self.clear_section3()
            return

        selected_file = self.catalog_entries[row]

        # --- Section 3: đọc thông tin chi tiết file TXT ---
        try:
            info = self.reader.read_txt_file_info(self.current_source, selected_file)
        except (FAT32ReaderError, Exception) as exc:
            self.detail_labels["name"].setText(selected_file.file_name)
            self.detail_labels["date_created"].setText("Error")
            self.detail_labels["time_created"].setText("Error")
            self.detail_labels["total_size"].setText(selected_file.get_size_display())
            self.process_table.clearContents()
            self.process_table.setRowCount(0)
            self.last_parsed_info = None
            self.run_scheduling_button.setEnabled(False)
            self.clear_section4()
            self.status_callback(f"Section 3 error: {exc}")
            QMessageBox.critical(self, "Unable to Read TXT File Details", str(exc))
            return

        self.last_parsed_info = info

        # hiển thị metadata
        self.detail_labels["name"].setText(info["file_name"])
        self.detail_labels["date_created"].setText(info["date_created"])
        self.detail_labels["time_created"].setText(info["time_created"])
        self.detail_labels["total_size"].setText(selected_file.get_size_display())

        # hiển thị bảng process
        processes = info["processes"]
        self.process_table.setRowCount(len(processes))
        for i, p in enumerate(processes):
            set_table_text(self.process_table, i, 0, p["process_id"])
            set_table_text(self.process_table, i, 1, str(p["arrival_time"]))
            set_table_text(self.process_table, i, 2, str(p["cpu_burst_time"]))
            set_table_text(self.process_table, i, 3, p["priority_queue_id"])
            set_table_text(self.process_table, i, 4, str(p["time_slice"]))
            set_table_text(self.process_table, i, 5, p["algorithm"])

        # bật nút Run Scheduling nếu có process
        self.run_scheduling_button.setEnabled(len(processes) > 0)
        self.clear_section4()
        self.status_callback(f"Loaded {len(processes)} processes from {info['file_name']}.")

    def clear_section3(self):
        for label in self.detail_labels.values():
            label.setText("-")
        self.process_table.clearContents()
        self.process_table.setRowCount(0)
        self.last_parsed_info = None
        self.run_scheduling_button.setEnabled(False)
        self.clear_section4()

    def clear_section4(self):
        self.gantt_table.clearContents()
        self.gantt_table.setRowCount(0)
        self.stats_table.clearContents()
        self.stats_table.setRowCount(0)
        self.avg_turnaround_label.setText("-")
        self.avg_waiting_label.setText("-")

    # --- Section 4: chạy scheduling và hiển thị kết quả ---

    def run_scheduling(self):
        if self.last_parsed_info is None:
            return

        queues = self.last_parsed_info["queues"]
        processes = self.last_parsed_info["processes"]

        try:
            result = self.scheduler.run(queues, processes)
        except Exception as exc:
            self.clear_section4()
            self.status_callback(f"Scheduling error: {exc}")
            QMessageBox.critical(self, "Scheduling Error", str(exc))
            return

        self.show_scheduling_result(result, processes)
        self.status_callback("Scheduling completed.")

    def show_scheduling_result(self, result, processes_info):
        # --- bảng Gantt chart ---
        self.gantt_table.setRowCount(len(result.slices))
        for i, s in enumerate(result.slices):
            set_table_text(self.gantt_table, i, 0, f"[{s.start_time} - {s.end_time}]")
            set_table_text(self.gantt_table, i, 1, s.queue_id)
            set_table_text(self.gantt_table, i, 2, s.process_id)

        # tạo lookup process theo pid
        proc_map = {}
        for p in processes_info:
            proc_map[p["process_id"]] = p

        # sắp xếp theo số thứ tự process (P1, P2, ...)
        sorted_pids = sorted(
            result.turnaround_times.keys(),
            key=lambda pid: int(pid[1:]),
        )

        # --- bảng thống kê ---
        self.stats_table.setRowCount(len(sorted_pids))
        total_turnaround = 0
        total_waiting = 0

        for i, pid in enumerate(sorted_pids):
            p = proc_map[pid]
            turnaround = result.turnaround_times[pid]
            waiting = result.waiting_times[pid]
            finish = p["arrival_time"] + turnaround

            set_table_text(self.stats_table, i, 0, pid)
            set_table_text(self.stats_table, i, 1, str(p["arrival_time"]))
            set_table_text(self.stats_table, i, 2, str(p["cpu_burst_time"]))
            set_table_text(self.stats_table, i, 3, str(finish))
            set_table_text(self.stats_table, i, 4, str(turnaround))
            set_table_text(self.stats_table, i, 5, str(waiting))

            total_turnaround += turnaround
            total_waiting += waiting

        # trung bình
        if sorted_pids:
            avg_turn = total_turnaround / len(sorted_pids)
            avg_wait = total_waiting / len(sorted_pids)
            self.avg_turnaround_label.setText(f"{avg_turn:.1f}")
            self.avg_waiting_label.setText(f"{avg_wait:.1f}")
        else:
            self.avg_turnaround_label.setText("-")
            self.avg_waiting_label.setText("-")


class MainWindow(QMainWindow):
    def __init__(self):
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

    def show_status_message(self, message):
        self.statusBar().showMessage(message, 5000)


def run():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("FAT32 Explorer")
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()
    return app.exec()
