from pathlib import Path
from typing import List
import shutil
import time
import logging

class FileRenamer:
    @staticmethod
    def get_next_number(files: List[Path]) -> int:
        """
        현재 존재하는 파일들 중 가장 큰 숫자를 찾아 다음 번호를 반환합니다.

        Args:
            files (List[Path]): 검사할 파일 리스트

        Returns:
            int: 다음 사용할 번호
        """
        numbers = []
        for file in files:
            if file.stem.isdigit():
                numbers.append(int(file.stem))
        return max(numbers, default=0) + 1

    @staticmethod
    def rename_file(file_path: Path, new_number: int, max_retries: int = 3) -> Path:
        """
        파일의 이름을 새로운 번호로 변경합니다.

        Args:
            file_path (Path): 변경할 파일 경로
            new_number (int): 새로운 번호
            max_retries (int): 최대 재시도 횟수

        Returns:
            Path: 새로운 파일 경로
        """
        logger = logging.getLogger(__name__)
        new_name = f"{new_number}{file_path.suffix}"
        new_path = file_path.parent / new_name
        
        # 이미 존재하는 파일명 처리
        while new_path.exists():
            new_number += 1
            new_name = f"{new_number}{file_path.suffix}"
            new_path = file_path.parent / new_name

        for attempt in range(max_retries):
            try:
                # rename 대신 copy2 사용 후 원본 삭제
                shutil.copy2(file_path, new_path)
                try:
                    file_path.unlink()  # 원본 파일 삭제
                except Exception as e:
                    logger.warning(f"원본 파일 삭제 실패: {e}")
                return new_path
            except FileNotFoundError:
                logger.error(f"파일을 찾을 수 없음: {file_path}")
                raise
            except PermissionError:
                if attempt < max_retries - 1:
                    logger.warning(f"파일 접근 권한 오류, {attempt + 1}번째 재시도 중...")
                    time.sleep(1)  # 1초 대기 후 재시도
                    continue
                else:
                    logger.error(f"파일 접근 권한 오류가 지속됨: {file_path}")
                    raise
            except Exception as e:
                logger.error(f"파일 이름 변경 중 예상치 못한 오류: {e}")
                raise 