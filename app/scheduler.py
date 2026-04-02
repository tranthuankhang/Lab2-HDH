from __future__ import annotations

from app.models import ProcessInfo, SchedulingResult


class SchedulerError(Exception):
    """Raised when scheduling input is invalid."""


class SchedulerEngine:
    """Placeholder engine for Project 01 scheduling algorithms."""

    @staticmethod
    def available_algorithms() -> tuple[str, ...]:
        return ("FCFS", "SJF", "Priority", "Round Robin")

    def run(self, processes: list[ProcessInfo], algorithm_name: str) -> SchedulingResult:
        if not processes:
            raise SchedulerError("The process list is empty.")
        if algorithm_name not in self.available_algorithms():
            raise SchedulerError(f"Unsupported scheduling algorithm: {algorithm_name}")

        raise NotImplementedError(
            "The scheduling engine will be connected after the TXT parsing workflow is completed."
        )
