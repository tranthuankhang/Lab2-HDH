# Lab 02 - FAT32 Explorer

Khung sườn Python + PySide6 cho đồ án Hệ điều hành.

Hiện tại đã làm xong:

- Chức năng 1: đọc `Boot Sector` và hiển thị ra giao diện dưới dạng bảng
- Khung sườn cho các chức năng còn lại: danh sách `*.txt`, chi tiết file, mô phỏng scheduling

## Cấu trúc thư mục

```text
Lab2/
|-- app/
|   |-- __init__.py
|   |-- fat32_reader.py
|   |-- models.py
|   |-- scheduler.py
|   `-- ui_main.py
|-- main.py
|-- requirements.txt
`-- README.md
```

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
- Hoặc bấm `Chọn file image...` để chọn file `.img`, `.bin`, `.ima`
- Bấm `Đọc Boot Sector`

Lưu ý:

- Khi đọc trực tiếp USB/ổ đĩa trên Windows, chương trình có thể cần quyền `Run as Administrator`
- `RDET sectors` trên FAT32 thường bằng `0`, đây là đặc điểm bình thường của FAT32

## Hướng mở rộng tiếp theo

- Duyệt toàn bộ thư mục theo cấu trúc FAT32 để lấy danh sách `*.txt`
- Parse nội dung file txt thành danh sách process
- Nối `scheduler.py` với giao diện để vẽ Gantt chart và tính waiting/turnaround time
