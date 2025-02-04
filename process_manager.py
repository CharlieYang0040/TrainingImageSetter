from pathlib import Path
from typing import Optional
import logging
from concurrent.futures import ThreadPoolExecutor
import time
from enum import Enum

from image_processor import ImageProcessor
from file_renamer import FileRenamer
from generateTxt_Function import TextFileGenerator
from progress_tracker import ProgressTracker

class ProcessingMode(Enum):
    COPY_ONLY = "copy_only"
    COPY_AND_TEXT = "copy_and_text"
    TEXT_ONLY = "text_only"

class ProcessManager:
    def __init__(self, input_path: Path, output_path: Path, 
                 mode: ProcessingMode, max_workers: int = 4,
                 resize_size: Optional[int] = None,
                 padding_color: str = 'black',
                 save_as_png: bool = False):
        self.input_path = input_path
        self.output_path = output_path
        self.mode = mode
        self.max_workers = max_workers
        self.progress_tracker = None
        self.logger = logging.getLogger(__name__)
        self.image_processor = ImageProcessor(resize_size, padding_color, save_as_png)

    def process_files(self) -> None:
        """
        파일 처리를 실행합니다.
        """
        if not self.output_path.exists():
            self.output_path.mkdir(parents=True)

        if self.mode == ProcessingMode.TEXT_ONLY:
            self._process_text_only()
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
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for idx, image_path in enumerate(image_files, 1):
                future = executor.submit(self._process_single_file, image_path, idx)
                futures.append(future)

            self._monitor_progress()

    def _process_single_file(self, image_path: Path, new_number: int) -> None:
        """
        단일 파일을 처리합니다.
        """
        try:
            temp_path = self.output_path / image_path.name
            processed_path = self.image_processor.process_image(image_path, temp_path)
            new_image_path = FileRenamer.rename_file(processed_path, new_number)

            if self.mode == ProcessingMode.COPY_AND_TEXT:
                TextFileGenerator.create_text_file(new_image_path)
                
            self.progress_tracker.update(1, f"처리 완료: {new_image_path.name}")
            
        except Exception as e:
            self.logger.error(f"파일 처리 중 오류 발생: {image_path}", exc_info=True)
            raise

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