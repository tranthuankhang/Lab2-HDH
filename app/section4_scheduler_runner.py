# ================================================================
#  Section 4 - Scheduler Runner
#  Lap lich da cap hang doi (Multi-Level Queue):
#    - Round Robin giua cac queue
#    - Moi queue dung 1 trong 2 thuat toan: SJF hoac SRTN
#  Logic tai su dung tu Lab1 (file models.py).
# ================================================================


# ----------------------------------------------------------------
#  CAC LOP DU LIEU DE GIAO TIEP VOI UI (giu nguyen interface)
# ----------------------------------------------------------------


class ProcessInfo:
    """Thong tin process dau vao (do UI truyen xuong)."""

    def __init__(self, process_id, arrival_time, cpu_burst_time,
                 priority_queue_id=None, time_slice=None):
        self.process_id = process_id
        self.arrival_time = arrival_time
        self.cpu_burst_time = cpu_burst_time
        self.priority_queue_id = priority_queue_id
        self.time_slice = time_slice


class ScheduledSlice:
    """Mot khoang thoi gian CPU chay 1 process (giong Gantt chart)."""

    def __init__(self, process_id, start_time, end_time, queue_id=""):
        self.process_id = process_id
        self.start_time = start_time
        self.end_time = end_time
        self.queue_id = queue_id


class SchedulingResult:
    """Ket qua lap lich, tra ve cho UI."""

    def __init__(self, algorithm_name):
        self.algorithm_name = algorithm_name
        self.slices = []            # list of ScheduledSlice
        self.turnaround_times = {}  # {process_id: int}
        self.waiting_times = {}     # {process_id: int}


class SchedulerError(Exception):
    """Loi khi du lieu dau vao khong hop le."""


# ----------------------------------------------------------------
#  CAC LOP NOI BO - MO PHONG LAB1 (Process, Queue, Sys)
# ----------------------------------------------------------------


class Process:
    """Mot process ben trong bo lap lich (giong class Process trong Lab1)."""

    def __init__(self, pid, arrival, burst, queue_id):
        self.pid = pid                  # vd: "P1"
        self.arrival = arrival          # thoi diem den
        self.burst = burst              # thoi gian CPU can ban dau
        self.remaining = burst          # thoi gian CPU con lai
        self.finish_time = 0            # thoi diem ket thuc
        self.queue_id = queue_id        # vd: "Q1"


class SchedulingQueue:
    """Mot hang doi priority (giong class Queue trong Lab1)."""

    def __init__(self, qid, time_slice, algorithm):
        self.qid = qid                  # vd: "Q1"
        self.time_slice = time_slice    # so don vi thoi gian toi da moi luot RR
        self.algorithm = algorithm      # "SJF" hoac "SRTN"
        self.processes = []             # danh sach Process trong queue

    def is_finished(self):
        """Queue da xong khi tat ca process khong con remaining."""
        for p in self.processes:
            if p.remaining > 0:
                return False
        return True

    def pick_shortest(self, current_time):
        """
        Chon process co remaining time ngan nhat da arrive.
        Uu tien: remaining ngan nhat -> arrival som nhat -> pid nho nhat.
        (Giong ham SJ trong Lab1)
        """
        # Loc ra cac process da arrive va con thoi gian chay
        available = []
        for p in self.processes:
            if p.arrival <= current_time and p.remaining > 0:
                available.append(p)

        if not available:
            return None

        # Sap xep theo 3 tieu chi
        available.sort(key=lambda p: (p.remaining, p.arrival, _pid_number(p.pid)))
        return available[0]


