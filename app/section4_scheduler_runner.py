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
    def __init__(self, process_id: str, start_time: int, end_time: int) -> None:
        self.process_id = process_id
        self.start_time = start_time
        self.end_time = end_time


class SchedulingResult:
    def __init__(self, algorithm_name: str) -> None:
        self.algorithm_name = algorithm_name
        self.slices = []
        self.turnaround_times = {}
        self.waiting_times = {}


class SchedulerError(Exception):
    """Raised when scheduling input is invalid."""


class SchedulingRunner:
    """Placeholder for Section 4: run the selected scheduling algorithm and build results."""

    @staticmethod
    def available_algorithms() -> tuple[str, ...]:
        return ("FCFS", "SJF", "Priority", "Round Robin")

    def run(self, processes: list[ProcessInfo], algorithm_name: str) -> SchedulingResult:
        if not processes:
            raise SchedulerError("The process list is empty.")
        if algorithm_name not in self.available_algorithms():
            raise SchedulerError(f"Unsupported scheduling algorithm: {algorithm_name}")

        raise NotImplementedError(
            "Section 4 is reserved for executing the scheduling algorithm and producing the final output."
        )
