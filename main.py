import argparse
from pathlib import Path
import logging
from process_manager import ProcessManager, ProcessingMode
from image_duplicate_checker import ImageDuplicateChecker

def setup_logging(debug_mode: bool):
    level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('process.log'),
            logging.StreamHandler()
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='LoRA 학습용 이미지 전처리 도구')
    parser.add_argument('input_path', type=str, help='입력 이미지 폴더 경로')
    parser.add_argument('output_path', type=str, help='출력 폴더 경로')
    parser.add_argument('--mode', type=str, 
                       choices=['copy_only', 'copy_and_text', 'text_only'],
                       default='copy_and_text', help='처리 모드 선택')
    parser.add_argument('--workers', type=int, default=4, help='작업자 스레드 수 (기본값: 4)')
    parser.add_argument('--debug', action='store_true', help='디버그 모드 활성화')
    parser.add_argument('--check-duplicates', action='store_true', help='중복 이미지 검사 실행')
    
    # 리사이즈 관련 인자
    parser.add_argument('--resize', type=int, choices=[512, 1024], 
                       help='이미지 리사이즈 크기 (512 또는 1024)')
    parser.add_argument('--padding-color', type=str, choices=['white', 'black', 'transparent'],
                       default='black', help='패딩 색상 (기본값: black)')
    parser.add_argument('--save-as-png', action='store_true', 
                       help='리사이즈된 이미지를 PNG로 저장')
    
    args = parser.parse_args()
    
    setup_logging(args.debug)
    
    try:
        if args.check_duplicates:
            checker = ImageDuplicateChecker()
            duplicates = checker.find_duplicates(Path(args.input_path))
            checker.print_duplicates(duplicates)
            if duplicates:
                response = input("\n처리를 계속하시겠습니까? (y/n): ")
                if response.lower() != 'y':
                    return

        processor = ProcessManager(
            input_path=Path(args.input_path),
            output_path=Path(args.output_path),
            mode=ProcessingMode(args.mode),
            max_workers=args.workers,
            resize_size=args.resize,
            padding_color=args.padding_color,
            save_as_png=args.save_as_png
        )
        processor.process_files()
        print("\n작업 완료!")

    except Exception as e:
        logging.error("처리 중 오류가 발생했습니다.", exc_info=True)
        raise

if __name__ == "__main__":
    main() 