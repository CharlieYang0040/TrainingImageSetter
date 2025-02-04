from pathlib import Path
from typing import Dict, List, Set, Tuple
import hashlib
from PIL import Image
import logging
import io

class ImageDuplicateChecker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_image_hash(self, image_path: Path) -> str:
        """
        이미지의 해시값을 계산합니다.
        
        Args:
            image_path (Path): 이미지 파일 경로
            
        Returns:
            str: 이미지의 해시값
        """
        try:
            with Image.open(image_path) as img:
                # 이미지를 바이트로 변환
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format=img.format)
                img_byte_arr = img_byte_arr.getvalue()
                
                # MD5 해시 계산
                return hashlib.md5(img_byte_arr).hexdigest()
        except Exception as e:
            self.logger.error(f"이미지 해시 계산 중 오류 발생 ({image_path}): {e}")
            return ""

    def find_duplicates(self, directory: Path) -> Dict[str, List[Path]]:
        """
        지정된 디렉토리에서 중복된 이미지를 찾습니다.
        
        Args:
            directory (Path): 검사할 디렉토리 경로
            
        Returns:
            Dict[str, List[Path]]: 해시값을 키로, 중복된 파일 경로 리스트를 값으로 하는 딕셔너리
        """
        hash_dict: Dict[str, List[Path]] = {}
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}

        # 모든 이미지 파일 검사
        for ext in image_extensions:
            for image_path in directory.rglob(f"*{ext}"):
                image_hash = self.calculate_image_hash(image_path)
                if image_hash:
                    if image_hash in hash_dict:
                        hash_dict[image_hash].append(image_path)
                    else:
                        hash_dict[image_hash] = [image_path]

        # 중복된 이미지만 필터링
        return {k: v for k, v in hash_dict.items() if len(v) > 1}

    def print_duplicates(self, duplicates: Dict[str, List[Path]]) -> None:
        """
        중복된 이미지 정보를 출력합니다.
        
        Args:
            duplicates (Dict[str, List[Path]]): 중복 이미지 정보
        """
        if not duplicates:
            print("중복된 이미지가 없습니다.")
            return

        print("\n=== 중복된 이미지 목록 ===")
        for hash_value, file_list in duplicates.items():
            print(f"\n동일한 이미지 그룹 (해시: {hash_value}):")
            for file_path in file_list:
                print(f"  - {file_path}") 