class SchedulingSystem:
    """
    He thong lap lich tong the (giong class Sys trong Lab1).
    Chua nhieu queue va CPU timeline.
    """

    def __init__(self):
        self.queues = []        # list of SchedulingQueue
        self.cpu = [None]       # timeline: moi phan tu = Process hoac "idle"
        self.queue_of_slot = [None]  # queue_id tuong ung voi tung phan tu trong cpu

    def add_queue(self, queue):
        self.queues.append(queue)

    def all_done(self):
        """Kiem tra tat ca process trong tat ca queue da xong chua."""
        for q in self.queues:
            if not q.is_finished():
                return False
        return True

    def run(self):
        """
        Vong lap chinh: Round Robin giua cac queue,
        moi queue chay trong time_slice cua no voi SJF hoac SRTN.
        Logic gan nhu giong het Lab1 Sys.Run().
        """
        t = 0

        while not self.all_done():
            check_idle = True  # neu khong queue nao chay duoc -> idle

            # Duyet tung queue theo thu tu Round Robin
            for cur_queue in self.queues:
                cur_process = None
                runtime = 0
                temp_cpu = []
                temp_queue = []

                # Chay trong khoang time_slice cua queue nay
                while runtime < cur_queue.time_slice:
                    # Chon process tuy theo thuat toan
                    if cur_queue.algorithm == "SJF":
                        # SJF non-preemptive: chi chon process moi
                        # khi chua co hoac process hien tai da xong
                        if cur_process is None or cur_process.remaining == 0:
                            cur_process = cur_queue.pick_shortest(t)
                    elif cur_queue.algorithm == "SRTN":
                        # SRTN preemptive: chon lai moi don vi thoi gian
                        cur_process = cur_queue.pick_shortest(t)

                    # Khong co process nao chay duoc -> thoat queue nay
                    if cur_process is None:
                        break

                    check_idle = False

                    # Chay process 1 don vi thoi gian
                    temp_cpu.append(cur_process)
                    temp_queue.append(cur_queue.qid)
                    cur_process.remaining -= 1
                    t += 1
                    runtime += 1

                    # Process vua chay xong -> ghi nhan finish_time
                    if cur_process.remaining == 0:
                        cur_process.finish_time = t

                # Noi ket qua cua queue nay vao timeline chung
                self.cpu += temp_cpu
                self.queue_of_slot += temp_queue

            # Neu khong queue nao chay duoc -> CPU nghi 1 don vi thoi gian
            if check_idle:
                self.cpu.append("idle")
                self.queue_of_slot.append("")
                t += 1

        # Xu ly phan tu dau (None) giong Lab1
        if len(self.cpu) > 1:
            self.cpu[0] = self.cpu[1]
            self.queue_of_slot[0] = self.queue_of_slot[1]
        else:
            self.cpu.pop(0)
            self.queue_of_slot.pop(0)


# ----------------------------------------------------------------
#  HAM HO TRO
# ----------------------------------------------------------------


def _pid_number(pid):
    """Lay phan so cua process_id, vd: 'P1' -> 1, 'P10' -> 10."""
    return int(pid[1:])


def _queue_number(qid):
    """Lay phan so cua queue_id, vd: 'Q1' -> 1."""
    return int(qid[1:])


# ----------------------------------------------------------------
#  LOP CHINH - SchedulingRunner (interface cho UI)
# ----------------------------------------------------------------


