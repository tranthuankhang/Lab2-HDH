class ProcessInfo:
    def __init__(
        self,
        process_id: str,
        arrival_time: int,
        cpu_burst_time: int,
        priority_queue_id: int | None = None,
        time_slice: int | None = None,
    ) -> None:
        self.process_id = process_id
        self.arrival_time = arrival_time
        self.cpu_burst_time = cpu_burst_time
        self.priority_queue_id = priority_queue_id
        self.time_slice = time_slice


class ScheduledSlice:
    def __init__(self, process_id: str, start_time: int, end_time: int,
                 queue_id: str = "") -> None:
        self.process_id = process_id
        self.start_time = start_time
        self.end_time = end_time
        self.queue_id = queue_id


class SchedulingResult:
    def __init__(self, algorithm_name: str) -> None:
        self.algorithm_name = algorithm_name
        self.slices = []
        self.turnaround_times = {}
        self.waiting_times = {}


class SchedulerError(Exception):
    """Raised when scheduling input is invalid."""


class SchedulingRunner:
    """Section 4: chay lap lich da cap hang doi (Multi-Level Queue)."""

    @staticmethod
    def available_algorithms() -> tuple[str, ...]:
        return ("SJF", "SRTN")

    def run(self, queues_info, processes_info) -> SchedulingResult:
        """
        Chay lap lich da cap hang doi voi Round Robin giua cac queue.
        Moi queue dung SJF (non-preemptive) hoac SRTN (preemptive).

        Logic tai su dung tu Lab1 (models.py - Sys.Run):
          - Duyet cac queue theo thu tu Round Robin
          - Moi queue chay trong khoang time_slice cua no
          - Trong moi queue, chon process theo thuat toan SJF hoac SRTN
          - Lap lai cho den khi tat ca process hoan thanh

        Tham so:
            queues_info:    [{"queue_id": "Q1", "time_slice": 8, "algorithm": "SRTN"}, ...]
            processes_info: [{"process_id": "P1", "arrival_time": 0,
                              "cpu_burst_time": 12, "priority_queue_id": "Q1"}, ...]

        Tra ve: SchedulingResult (gom slices, turnaround_times, waiting_times)
        """
        if not processes_info:
            raise SchedulerError("The process list is empty.")
        if not queues_info:
            raise SchedulerError("The queue list is empty.")

        # ============================================================
        #  Buoc 1: Chuan bi du lieu
        # ============================================================

        # Sap xep queue theo so thu tu (Q1 < Q2 < Q3)
        queues = sorted(queues_info, key=lambda q: int(q["queue_id"][1:]))

        # Dict luu trang thai cua moi process
        remaining = {}    # process_id -> thoi gian CPU con lai
        finish_time = {}  # process_id -> thoi diem ket thuc
        arrival = {}      # process_id -> thoi diem den
        burst = {}        # process_id -> thoi gian CPU ban dau

        # Nhom process vao queue tuong ung
        queue_processes = {}
        for q in queues:
            queue_processes[q["queue_id"]] = []

        for p in processes_info:
            pid = p["process_id"]
            remaining[pid] = p["cpu_burst_time"]
            arrival[pid] = p["arrival_time"]
            burst[pid] = p["cpu_burst_time"]
            qid = p["priority_queue_id"]
            if qid in queue_processes:
                queue_processes[qid].append(p)

        # Sap xep process trong moi queue theo process_id
        for qid in queue_processes:
            queue_processes[qid].sort(key=lambda p: int(p["process_id"][1:]))

        # ============================================================
        #  Buoc 2: Chay lap lich (giong Lab1 Sys.Run)
        # ============================================================

        # Moi phan tu tuong ung 1 don vi thoi gian CPU
        cpu_timeline = [None]      # process_id hoac "idle"
        queue_timeline = [None]    # queue_id tuong ung
        t = 0                      # thoi gian hien tai

        def all_done():
            """Kiem tra tat ca process da chay xong chua."""
            for pid in remaining:
                if remaining[pid] > 0:
                    return False
            return True

        def pick_shortest(qid, current_time):
            """
            Chon process co remaining time nho nhat da arrive.
            Uu tien: remaining ngan nhat -> arrival som nhat -> process_id nho nhat.
            (Giong ham SJ trong Lab1 models.py)
            """
            candidates = []
            for p in queue_processes[qid]:
                pid = p["process_id"]
                if arrival[pid] <= current_time and remaining[pid] > 0:
                    candidates.append(p)
            if not candidates:
                return None
            # Sap xep theo 3 tieu chi
            candidates.sort(key=lambda p: (
                remaining[p["process_id"]],
                p["arrival_time"],
                int(p["process_id"][1:]),
            ))
            return candidates[0]

        # Vong lap chinh: Round Robin giua cac queue
        while not all_done():
            check_idle = True  # danh dau co queue nao chay duoc khong

            for q in queues:
                qid = q["queue_id"]
                time_slice = q["time_slice"]
                algorithm = q["algorithm"]

                cur_process = None  # process dang chay (dung cho SJF non-preemptive)
                runtime = 0         # so don vi thoi gian da chay trong queue nay
                temp_cpu = []       # danh sach process chay trong luot nay
                temp_queue = []     # danh sach queue tuong ung

                while runtime < time_slice:
                    # Chon process tuy theo thuat toan cua queue
                    if algorithm == "SJF":
                        # SJF (non-preemptive): chi chon process moi
                        # khi chua co process hoac process hien tai da xong
                        if cur_process is None or remaining[cur_process["process_id"]] == 0:
                            cur_process = pick_shortest(qid, t)
                    elif algorithm == "SRTN":
                        # SRTN (preemptive): chon lai moi don vi thoi gian
                        cur_process = pick_shortest(qid, t)

                    # Khong co process nao chay duoc -> thoat khoi queue nay
                    if cur_process is None:
                        break

                    check_idle = False
                    pid = cur_process["process_id"]
                    temp_cpu.append(pid)
                    temp_queue.append(qid)

                    remaining[pid] -= 1
                    t += 1
                    runtime += 1

                    # Process vua chay xong -> ghi nhan thoi diem ket thuc
                    if remaining[pid] == 0:
                        finish_time[pid] = t

                cpu_timeline += temp_cpu
                queue_timeline += temp_queue

            # Neu khong queue nao chay duoc -> CPU nghi (idle) 1 don vi
            if check_idle:
                cpu_timeline.append("idle")
                queue_timeline.append("")
                t += 1

        # Thay the phan tu dau (None) giong Lab1
        if len(cpu_timeline) > 1:
            cpu_timeline[0] = cpu_timeline[1]
            queue_timeline[0] = queue_timeline[1]
        else:
            cpu_timeline.pop(0)
            queue_timeline.pop(0)

        # ============================================================
        #  Buoc 3: Chuyen timeline thanh danh sach ScheduledSlice
        # ============================================================
        #  Gom nhom cac don vi thoi gian lien tiep co cung process
        #  thanh 1 slice [start_time - end_time].
        #  (Giong cach in Gantt chart trong Lab1 file_io.py)

        result = SchedulingResult("Multi-Level Queue")

        if not cpu_timeline:
            return result

        current_pid = cpu_timeline[0]
        current_qid = queue_timeline[0]
        start = 0

        for i in range(1, len(cpu_timeline)):
            if cpu_timeline[i] != current_pid:
                end = i - 1
                result.slices.append(
                    ScheduledSlice(current_pid, start, end, current_qid)
                )
                start = end
                current_pid = cpu_timeline[i]
                current_qid = queue_timeline[i]

        # Slice cuoi cung
        end = len(cpu_timeline) - 1
        result.slices.append(
            ScheduledSlice(current_pid, start, end, current_qid)
        )

        # ============================================================
        #  Buoc 4: Tinh turnaround time va waiting time
        # ============================================================
        #  turnaround = finish_time - arrival_time
        #  waiting    = turnaround  - burst_time

        for p in processes_info:
            pid = p["process_id"]
            if pid in finish_time:
                turnaround = finish_time[pid] - arrival[pid]
                waiting = turnaround - burst[pid]
                result.turnaround_times[pid] = turnaround
                result.waiting_times[pid] = waiting

        return result
