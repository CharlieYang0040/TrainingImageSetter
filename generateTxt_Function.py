import os
import re
from pathlib import Path
from typing import List, Union

def get_next_number(files):
    # 현재 존재하는 숫자 파일들 중 가장 큰 숫자 찾기
    numbers = []
    for file in files:
        if file.stem.isdigit():
            numbers.append(int(file.stem))
    return max(numbers, default=0) + 1

def rename_images():
    # 현재 디렉토리 경로
    current_dir = Path.cwd()
    
    # 이미지 파일 확장자
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
    
    # 모든 이미지 파일 찾기
    image_files = [f for f in current_dir.glob('*.*') if f.suffix.lower() in image_extensions]
    
    # 다음 사용할 번호 찾기
    next_number = get_next_number(image_files)
    
    # 숫자가 아닌 이름을 가진 이미지 파일 처리
    for img_file in image_files:
        if not img_file.stem.isdigit():
            new_name = f"{next_number}{img_file.suffix}"
            new_path = img_file.parent / new_name
            
            # 이미 존재하는 파일명이면 다음 번호 사용
            while new_path.exists():
                next_number += 1
                new_name = f"{next_number}{img_file.suffix}"
                new_path = img_file.parent / new_name
            
            img_file.rename(new_path)
            next_number += 1

def create_matching_text_files():
    current_dir = Path.cwd()
    
    # PNG 파일 찾기
    png_files = list(current_dir.glob('*.png'))
    
    # 각 PNG 파일에 대해 대응하는 텍스트 파일 생성
    for png_file in png_files:
        if png_file.stem.isdigit():
            txt_file = png_file.with_suffix('.txt')
            
            # 텍스트 파일이 존재하지 않을 경우에만 생성
            if not txt_file.exists():
                txt_file.touch()

class TextFileGenerator:
    @staticmethod
    def create_text_files(image_paths: List[Union[str, Path]]) -> None:
        """
        이미지 파일들에 대응하는 빈 텍스트 파일들을 생성합니다.
        
        Args:
            image_paths (List[Union[str, Path]]): 이미지 파일 경로 리스트
        """
        for img_path in image_paths:
            img_path = Path(img_path) if isinstance(img_path, str) else img_path
            txt_path = img_path.with_suffix('.txt')
            
            if not txt_path.exists():
                txt_path.touch()

    @staticmethod
    def create_text_file(image_path: Union[str, Path]) -> None:
        """
        단일 이미지 파일에 대응하는 빈 텍스트 파일을 생성합니다.
        
        Args:
            image_path (Union[str, Path]): 이미지 파일 경로
        """
        path = Path(image_path) if isinstance(image_path, str) else image_path
        txt_path = path.with_suffix('.txt')
        
        if not txt_path.exists():
            txt_path.touch()

    @staticmethod
    def create_text_files_from_output(output_path: Path, progress_tracker=None) -> None:
        """
        출력 폴더의 이미지 파일들에 대응하는 텍스트 파일을 생성합니다.
        
        Args:
            output_path (Path): 출력 폴더 경로
            progress_tracker (Optional[ProgressTracker]): 진행 상황 추적기
        """
        image_files = [f for f in output_path.glob("*") 
                      if f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}]
        
        for img_path in image_files:
            txt_path = img_path.with_suffix('.txt')
            if not txt_path.exists():
                txt_path.touch()
            if progress_tracker:
                progress_tracker.update(1, f"텍스트 파일 생성 완료: {txt_path.name}")

def main():
    rename_images()
    create_matching_text_files()

if __name__ == "__main__":
    main()
