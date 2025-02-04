from dataclasses import dataclass
from threading import Lock
from typing import Optional

@dataclass
class ProgressInfo:
    total: int = 0
    current: int = 0
    percentage: float = 0.0
    status: str = ""

class ProgressTracker:
    def __init__(self, total_items: int):
        self._lock = Lock()
        self._total = total_items
        self._current = 0
        self._status = ""

    def update(self, increment: int = 1, status: Optional[str] = None) -> None:
        """
        진행 상황을 업데이트합니다.

        Args:
            increment (int): 증가시킬 값
            status (Optional[str]): 현재 상태 메시지
        """
        with self._lock:
            self._current += increment
            if status:
                self._status = status

    def get_progress(self) -> ProgressInfo:
        """
        현재 진행 상황 정보를 반환합니다.

        Returns:
            ProgressInfo: 진행 상황 정보
        """
        with self._lock:
            percentage = (self._current / self._total * 100) if self._total > 0 else 0
            return ProgressInfo(
                total=self._total,
                current=self._current,
                percentage=percentage,
                status=self._status
            ) 