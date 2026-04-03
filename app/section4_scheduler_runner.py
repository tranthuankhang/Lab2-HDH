from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProcessInfo:
    process_id: str
    arrival_time: int
    cpu_burst_time: int
    priority_queue_id: int | None = None
    time_slice: int | None = None


@dataclass(slots=True)
class ScheduledSlice:
    process_id: str
    start_time: int
    end_time: int


@dataclass(slots=True)
class SchedulingResult:
    algorithm_name: str
    slices: list[ScheduledSlice] = field(default_factory=list)
    turnaround_times: dict[str, int] = field(default_factory=dict)
    waiting_times: dict[str, int] = field(default_factory=dict)


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
