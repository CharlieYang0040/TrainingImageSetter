# file_renamer.py

from pathlib import Path
from typing import List, Set
import shutil
import time
import logging

class FileRenamer:
    @staticmethod
    def get_used_numbers(directory: Path) -> Set[int]:
        """
        디렉토리에서 현재 사용 중인 모든 번호를 수집합니다.
        
        Args:
            directory (Path): 검사할 디렉토리
            
        Returns:
            Set[int]: 사용 중인 번호들의 집합
        """
        used_numbers = set()
        for file in directory.iterdir():
            if file.is_file() and file.stem.isdigit():
                used_numbers.add(int(file.stem))
        return used_numbers

    @staticmethod
    def get_next_available_number(directory: Path, start_number: int) -> int:
        """
        사용 가능한 다음 번호를 찾습니다.
        
        Args:
            directory (Path): 검사할 디렉토리
            start_number (int): 시작 번호
            
        Returns:
            int: 사용 가능한 다음 번호
        """
        used_numbers = FileRenamer.get_used_numbers(directory)
        while start_number in used_numbers:
            start_number += 1
        return start_number

    @staticmethod
    def rename_file(file_path: Path, new_number: int, prefix: str = "", suffix: str = "", max_retries: int = 3) -> Path:
        """
        파일의 이름을 새로운 번호로 변경합니다.
        
        Args:
            file_path (Path): 변경할 파일 경로
            new_number (int): 새로운 번호
            prefix (str): 파일 이름 앞에 추가할 텍스트
            suffix (str): 파일 이름 뒤에 추가할 텍스트
            max_retries (int): 최대 재시도 횟수
            
        Returns:
            Path: 새로운 파일 경로
        """
        logger = logging.getLogger(__name__)
        
        # 새 파일 이름 생성
        new_name = f"{prefix}{new_number}{suffix}{file_path.suffix}"
        new_path = file_path.parent / new_name

        for attempt in range(max_retries):
            try:
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
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"파일 접근 권한 오류가 지속됨: {file_path}")
                    raise
            except Exception as e:
                logger.error(f"파일 이름 변경 중 예상치 못한 오류: {e}")
                raise

    @staticmethod
    def rename_with_name(file_path: Path, new_name: str) -> Path:
        """
        파일의 이름을 새로운 이름으로 변경합니다.
        
        Args:
            file_path (Path): 변경할 파일 경로
            new_name (str): 새로운 이름 (확장자 제외)
            
        Returns:
            Path: 새로운 파일 경로
        """
        logger = logging.getLogger(__name__)
        
        new_path = file_path.parent / f"{new_name}{file_path.suffix}"
        
        # 대상 경로가 이미 존재하는 경우
        if new_path.exists():
            raise FileExistsError(f"대상 파일이 이미 존재함: {new_path}")
        
        try:
            file_path.rename(new_path)
            return new_path
        except Exception as e:
            logger.error(f"파일 이름 변경 실패: {e}")
            raise 