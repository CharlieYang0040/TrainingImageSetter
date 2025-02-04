from pathlib import Path
from shutil import copy2
from typing import List, Set, Optional
from PIL import Image
import logging
Image.MAX_IMAGE_PIXELS = None  # DecompressionBombError 방지

class ImageProcessor:
    # 지원하는 이미지 확장자
    SUPPORTED_EXTENSIONS: Set[str] = {'.png', '.jpg', '.jpeg', '.gif'}

    def __init__(self, resize_size: Optional[int] = None, 
                 padding_color: str = 'black',
                 save_as_png: bool = False):
        self.resize_size = resize_size
        self.padding_color = padding_color
        self.save_as_png = save_as_png
        self.logger = logging.getLogger(__name__)

    def resize_image(self, image_path: Path, output_path: Path, size: int = 512) -> None:
        """
        이미지를 지정된 크기로 리사이즈합니다. 비율을 유지하며 패딩을 추가합니다.
        """
        try:
            with Image.open(image_path) as img:
                # 알파 채널 처리
                if img.mode in ('RGBA', 'LA') and self.padding_color != 'transparent':
                    background = Image.new('RGB', img.size, self.padding_color)
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB' and self.padding_color != 'transparent':
                    img = img.convert('RGB')

                # 비율 계산
                width, height = img.size
                aspect_ratio = width / height

                if aspect_ratio > 1:
                    new_width = size
                    new_height = int(size / aspect_ratio)
                else:
                    new_height = size
                    new_width = int(size * aspect_ratio)

                # 리사이즈
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # 패딩 처리
                if self.padding_color == 'transparent':
                    new_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                else:
                    padding_color = {'white': (255, 255, 255), 
                                   'black': (0, 0, 0)}.get(self.padding_color, (0, 0, 0))
                    new_img = Image.new('RGB', (size, size), padding_color)

                # 중앙에 배치
                paste_x = (size - new_width) // 2
                paste_y = (size - new_height) // 2
                
                if self.padding_color == 'transparent':
                    new_img.paste(img, (paste_x, paste_y), img if img.mode == 'RGBA' else None)
                else:
                    new_img.paste(img, (paste_x, paste_y))

                # 저장
                if self.padding_color == 'transparent' or self.save_as_png:
                    new_img.save(output_path.with_suffix('.png'), 'PNG')
                else:
                    new_img.save(output_path, quality=95, optimize=True)

        except Image.DecompressionBombError:
            self.logger.warning(f"큰 이미지 처리 중: {image_path}")
            with Image.open(image_path) as img:
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                if self.padding_color == 'transparent':
                    new_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                else:
                    padding_color = {'white': (255, 255, 255), 
                                   'black': (0, 0, 0)}.get(self.padding_color, (0, 0, 0))
                    new_img = Image.new('RGB', (size, size), padding_color)
                
                width, height = img.size
                paste_x = (size - width) // 2
                paste_y = (size - height) // 2
                new_img.paste(img, (paste_x, paste_y))
                
                if self.padding_color == 'transparent' or self.save_as_png:
                    new_img.save(output_path.with_suffix('.png'), 'PNG')
                else:
                    new_img.save(output_path, quality=95, optimize=True)

        except Exception as e:
            self.logger.error(f"이미지 처리 중 오류 발생: {str(e)}")
            raise

    @staticmethod
    def find_all_images(input_path: Path) -> List[Path]:
        """
        입력 경로의 모든 하위 폴더에서 이미지 파일을 찾습니다.

        Args:
            input_path (Path): 검색할 루트 경로

        Returns:
            List[Path]: 발견된 모든 이미지 파일의 경로 리스트
        """
        image_files = set()  # 중복 제거를 위해 set 사용
        for ext in ImageProcessor.SUPPORTED_EXTENSIONS:
            # 대소문자 구분 없이 한 번만 검색
            found_files = input_path.rglob(f"*{ext}")
            image_files.update(found_files)
        
        # 정렬된 리스트로 반환
        return sorted(list(image_files))

    def process_image(self, src_path: Path, dest_path: Path) -> Path:
        """
        이미지를 처리하고 저장합니다.
        """
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.resize_size:
            if self.save_as_png:
                # PNG로 저장할 경우 바로 PNG 확장자로 저장
                dest_path = dest_path.with_suffix('.png')
            self.resize_image(src_path, dest_path, self.resize_size)
        else:
            if self.save_as_png:
                # 리사이즈 없이 PNG로 변환만 할 경우
                dest_path = dest_path.with_suffix('.png')
                with Image.open(src_path) as img:
                    if img.mode == 'RGBA' or self.padding_color == 'transparent':
                        img.save(dest_path, 'PNG')
                    else:
                        img.convert('RGB').save(dest_path, 'PNG')
            else:
                # 그대로 복사
                copy2(src_path, dest_path)
            
        return dest_path 