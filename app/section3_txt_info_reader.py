from app.section2_txt_scanner import TxtFileScanner


class TxtFileInfoReader(TxtFileScanner):
    """Section 3: doc thong tin chi tiet file TXT tu USB FAT32."""

    def read_txt_file_info(self, source, selected_file):
        """
        Doc thong tin chi tiet cua file TXT duoc chon.

        Tra ve dict gom:
          file_name, date_created, time_created, total_size, queues, processes
        """
        if not source.strip():
            raise ValueError("A FAT32 USB drive letter is required before reading TXT file details.")
        if not selected_file.file_name:
            raise ValueError("A TXT file must be selected before reading its details.")

        # Lay thong tin boot sector va layout
        boot_info = self.drive_reader.get_boot_sector_info(source)
        if boot_info is None:
            boot_info = self.boot_sector_reader.read_boot_sector(source)
        layout = self.drive_reader.build_layout(source, boot_info)
        fat_table = self.drive_reader.get_fat_table(source, layout)

        # Tim ngay gio tao tu directory entry
        date_created, time_created = self._find_creation_datetime(
            source, layout, fat_table, selected_file
        )

        # Doc noi dung file tu cluster chain
        raw_bytes = self._read_file_content(source, layout, fat_table, selected_file)
        text = raw_bytes.decode("utf-8", errors="ignore")

        # Parse noi dung file thanh queue va process
        queues, processes = self._parse_scheduling_text(text)

        return {
            "file_name": selected_file.file_name,
            "date_created": date_created,
            "time_created": time_created,
            "total_size": selected_file.file_size,
            "queues": queues,
            "processes": processes,
        }

    # ----------------------------------------------------------------
    #  Doc noi dung file theo FAT chain
    # ----------------------------------------------------------------

    def _read_file_content(self, source, layout, fat_table, selected_file):
        """Doc toan bo noi dung file bang cach di theo FAT chain."""
        data = bytearray()
        cluster = selected_file.starting_cluster

        # File rong (cluster < 2) -> tra ve bytes rong
        if cluster < 2:
            return bytes(data)

        visited = set()
        while True:
            if cluster in visited:
                break  # tranh vong lap
            visited.add(cluster)

            self.drive_reader.validate_cluster_number(cluster, layout)
            chunk = self.drive_reader.read_cluster(source, layout, cluster)
            data.extend(chunk)

            # Doc cluster tiep theo trong bang FAT
            next_cluster = self._read_fat_entry(fat_table, cluster)
            if next_cluster >= 0x0FFFFFF8 or next_cluster < 2:
                break  # het chain hoac cluster khong hop le
            cluster = next_cluster

        # Cat du lieu dung bang kich thuoc file thuc te
        return bytes(data[: selected_file.file_size])

    # ----------------------------------------------------------------
    #  Tim ngay gio tao tu directory entry
    # ----------------------------------------------------------------

    def _find_creation_datetime(self, source, layout, fat_table, selected_file):
        """Tim directory entry cua file de lay ngay va gio tao."""
        # Bat dau tu thu muc goc (RDET)
        dir_cluster = layout.RDET_start_cluster

        # Neu file nam trong thu muc con, di theo duong dan
        path = selected_file.directory_path.strip("/")
        if path:
            for folder_name in path.split("/"):
                dir_cluster = self._find_subdir_cluster(
                    source, layout, fat_table, dir_cluster, folder_name
                )
                if dir_cluster is None:
                    return "N/A", "N/A"

        # Tim entry 32-byte cua file trong thu muc hien tai
        entry = self._find_file_entry(
            source, layout, fat_table, dir_cluster, selected_file
        )
        if entry is None:
            return "N/A", "N/A"

        return self._decode_datetime(entry)

    def _find_subdir_cluster(self, source, layout, fat_table, dir_cluster, folder_name):
        """Tim cluster bat dau cua thu muc con co ten = folder_name."""
        cur = dir_cluster
        lfn_parts = []
        visited = set()

        while True:
            if cur in visited:
                return None
            visited.add(cur)
            self.drive_reader.validate_cluster_number(cur, layout)
            data = self.drive_reader.read_cluster(source, layout, cur)

            for off in range(0, len(data), 32):
                entry = data[off : off + 32]
                if len(entry) < 32:
                    return None
                if entry[0] == 0x00:
                    return None
                if entry[0] == 0xE5:
                    lfn_parts = []
                    continue

                attr = entry[11]
                if attr == 0x0F:  # LFN entry
                    lfn_parts.insert(0, self._get_lfn_text(entry))
                    continue

                # Lay ten file/folder
                if lfn_parts:
                    name = "".join(lfn_parts).strip()
                else:
                    name = self._get_short_name(entry)
                lfn_parts = []

                # Bo qua entry khong phai thu muc
                if not name or not (attr & 0x10) or name in (".", ".."):
                    continue

                if name.lower() == folder_name.lower():
                    return self._get_start_cluster(entry)

            # Chuyen sang cluster tiep theo cua thu muc
            nxt = self._read_fat_entry(fat_table, cur)
            if nxt >= 0x0FFFFFF8 or nxt < 2:
                return None
            cur = nxt

    def _find_file_entry(self, source, layout, fat_table, dir_cluster, selected_file):
        """Tim 32-byte directory entry cua file trong thu muc."""
        cur = dir_cluster
        lfn_parts = []
        visited = set()

        while True:
            if cur in visited:
                return None
            visited.add(cur)
            self.drive_reader.validate_cluster_number(cur, layout)
            data = self.drive_reader.read_cluster(source, layout, cur)

            for off in range(0, len(data), 32):
                entry = data[off : off + 32]
                if len(entry) < 32:
                    return None
                if entry[0] == 0x00:
                    return None
                if entry[0] == 0xE5:
                    lfn_parts = []
                    continue

                attr = entry[11]
                if attr == 0x0F:  # LFN entry
                    lfn_parts.insert(0, self._get_lfn_text(entry))
                    continue

                if lfn_parts:
                    name = "".join(lfn_parts).strip()
                else:
                    name = self._get_short_name(entry)
                lfn_parts = []

                if not name:
                    continue

                # So sanh starting_cluster va ten file de tim dung entry
                start = self._get_start_cluster(entry)
                if (start == selected_file.starting_cluster
                        and name.lower() == selected_file.file_name.lower()):
                    return entry

            nxt = self._read_fat_entry(fat_table, cur)
            if nxt >= 0x0FFFFFF8 or nxt < 2:
                return None
            cur = nxt

    def _decode_datetime(self, entry):
        """
        Giai ma ngay/gio tao tu directory entry (32 bytes).

        Offset 14-15: Creation time (2 bytes, little-endian)
            Bits 15-11: Gio (0-23)
            Bits 10-5:  Phut (0-59)
            Bits 4-0:   Giay / 2 (0-29 => 0-58 giay)

        Offset 16-17: Creation date (2 bytes, little-endian)
            Bits 15-9: Nam - 1980 (0-127 => 1980-2107)
            Bits 8-5:  Thang (1-12)
            Bits 4-0:  Ngay (1-31)
        """
        raw_time = int.from_bytes(entry[14:16], "little")
        raw_date = int.from_bytes(entry[16:18], "little")

        hour = (raw_time >> 11) & 0x1F
        minute = (raw_time >> 5) & 0x3F
        second = (raw_time & 0x1F) * 2

        year = ((raw_date >> 9) & 0x7F) + 1980
        month = (raw_date >> 5) & 0x0F
        day = raw_date & 0x1F

        date_str = f"{day:02d}/{month:02d}/{year}"
        time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
        return date_str, time_str

    # ----------------------------------------------------------------
    #  Parse noi dung file TXT theo format Lab1
    # ----------------------------------------------------------------

    def _parse_scheduling_text(self, text):
        """
        Parse noi dung file TXT theo format cua Lab1.

        Dong 1:           so luong queue (N)
        N dong tiep theo: Q<id> <time_slice> <algorithm>
        Cac dong con lai: P<id> <arrival> <burst> Q<queue_id>

        Tra ve (queues, processes) voi moi phan tu la dict.
        """
        lines = text.strip().splitlines()
        if not lines:
            return [], []

        queues = []
        processes = []
        idx = 0

        # Dong dau tien: so luong queue
        num_queues = int(lines[idx].strip())
        idx += 1

        # Doc thong tin tung queue
        for _ in range(num_queues):
            if idx >= len(lines):
                break
            parts = lines[idx].split()
            # VD: parts = ["Q1", "8", "SRTN"]
            queues.append({
                "queue_id": parts[0],
                "time_slice": int(parts[1]),
                "algorithm": parts[2],
            })
            idx += 1

        # Tao dict de tra cuu nhanh thong tin queue theo queue_id
        queue_map = {q["queue_id"]: q for q in queues}

        # Doc thong tin tung process
        while idx < len(lines):
            line = lines[idx].strip()
            idx += 1
            if not line:
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            # VD: parts = ["P1", "0", "12", "Q1"]
            qid = parts[3]
            q_info = queue_map.get(qid, {})

            processes.append({
                "process_id": parts[0],
                "arrival_time": int(parts[1]),
                "cpu_burst_time": int(parts[2]),
                "priority_queue_id": qid,
                "time_slice": q_info.get("time_slice", 0),
                "algorithm": q_info.get("algorithm", ""),
            })

        return queues, processes
