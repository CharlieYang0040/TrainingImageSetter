# process_manager.py

from pathlib import Path
from typing import Optional, List
import logging
from concurrent.futures import ThreadPoolExecutor
import time
from enum import Enum
import threading

from image_processor import ImageProcessor
from file_renamer import FileRenamer
from generateTxt_Function import TextFileGenerator
from progress_tracker import ProgressTracker
from image_duplicate_checker import ImageDuplicateChecker

class ProcessingMode(Enum):
    COPY_ONLY = "copy_only"
    COPY_AND_TEXT = "copy_and_text"
    TEXT_ONLY = "text_only"
    CHECK_AND_REMOVE_DUPLICATES = "check_duplicates"
    RENAME_ONLY = "rename_only"

class ProcessManager:
    def __init__(self, input_path: Path, output_path: Path, 
                 mode: ProcessingMode, max_workers: int = 4,
                 resize_size: Optional[int] = None,
                 padding_color: str = 'black',
                 save_as_png: bool = False,
                 use_numbering: bool = True,
                 use_prefix: bool = False,
                 use_suffix: bool = False,
                 prefix: str = "",
                 suffix: str = "",
                 use_replace: bool = False,
                 replace_from: str = "",
                 replace_to: str = ""):
        self.input_path = input_path
        self.output_path = output_path
        self.mode = mode
        self.max_workers = max_workers
        self.progress_tracker = None
        self.logger = logging.getLogger(__name__)
        self.image_processor = ImageProcessor(resize_size, padding_color, save_as_png)
        self.use_numbering = use_numbering
        self.use_prefix = use_prefix
        self.use_suffix = use_suffix
        self.prefix = prefix if use_prefix else ""
        self.suffix = suffix if use_suffix else ""
        self.use_replace = use_replace
        self.replace_from = replace_from if use_replace else ""
        self.replace_to = replace_to if use_replace else ""

    def process_files(self) -> None:
        """
        파일 처리를 실행합니다.
        """
        if not self.output_path.exists():
            self.output_path.mkdir(parents=True)

        if self.mode == ProcessingMode.TEXT_ONLY:
            self._process_text_only()
        elif self.mode == ProcessingMode.CHECK_AND_REMOVE_DUPLICATES:
            self._remove_duplicates()
        elif self.mode == ProcessingMode.RENAME_ONLY:
            self._rename_existing_files()
        else:
            self._process_images()

    def _process_text_only(self) -> None:
        """
        텍스트 파일만 생성하는 모드를 처리합니다.
        """
        image_files = [f for f in self.output_path.glob("*") 
                      if f.suffix.lower() in ImageProcessor.SUPPORTED_EXTENSIONS]
        self.progress_tracker = ProgressTracker(len(image_files))
        TextFileGenerator.create_text_files_from_output(self.output_path, self.progress_tracker)

    def _process_images(self) -> None:
        """
        이미지 처리 모드를 실행합니다.
        """
        image_files = self.image_processor.find_all_images(self.input_path)
        self.progress_tracker = ProgressTracker(len(image_files))
        processed_files = []
        
        # 진행 상황 모니터링 시작
        monitor_thread = threading.Thread(target=self._monitor_progress)
        monitor_thread.start()
        
        # 1단계: 멀티스레드로 이미지 복사/처리
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for image_path in image_files:
                future = executor.submit(self._copy_single_file, image_path)
                futures.append(future)
            
            # 모든 복사 작업 완료 대기
            for future in futures:
                try:
                    processed_path = future.result()
                    if processed_path:
                        processed_files.append(processed_path)
                except Exception as e:
                    self.logger.error(f"파일 처리 중 오류 발생", exc_info=True)
                    raise

        # 모니터링 스레드 완료 대기
        monitor_thread.join()
        
        # 2단계: 단일 스레드로 순차적 이름 변경
        self._rename_processed_files(processed_files)

    def _copy_single_file(self, image_path: Path) -> Optional[Path]:
        """
        단일 파일을 복사/처리합니다.
        """
        try:
            temp_path = self.output_path / image_path.name
            processed_path = self.image_processor.process_image(image_path, temp_path)
            self.progress_tracker.update(1, f"처리 완료: {image_path.name}")
            return processed_path
        except Exception as e:
            self.logger.error(f"파일 처리 중 오류 발생: {image_path}", exc_info=True)
            raise

    def _rename_processed_files(self, processed_files: List[Path]) -> None:
        """
        처리된 파일들의 이름을 순차적으로 변경합니다.
        """
        # 파일들을 정렬하여 순차적으로 처리
        sorted_files = sorted(processed_files, key=lambda x: x.name)
        print(f"\n총 {len(sorted_files)}개 파일 처리 시작")
        
        if self.use_numbering:
            self._rename_with_numbers(sorted_files)
        else:
            self._rename_with_options(sorted_files)

    def _rename_with_numbers(self, files: List[Path]) -> None:
        """
        파일들의 이름을 순차적인 번호로 변경합니다.
        
        Args:
            files (List[Path]): 이름을 변경할 파일 목록
        """
        for idx, path in enumerate(files, 1):
            try:
                new_name = str(idx)
                new_path = FileRenamer.rename_with_name(path, new_name)
                print(f"이름 변경: {path.name} -> {new_path.name}")
                
                if self.mode == ProcessingMode.COPY_AND_TEXT:
                    TextFileGenerator.create_text_file(new_path)
                
            except Exception as e:
                self.logger.error(f"파일 이름 변경 중 오류 발생: {str(e)}")
                continue

    def _rename_with_options(self, files: List[Path]) -> None:
        """
        파일들의 이름을 사용자 지정 옵션(접두사/접미사/치환)에 따라 변경합니다.
        
        Args:
            files (List[Path]): 이름을 변경할 파일 목록
        """
        for path in files:
            try:
                original_name = path.stem
                new_name = original_name
                
                if self.use_replace:
                    new_name = new_name.replace(self.replace_from, self.replace_to)
                
                if self.use_prefix:
                    new_name = f"{self.prefix}{new_name}"
                
                if self.use_suffix:
                    new_name = f"{new_name}{self.suffix}"
                
                if new_name == original_name:
                    print(f"건너뛰기: {path.name} (변경사항 없음)")
                    continue
                
                new_path = FileRenamer.rename_with_name(path, new_name)
                print(f"이름 변경: {path.name} -> {new_path.name}")
                
                if self.mode == ProcessingMode.COPY_AND_TEXT:
                    TextFileGenerator.create_text_file(new_path)
                
            except Exception as e:
                self.logger.error(f"파일 이름 변경 중 오류 발생: {str(e)}")
                continue

    def _monitor_progress(self) -> None:
        """
        진행 상황을 모니터링합니다.
        """
        while True:
            progress = self.progress_tracker.get_progress()
            print(f"\r진행률: {progress.percentage:.1f}% ({progress.current}/{progress.total}) - {progress.status}", end="")
            
            if progress.current >= progress.total:
                break
            time.sleep(0.1)

    def _remove_duplicates(self) -> None:
        """
        중복 이미지를 검사하고 제거합니다.
        """
        checker = ImageDuplicateChecker()
        self.progress_tracker = ProgressTracker(100)  # 임시 총량으로 초기화
        
        print("\n중복 이미지 검사 및 제거를 시작합니다...")
        removed_count, removed_files = checker.remove_duplicates(self.output_path, self.progress_tracker)
        
        print("\n=== 중복 이미지 제거 결과 ===")
        if removed_count == 0:
            print("중복된 이미지가 없습니다.")
        else:
            print(f"\n총 {removed_count}개의 중복 파일이 제거되었습니다.")
            print("\n제거된 파일 목록:")
            for file_path in removed_files:
                print(f"  - {file_path}")

    def _rename_existing_files(self) -> None:
        """
        출력 폴더의 기존 파일들의 이름을 변경합니다.
        """
        image_files = [f for f in self.output_path.glob("*") 
                      if f.suffix.lower() in ImageProcessor.SUPPORTED_EXTENSIONS]
        
        if not image_files:
            print("이름을 변경할 이미지 파일이 없습니다.")
            return
        
        self.progress_tracker = ProgressTracker(len(image_files))
        sorted_files = sorted(image_files, key=lambda x: x.name)
        
        print(f"\n총 {len(sorted_files)}개 파일 이름 변경 시작")
        
        for idx, path in enumerate(sorted_files, 1):
            try:
                original_name = path.stem
                new_name = original_name
                
                if self.use_numbering:
                    new_name = str(idx)
                else:
                    if self.use_replace:
                        new_name = new_name.replace(self.replace_from, self.replace_to)
                    
                    if self.use_prefix:
                        new_name = f"{self.prefix}{new_name}"
                    
                    if self.use_suffix:
                        new_name = f"{new_name}{self.suffix}"
                
                if new_name == original_name:
                    print(f"건너뛰기: {path.name} (변경사항 없음)")
                    self.progress_tracker.update(1, f"건너뛰기: {path.name}")
                    continue
                
                new_path = FileRenamer.rename_with_name(path, new_name)
                print(f"이름 변경: {path.name} -> {new_path.name}")
                self.progress_tracker.update(1, f"이름 변경 완료: {new_path.name}")
                
            except Exception as e:
                print(f"오류 발생: {path.name} - {str(e)}")
                self.progress_tracker.update(1, f"오류: {path.name}")
                continue 