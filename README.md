# Lab 02 - FAT32 Explorer

Khung sườn Python + PySide6 cho đồ án Hệ điều hành.

Hiện tại đã làm xong:

- Chức năng 1: đọc `Boot Sector` và hiển thị ra giao diện dưới dạng bảng
- Chức năng 2: liệt kê tất cả file `*.txt` trên USB FAT32, kể cả trong thư mục con
- Đã tách mã nguồn theo 4 phần của đề bài: Boot Sector, TXT scan, TXT info, scheduling
- Khung sườn cho các chức năng còn lại: chi tiết file, mô phỏng scheduling

## Cấu trúc thư mục

```text
Lab2/
|-- app/
|   |-- __init__.py
|   |-- section1_boot_sector_reader.py
|   |-- section2_txt_scanner.py
|   |-- section3_txt_info_reader.py
|   |-- section4_scheduler_runner.py
|   `-- ui_main.py
|-- main.py
|-- requirements.txt
`-- README.md
```

Ghi chú:

- `section1_boot_sector_reader.py`: phần 1 của đề, đọc và phân tích Boot Sector
- `section2_txt_scanner.py`: phần 2 của đề, dò tất cả file `*.txt`
- `section3_txt_info_reader.py`: khung sườn phần 3, chưa triển khai logic
- `section4_scheduler_runner.py`: khung sườn phần 4, chưa triển khai logic

## Cách chạy chính (không cần venv)

Nếu máy đã có Python, có thể cài thư viện và chạy trực tiếp:

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Cách chạy tùy chọn (dùng venv)

Nếu muốn tách môi trường cài đặt riêng cho bài lab, có thể dùng `venv`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Cách dùng chức năng Boot Sector

- Nhập ký tự ổ đĩa FAT32, ví dụ: `E:`
- Bấm `Đọc Boot Sector`

Lưu ý:

- Khi đọc trực tiếp USB/ổ đĩa trên Windows, chương trình có thể cần quyền `Run as Administrator`
- `RDET sectors` trên FAT32 thường bằng `0`, đây là đặc điểm bình thường của FAT32

## Hướng mở rộng tiếp theo

- Parse nội dung file txt thành danh sách process
- Nối `section4_scheduler_runner.py` với giao diện để vẽ Gantt chart và tính waiting/turnaround time
