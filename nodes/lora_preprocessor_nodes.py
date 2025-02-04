import os
import folder_paths
from PIL import Image
from pathlib import Path
from .utils.image_processor import ImageProcessor
import datetime

class LoraPreprocessorLoader:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "lora_preprocessor"
        
        # ComfyUI의 input 디렉토리에 preprocessor_input 폴더 생성
        self.input_base_dir = os.path.join(folder_paths.get_input_directory(), "preprocessor_input")
        if not os.path.exists(self.input_base_dir):
            os.makedirs(self.input_base_dir)
            
        # 입력 폴더를 ComfyUI의 폴더 경로에 등록
        folder_paths.add_input_path(self.input_base_dir)

    @classmethod
    def INPUT_TYPES(cls):
        # 입력 폴더 목록 동적 생성
        input_folders = []
        preprocessor_path = os.path.join(folder_paths.get_input_directory(), "preprocessor_input")
        if os.path.exists(preprocessor_path):
            input_folders = [f.name for f in os.scandir(preprocessor_path) if f.is_dir()]
        
        return {
            "required": {
                "input_folder": (input_folders, {"default": input_folders[0] if input_folders else None}),
                "mode": (["copy_only", "copy_and_text", "text_only"], {"default": "copy_and_text"}),
                "resize_enabled": ("BOOLEAN", {"default": False}),
                "resize_size": (["512", "1024"], {"default": "512"}),
                "padding_color": (["white", "black", "transparent"], {"default": "black"}),
                "save_as_png": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "preprocess"
    CATEGORY = "LoRA Preprocessor"
    OUTPUT_NODE = True

    def preprocess(self, input_folder, mode="copy_and_text", 
                  resize_enabled=False, resize_size="512", 
                  padding_color="black", save_as_png=True):
        
        # 입력 폴더 경로 설정
        input_path = os.path.join(self.input_base_dir, input_folder)
        
        # 출력 폴더 설정 (ComfyUI의 output 디렉토리 아래에 생성)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"preprocessed_{timestamp}")
        os.makedirs(output_path, exist_ok=True)

        # 이미지 프로세서 초기화
        processor = ImageProcessor(
            resize_size=int(resize_size) if resize_enabled else None,
            padding_color=padding_color,
            save_as_png=save_as_png
        )

        # 입력 디렉토리의 모든 이미지 찾기
        image_files = [f for f in Path(input_path).glob("**/*") 
                      if f.suffix.lower() in processor.SUPPORTED_EXTENSIONS]
        
        processed_count = 0
        for idx, image_path in enumerate(image_files, 1):
            try:
                temp_path = Path(output_path) / image_path.name
                processed_path = processor.process_image(image_path, temp_path)
                new_image_path = FileRenamer.rename_file(processed_path, idx)

                if mode in ["copy_and_text", "text_only"]:
                    TextFileGenerator.create_text_file(new_image_path)
                
                processed_count += 1

            except Exception as e:
                print(f"파일 처리 중 오류 발생: {image_path} - {str(e)}")

        results = {
            "processed_count": processed_count,
            "output_path": output_path,
            "mode": mode
        }
        
        return (f"처리 완료: {processed_count}개 파일\n저장 위치: {output_path}",)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """노드의 캐시를 방지하기 위한 메서드"""
        return float("NaN") 