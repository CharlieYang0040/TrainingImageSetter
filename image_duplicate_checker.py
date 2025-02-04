# image_duplicate_checker.py

from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import hashlib
from PIL import Image
import logging
import io
from progress_tracker import ProgressTracker

class ImageDuplicateChecker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        Image.MAX_IMAGE_PIXELS = None  # PIL의 기본 제한 해제

    def calculate_image_hash(self, image_path: Path) -> str:
        """
        이미지의 MD5 해시값을 계산합니다. 큰 이미지의 경우 축소하여 처리합니다.
        
        Args:
            image_path (Path): 이미지 파일 경로
            
        Returns:
            str: 이미지의 해시값
        """
        try:
            with Image.open(image_path) as img:
                # 큰 이미지 처리를 위한 예외 처리
                try:
                    # 이미지를 메모리에 로드하여 해시 계산
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format=img.format)
                    img_byte_arr = img_byte_arr.getvalue()
                except Image.DecompressionBombError:
                    # 이미지가 너무 큰 경우 축소하여 처리
                    self.logger.warning(f"큰 이미지 감지됨, 축소하여 처리: {image_path}")
                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=50)
                    img_byte_arr = img_byte_arr.getvalue()
                
                return hashlib.md5(img_byte_arr).hexdigest()
                
        except Exception as e:
            self.logger.error(f"이미지 해시 계산 중 오류 발생 ({image_path}): {e}")
            return ""

    def check_output_duplicates(self, output_path: Path, progress_tracker: Optional['ProgressTracker'] = None) -> Dict[str, List[Path]]:
        """
        출력 폴더의 중복 이미지를 검사합니다.
        
        Args:
            output_path (Path): 검사할 출력 폴더 경로
            progress_tracker (ProgressTracker, optional): 진행 상황 추적기
            
        Returns:
            Dict[str, List[Path]]: 해시값을 키로, 중복된 파일 경로 리스트를 값으로 하는 딕셔너리
        """
        hash_dict: Dict[str, List[Path]] = {}
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
        
        # 전체 이미지 파일 목록 수집
        all_images = []
        for ext in image_extensions:
            all_images.extend(list(output_path.glob(f"*{ext}")))
            
        total_images = len(all_images)
        if progress_tracker:
            progress_tracker.total = total_images * 2  # 해시 계산과 중복 제거 두 단계를 위해 2배
            print(f"\n총 {total_images}개 이미지 검사 시작...")

        # 출력 폴더의 모든 이미지 파일 검사
        for idx, image_path in enumerate(all_images, 1):
            if progress_tracker:
                progress_tracker.update(1, f"해시 계산 중: {image_path.name} ({idx}/{total_images})")
            
            image_hash = self.calculate_image_hash(image_path)
            if image_hash:
                if image_hash in hash_dict:
                    hash_dict[image_hash].append(image_path)
                else:
                    hash_dict[image_hash] = [image_path]

        return {k: v for k, v in hash_dict.items() if len(v) > 1}

    def print_duplicates(self, duplicates: Dict[str, List[Path]]) -> None:
        """
        중복된 이미지 정보를 출력합니다.
        
        Args:
            duplicates (Dict[str, List[Path]]): 중복 이미지 정보
        """
        if not duplicates:
            print("\n중복된 이미지가 없습니다.")
            return

        print("\n=== 중복된 이미지 목록 ===")
        for hash_value, file_list in duplicates.items():
            print(f"\n동일한 이미지 그룹 (해시: {hash_value}):")
            for file_path in file_list:
                print(f"  - {file_path}")

    def remove_duplicates(self, output_path: Path, progress_tracker: Optional['ProgressTracker'] = None) -> Tuple[int, List[Path]]:
        """
        출력 폴더의 중복 이미지를 검사하고 제거합니다.
        
        Args:
            output_path (Path): 검사할 출력 폴더 경로
            progress_tracker (ProgressTracker, optional): 진행 상황 추적기
            
        Returns:
            Tuple[int, List[Path]]: (제거된 파일 수, 제거된 파일 경로 리스트)
        """
        duplicates = self.check_output_duplicates(output_path, progress_tracker)
        removed_files = []
        
        if not duplicates:
            if progress_tracker:
                progress_tracker.update(progress_tracker.total - progress_tracker.current, "검사 완료")
            return 0, removed_files

        total_duplicates = sum(len(files) - 1 for files in duplicates.values())
        print(f"\n중복 파일 {total_duplicates}개 발견, 제거 시작...")
        
        for hash_value, file_list in duplicates.items():
            # 첫 번째 파일은 유지하고 나머지는 제거
            for file_path in file_list[1:]:
                try:
                    if progress_tracker:
                        progress_tracker.update(1, f"중복 파일 제거 중: {file_path.name}")
                    
                    file_path.unlink()  # 파일 삭제
                    txt_path = file_path.with_suffix('.txt')
                    if txt_path.exists():  # 관련된 텍스트 파일도 삭제
                        txt_path.unlink()
                    removed_files.append(file_path)
                except Exception as e:
                    self.logger.error(f"파일 삭제 중 오류 발생 ({file_path}): {e}")
        
        if progress_tracker:
            progress_tracker.update(progress_tracker.total - progress_tracker.current, "작업 완료")
        
        return len(removed_files), removed_files

    def print_removal_results(self, removed_count: int, removed_files: List[Path]) -> None:
        """
        중복 이미지 제거 결과를 출력합니다.
        
        Args:
            removed_count (int): 제거된 파일 수
            removed_files (List[Path]): 제거된 파일 경로 리스트
        """
        if removed_count == 0:
            print("\n중복된 이미지가 없습니다.")
            return

        print(f"\n=== 중복 이미지 제거 결과 ===")
        print(f"총 {removed_count}개의 중복 파일이 제거되었습니다.")
        print("\n제거된 파일 목록:")
        for file_path in removed_files:
            print(f"  - {file_path}") 