class SchedulingRunner:
    """Section 4: chay lap lich da cap hang doi cho UI."""

    def available_algorithms(self):
        return ("SJF", "SRTN")

    def run(self, queues_info, processes_info):
        """
        Chay lap lich va tra ve SchedulingResult.

        Tham so:
            queues_info:    list of dict
                [{"queue_id": "Q1", "time_slice": 8, "algorithm": "SRTN"}, ...]
            processes_info: list of dict
                [{"process_id": "P1", "arrival_time": 0, "cpu_burst_time": 12,
                  "priority_queue_id": "Q1"}, ...]

        Luong xu ly:
            Buoc 1: Tao SchedulingSystem va them cac Queue + Process vao.
            Buoc 2: Goi system.run() de chay thuat toan lap lich.
            Buoc 3: Tu cpu timeline -> gom nhom thanh cac ScheduledSlice.
            Buoc 4: Tu Process object -> tinh turnaround va waiting time.
            Buoc 5: Dong goi ket qua vao SchedulingResult va tra ve.
        """
        if not processes_info:
            raise SchedulerError("The process list is empty.")
        if not queues_info:
            raise SchedulerError("The queue list is empty.")

        # ===== Buoc 1: Xay dung he thong =====
        system = self._build_system(queues_info, processes_info)

        # ===== Buoc 2: Chay thuat toan lap lich =====
        system.run()

        # ===== Buoc 3 & 4 & 5: Dong goi ket qua =====
        result = SchedulingResult("Multi-Level Queue")
        result.slices = self._build_slices(system)
        self._fill_times(result, system)
        return result

    # ------------------------------------------------------------
    #  Buoc 1: Xay dung SchedulingSystem tu du lieu dau vao
    # ------------------------------------------------------------

    def _build_system(self, queues_info, processes_info):
        """Tao SchedulingSystem, them queue va process vao theo thu tu."""
        system = SchedulingSystem()

        # Sap xep queue theo thu tu Q1 < Q2 < Q3 ...
        sorted_queues = sorted(queues_info, key=lambda q: _queue_number(q["queue_id"]))

        # Tao SchedulingQueue va add vao system
        queue_map = {}  # queue_id -> SchedulingQueue
        for q in sorted_queues:
            sq = SchedulingQueue(q["queue_id"], q["time_slice"], q["algorithm"])
            system.add_queue(sq)
            queue_map[q["queue_id"]] = sq

        # Tao Process va add vao queue tuong ung
        for p in processes_info:
            proc = Process(
                pid=p["process_id"],
                arrival=p["arrival_time"],
                burst=p["cpu_burst_time"],
                queue_id=p["priority_queue_id"],
            )
            parent_queue = queue_map.get(p["priority_queue_id"])
            if parent_queue is not None:
                parent_queue.processes.append(proc)

        # Sap xep process trong moi queue theo pid
        for sq in system.queues:
            sq.processes.sort(key=lambda p: _pid_number(p.pid))

        return system

    # ------------------------------------------------------------
    #  Buoc 3: Gom nhom cpu timeline thanh cac ScheduledSlice
    # ------------------------------------------------------------

    def _build_slices(self, system):
        """
        Chuyen cpu timeline thanh danh sach ScheduledSlice.
        Gom nhom cac don vi thoi gian lien tiep co cung process
        thanh 1 slice [start_time - end_time].
        (Giong cach in Gantt chart trong Lab1 file_io.py)
        """
        slices = []
        cpu = system.cpu
        q_slot = system.queue_of_slot

        if not cpu:
            return slices

        # Ham nho de lay pid tu phan tu timeline (co the la Process hoac "idle")
        def pid_of(x):
            if x == "idle":
                return "idle"
            return x.pid

        current_pid = pid_of(cpu[0])
        current_qid = q_slot[0]
        start = 0

        for i in range(1, len(cpu)):
            next_pid = pid_of(cpu[i])
            if next_pid != current_pid:
                end = i - 1
                slices.append(ScheduledSlice(current_pid, start, end, current_qid))
                start = end
                current_pid = next_pid
                current_qid = q_slot[i]

        # Slice cuoi cung
        end = len(cpu) - 1
        slices.append(ScheduledSlice(current_pid, start, end, current_qid))

        return slices

    # ------------------------------------------------------------
    #  Buoc 4: Tinh turnaround va waiting time tu cac Process
    # ------------------------------------------------------------

    def _fill_times(self, result, system):
        """
        Tinh turnaround va waiting time cho tung process.
            turnaround = finish_time - arrival
            waiting    = turnaround  - burst
        """
        for q in system.queues:
            for p in q.processes:
                if p.finish_time > 0:
                    turnaround = p.finish_time - p.arrival
                    waiting = turnaround - p.burst
                    result.turnaround_times[p.pid] = turnaround
                    result.waiting_times[p.pid] = waiting
