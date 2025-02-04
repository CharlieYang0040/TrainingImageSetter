from PIL import Image
from pathlib import Path
import shutil

class ImageProcessor:
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}

    def __init__(self, resize_size=None, padding_color='black', save_as_png=False):
        self.resize_size = resize_size
        self.padding_color = padding_color
        self.save_as_png = save_as_png

    def process_image(self, src_path, dest_path):
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.resize_size:
            self.resize_image(src_path, dest_path, self.resize_size)
        else:
            if self.save_as_png:
                dest_path = dest_path.with_suffix('.png')
                with Image.open(src_path) as img:
                    if img.mode == 'RGBA' or self.padding_color == 'transparent':
                        img.save(dest_path, 'PNG')
                    else:
                        img.convert('RGB').save(dest_path, 'PNG')
            else:
                shutil.copy2(src_path, dest_path)
                
        return dest_path

    def resize_image(self, image_path, output_path, size):
        """
        이미지를 지정된 크기로 리사이즈하고 패딩을 추가합니다.
        
        Args:
            image_path (Path): 입력 이미지 경로
            output_path (Path): 출력 이미지 경로
            size (int): 목표 크기 (가로/세로)
        """
        with Image.open(image_path) as img:
            # RGBA 이미지 처리
            if img.mode == 'RGBA':
                if self.padding_color != 'transparent':
                    # 배경색으로 알파 채널 병합
                    background = Image.new('RGB', img.size, self.padding_color)
                    background.paste(img, mask=img.split()[3])
                    img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 원본 이미지 비율 계산
            width, height = img.size
            aspect_ratio = width / height

            if aspect_ratio > 1:  # 가로가 더 긴 경우
                new_width = size
                new_height = int(size / aspect_ratio)
            else:  # 세로가 더 긴 경우
                new_height = size
                new_width = int(size * aspect_ratio)

            # 이미지 리사이즈
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 패딩을 위한 새 이미지 생성
            if self.padding_color == 'transparent' and self.save_as_png:
                padded_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            else:
                padded_img = Image.new('RGB', (size, size), self.padding_color)

            # 리사이즈된 이미지를 중앙에 배치
            paste_x = (size - new_width) // 2
            paste_y = (size - new_height) // 2

            if self.padding_color == 'transparent' and self.save_as_png:
                padded_img.paste(resized_img, (paste_x, paste_y), 
                               resized_img if resized_img.mode == 'RGBA' else None)
            else:
                padded_img.paste(resized_img, (paste_x, paste_y))

            # 출력 경로 확장자 처리
            if self.save_as_png:
                output_path = output_path.with_suffix('.png')

            # 이미지 저장
            if self.padding_color == 'transparent' and self.save_as_png:
                padded_img.save(output_path, 'PNG')
            else:
                padded_img.convert('RGB').save(output_path, 
                                             'PNG' if self.save_as_png else 'JPEG',
                                             quality=95) 