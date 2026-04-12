# ================================================================
#  Section 3 - Txt File Info Reader
#  Doc thong tin chi tiet cua 1 file TXT tren USB FAT32:
#    - Ten file, ngay gio tao, kich thuoc
#    - Parse noi dung file theo format Lab1 (queue + process)
#  Class TxtFileInfoReader ke thua TxtFileScanner (section 2)
#  de tai su dung cac ham doc FAT, cluster, directory entry.
# ================================================================

from app.section2_txt_scanner import TxtFileScanner


class TxtFileInfoReader(TxtFileScanner):
    """Section 3: doc thong tin chi tiet file TXT tu USB FAT32."""

    # ------------------------------------------------------------
    #  HAM CHINH - giao tiep voi UI
    # ------------------------------------------------------------

    def read_txt_file_info(self, source, selected_file):
        """
        Doc toan bo thong tin cua file TXT duoc chon.

        Tham so:
            source:        chu cai o dia, vd "E:"
            selected_file: doi tuong TxtFileEntry (tu section 2)

        Tra ve dict gom:
            file_name, date_created, time_created, total_size, queues, processes
        """
        # --- Kiem tra dau vao ---
        if not source.strip():
            raise ValueError("A FAT32 USB drive letter is required before reading TXT file details.")
        if not selected_file.file_name:
            raise ValueError("A TXT file must be selected before reading its details.")

        # --- Chuan bi: lay boot sector info va FAT table ---
        boot_info, fat_table = self._prepare_fat_access(source)

        # --- Lay ngay gio tao tu directory entry da luu trong TxtFileEntry ---
        if selected_file.raw_entry is not None:
            date_created, time_created = self._decode_datetime(selected_file.raw_entry)
        else:
            date_created, time_created = "N/A", "N/A"

        # --- Doc noi dung file tu cluster chain ---
        raw_bytes = self._read_file_content(source, boot_info, fat_table, selected_file)
        text = raw_bytes.decode("utf-8", errors="ignore")

        # --- Parse noi dung file theo format Lab1 ---
        queues, processes = self._parse_scheduling_text(text)

        # --- Dong goi ket qua ---
        return {
            "file_name": selected_file.file_name,
            "date_created": date_created,
            "time_created": time_created,
            "total_size": selected_file.file_size,
            "queues": queues,
            "processes": processes,
        }

    # ------------------------------------------------------------
    #  CHUAN BI: lay boot sector info va fat table tu source
    # ------------------------------------------------------------

    def _prepare_fat_access(self, source):
        """Lay Boot Sector info va FAT table de su dung cho cac buoc sau."""
        boot_info = self.drive_reader.get_boot_sector_info(source)
        if boot_info is None:
            boot_info = self.boot_sector_reader.read_boot_sector(source)
        fat_table = self.drive_reader.get_fat_table(source, boot_info)
        return boot_info, fat_table

    # ------------------------------------------------------------
    #  DOC NOI DUNG FILE THEO FAT CHAIN
    # ------------------------------------------------------------

    def _read_file_content(self, source, boot_info, fat_table, selected_file):
        """
        Doc toan bo noi dung file bang cach di theo FAT chain.

        Cach hoat dong:
            1. Bat dau tu starting_cluster cua file.
            2. Doc du lieu cua cluster do, noi vao buffer.
            3. Tra bang FAT de tim cluster ke tiep.
            4. Lap lai cho den khi gap ket thuc chain.
            5. Cat buffer theo dung kich thuoc file thuc te.
        """
        data = bytearray()
        cluster = selected_file.starting_cluster

        # File rong (cluster < 2) -> tra ve bytes rong
        if cluster < 2:
            return bytes(data)

        visited = set()  # tap cluster da doc, de tranh vong lap vo tan

        while True:
            # Neu cluster nay da doc roi -> co loi vong lap, thoat
            if cluster in visited:
                break
            visited.add(cluster)

            # Doc du lieu cua cluster hien tai va noi vao buffer
            self.drive_reader.validate_cluster_number(cluster, boot_info)
            chunk = self.drive_reader.read_cluster(source, boot_info, cluster)
            data.extend(chunk)

            # Tra bang FAT de tim cluster ke tiep trong chain
            next_cluster = self._read_fat_entry(fat_table, cluster)

            # Het chain hoac cluster khong hop le -> thoat
            if next_cluster >= 0x0FFFFFF8 or next_cluster < 2:
                break

            cluster = next_cluster

        # Cat du lieu dung bang kich thuoc file (vi cluster cuoi co the du byte)
        return bytes(data[: selected_file.file_size])

    # ------------------------------------------------------------
    #  GIAI MA NGAY GIO TAO TU DIRECTORY ENTRY
    # ------------------------------------------------------------

    def _decode_datetime(self, entry):
        """
        Giai ma ngay/gio tao tu 32-byte directory entry.

        Cau truc 3 byte creation time (offset 13-15, little-endian):
            Bits 23-19: Gio (0-23)
            Bits 18-13: Phut (0-59)
            Bits 12-7:  Giay (0-59)

        Cau truc 2 byte creation date (offset 16-17, little-endian):
            Bits 15-9: Nam - 1980 (0-127 -> 1980-2107)
            Bits 8-5:  Thang (1-12)
            Bits 4-0:  Ngay (1-31)
        """
        raw_time = int.from_bytes(entry[13:16], "little")
        raw_date = int.from_bytes(entry[16:18], "little")

        # Tach tung truong bang phep dich bit va mask
        hour = (raw_time >> 19) & 0x1F
        minute = (raw_time >> 13) & 0x3F
        second = (raw_time >> 7) & 0x3F

        year = ((raw_date >> 9) & 0x7F) + 1980
        month = (raw_date >> 5) & 0x0F
        day = raw_date & 0x1F

        # Dinh dang thanh chuoi de hien thi
        date_str = f"{day:02d}/{month:02d}/{year}"
        time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
        return date_str, time_str

    # ------------------------------------------------------------
    #  PARSE NOI DUNG FILE TXT THEO FORMAT LAB1
    # ------------------------------------------------------------

    def _parse_scheduling_text(self, text):
        """
        Parse noi dung file TXT theo format cua Lab1.

        Format file:
            Dong 1:           so luong queue (N)
            N dong tiep theo: "Q<id> <time_slice> <algorithm>"
                              vd: "Q1 8 SRTN"
            Cac dong con lai: "P<id> <arrival> <burst> Q<queue_id>"
                              vd: "P1 0 12 Q1"

        Vi du noi dung file:
            3
            Q1 8 SRTN
            Q2 5 SJF
            Q3 3 SJF
            P1 0 12 Q1
            P2 1 6  Q1
            P3 2 8  Q2

        Tra ve 2 danh sach (queues, processes), moi phan tu la dict.
        """
        # Tach thanh cac dong, bo dong trong dau/cuoi
        lines = text.strip().splitlines()
        if not lines:
            return [], []

        queues = []
        processes = []
        idx = 0

        # --- Buoc 1: dong dau tien la so luong queue ---
        num_queues = int(lines[idx].strip())
        idx += 1

        # --- Buoc 2: doc N dong thong tin queue ---
        for _ in range(num_queues):
            if idx >= len(lines):
                break
            parts = lines[idx].split()
            # parts[0] = "Q1", parts[1] = "8", parts[2] = "SRTN"
            queues.append({
                "queue_id": parts[0],
                "time_slice": int(parts[1]),
                "algorithm": parts[2],
            })
            idx += 1

        # Tao dict tra cuu nhanh thong tin queue theo queue_id
        queue_map = {q["queue_id"]: q for q in queues}

        # --- Buoc 3: doc cac dong con lai (thong tin process) ---
        while idx < len(lines):
            line = lines[idx].strip()
            idx += 1
            if not line:
                continue  # bo qua dong trong

            parts = line.split()
            if len(parts) < 4:
                continue  # dong khong du truong -> bo qua

            # parts[0]="P1", parts[1]="0", parts[2]="12", parts[3]="Q1"
            qid = parts[3]
            q_info = queue_map.get(qid, {})

            processes.append({
                "process_id": parts[0],
                "arrival_time": int(parts[1]),
                "cpu_burst_time": int(parts[2]),
                "priority_queue_id": qid,
                # Them time_slice va algorithm tu queue tuong ung
                # de UI co the hien thi trong bang process.
                "time_slice": q_info.get("time_slice", 0),
                "algorithm": q_info.get("algorithm", ""),
            })

        return queues, processes
