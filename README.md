# Lab 02 - FAT32 Explorer

Ứng dụng Python + PySide6 hỗ trợ đọc USB/phân vùng FAT32 cho bài lab Hệ điều hành.

Chương trình hiện có các chức năng chính:

- Section 1: đọc Boot Sector của FAT32, hiển thị các trường đang có trên giao diện như bytes/sector, sectors/cluster, Boot Sector region, số FAT, sectors/FAT, tổng số sector và lấy root directory start cluster để các section sau duyệt thư mục.
- Section 2: quét đệ quy tất cả file `*.txt` trên USB FAT32, bao gồm cả file trong thư mục con.
- Section 3: đọc thông tin chi tiết của file TXT được chọn: tên file, ngày/giờ tạo, kích thước và nội dung process theo format Lab1.
- Section 4: chạy mô phỏng lập lịch Multi-Level Queue, Round Robin giữa các queue; mỗi queue dùng `SJF` hoặc `SRTN`, sau đó hiển thị Gantt chart, turnaround time và waiting time.

## Cấu trúc thư mục

```text
Lab2/
|-- app/
|   |-- __init__.py
|   |-- drive_reader.py
|   |-- section1_boot_sector_reader.py
|   |-- section2_txt_scanner.py
|   |-- section3_txt_info_reader.py
|   |-- section4_scheduler_runner.py
|   `-- ui_main.py
|-- main.py
|-- requirements.txt
|-- .gitignore
`-- README.md
```

`BaoCao/` là thư mục báo cáo LaTeX/PDF cá nhân và đã được đưa vào `.gitignore`, nên sẽ không được commit lên git.

## Vai trò các file

- `main.py`: điểm chạy chính của ứng dụng.
- `app/ui_main.py`: giao diện PySide6 gồm tab Boot Sector và Text Files.
- `app/drive_reader.py`: mở, đọc và cache dữ liệu từ USB/phân vùng FAT32.
- `app/section1_boot_sector_reader.py`: đọc và parse Boot Sector.
- `app/section2_txt_scanner.py`: duyệt FAT/directory entry để tìm file `*.txt`.
- `app/section3_txt_info_reader.py`: đọc metadata và nội dung TXT, parse queue/process.
- `app/section4_scheduler_runner.py`: mô phỏng Multi-Level Queue Scheduler và tính kết quả.
- `requirements.txt`: danh sách thư viện cần cài. Chương trình chỉ cần cài trực tiếp `PySide6`; các dependency con của PySide6 sẽ được `pip` tự cài theo.

## Cài đặt và chạy

Nếu máy đã có Python, có thể cài thư viện và chạy trực tiếp:

```powershell
python -m pip install -r requirements.txt
python main.py
```

Nếu muốn tách môi trường cài đặt riêng:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Cách dùng

1. Cắm USB/phân vùng FAT32 vào máy.
2. Mở chương trình bằng `python main.py`.
3. Ở tab `Boot Sector`, nhập ký tự ổ đĩa, ví dụ `E:`, rồi bấm `Read`.
4. Sau khi đọc Boot Sector thành công, tab `Text Files` sẽ tự động quét các file `.txt`.
5. Chọn một file TXT để xem metadata và bảng process.
6. Bấm `Run Scheduling` để xem CPU Scheduling Diagram và bảng thống kê.

Lưu ý: trên Windows, việc đọc trực tiếp `\\.\E:` có thể cần chạy terminal/IDE bằng quyền Administrator.

## Đóng gói nộp bài

Theo yêu cầu lab, nộp 2 file riêng, không zip chung báo cáo với source code:

- `MSSV1_MSSV2.zip`: chỉ chứa source code chương trình, gồm `app/`, `main.py`, `requirements.txt` và `README.md`.
- `MSSV1_MSSV2.pdf`: file báo cáo PDF riêng.

Không cần đưa vào file zip source các thư mục/file local như `.git/`, `__pycache__/`, `BaoCao/`, `*.log` hoặc các file build trung gian của LaTeX.

## Format file TXT đầu vào

Nội dung file TXT được parse theo format Lab1:

```text
<so_luong_queue>
Q<id> <time_slice> <algorithm>
...
P<id> <arrival_time> <cpu_burst_time> Q<queue_id>
...
```

Ví dụ:

```text
3
Q1 8 SRTN
Q2 5 SJF
Q3 3 SJF
P1 0 12 Q1
P2 1 6 Q1
P3 2 8 Q2
```

`algorithm` hiện hỗ trợ:

- `SJF`
- `SRTN`

## Kiểm tra nhanh

Có thể kiểm tra lỗi cú pháp bằng lệnh:

```powershell
python -m compileall main.py app
```
