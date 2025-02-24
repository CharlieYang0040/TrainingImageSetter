# gui_launcher.py

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
from pathlib import Path
from image_duplicate_checker import ImageDuplicateChecker
from main import ProcessManager, ProcessingMode
from progress_tracker import ProgressTracker
import threading
import os

class LoraPreprocessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LoRA 학습용 이미지 전처리 도구")
        
        # 변수 초기화
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.mode = tk.StringVar(value="copy_and_text")
        self.workers = tk.StringVar(value="8")
        self.debug_mode = tk.BooleanVar()
        
        # 리사이즈 관련 변수
        self.resize_enabled = tk.BooleanVar(value=False)
        self.resize_size = tk.StringVar(value="512")
        self.padding_color = tk.StringVar(value="white")
        self.save_as_png = tk.BooleanVar(value=True)
        
        self.create_widgets()
        
    def create_widgets(self):
        # 입력 경로
        input_frame = ttk.LabelFrame(self.root, text="입력 경로", padding=10)
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Entry(input_frame, textvariable=self.input_path, width=50).grid(row=0, column=0, padx=5)
        ttk.Button(input_frame, text="찾아보기", command=self.browse_input).grid(row=0, column=1)
        
        # 출력 경로
        output_frame = ttk.LabelFrame(self.root, text="출력 경로", padding=10)
        output_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Entry(output_frame, textvariable=self.output_path, width=50).grid(row=0, column=0, padx=5)
        ttk.Button(output_frame, text="찾아보기", command=self.browse_output).grid(row=0, column=1)
        
        # 처리 모드
        mode_frame = ttk.LabelFrame(self.root, text="처리 모드", padding=10)
        mode_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Radiobutton(mode_frame, text="이미지만 복사", 
                       variable=self.mode, value="copy_only").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="이미지 복사 + 텍스트 생성", 
                       variable=self.mode, value="copy_and_text").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="텍스트만 생성", 
                       variable=self.mode, value="text_only").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="중복 이미지 검사", 
                       variable=self.mode, value="check_duplicates").grid(row=3, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="이름 변경만", 
                       variable=self.mode, value="rename_only").grid(row=4, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="이미지 크롤링", 
                       variable=self.mode, value="crawl_images").grid(row=5, column=0, sticky="w")
        
        # 리사이즈 옵션
        resize_frame = ttk.LabelFrame(self.root, text="리사이즈 옵션", padding=10)
        resize_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        def update_resize_options(*args):
            state = "normal" if self.resize_enabled.get() else "disabled"
            size_combo["state"] = state
            padding_combo["state"] = state
            png_check["state"] = state
        
        # 리사이즈 활성화 체크박스
        resize_check = ttk.Checkbutton(resize_frame, text="이미지 리사이즈 활성화", 
                                     variable=self.resize_enabled, 
                                     command=update_resize_options)
        resize_check.grid(row=0, column=0, columnspan=2, sticky="w")
        
        # 리사이즈 크기 선택
        ttk.Label(resize_frame, text="리사이즈 크기:").grid(row=1, column=0, sticky="w", padx=5)
        size_combo = ttk.Combobox(resize_frame, textvariable=self.resize_size, 
                                values=["512", "1024"], width=10, state="disabled")
        size_combo.grid(row=1, column=1, sticky="w", padx=5)
        
        # 패딩 색상 선택
        ttk.Label(resize_frame, text="패딩 색상:").grid(row=2, column=0, sticky="w", padx=5)
        padding_combo = ttk.Combobox(resize_frame, textvariable=self.padding_color,
                                   values=["white", "black", "transparent"], 
                                   width=10, state="disabled")
        padding_combo.grid(row=2, column=1, sticky="w", padx=5)
        
        # PNG 저장 옵션
        png_check = ttk.Checkbutton(resize_frame, text="PNG 파일로 저장", 
                                  variable=self.save_as_png, state="disabled")
        png_check.grid(row=3, column=0, columnspan=2, sticky="w")
        
        # 추가 옵션
        options_frame = ttk.LabelFrame(self.root, text="추가 옵션", padding=10)
        options_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(options_frame, text="작업자 스레드 수:").grid(row=0, column=0, sticky="w")
        ttk.Entry(options_frame, textvariable=self.workers, width=5).grid(row=0, column=1, padx=5)
        
        ttk.Checkbutton(options_frame, text="디버그 모드", 
                       variable=self.debug_mode).grid(row=1, column=0, sticky="w")
        
        # 이름 변경 옵션 프레임 추가
        rename_frame = ttk.LabelFrame(self.root, text="이름 변경 옵션", padding=10)
        rename_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        
        # 번호 매기기 체크박스
        self.use_numbering = tk.BooleanVar(value=True)  # 기본값 True
        ttk.Checkbutton(rename_frame, text="번호 매기기", 
                        variable=self.use_numbering).grid(row=0, column=0, columnspan=2, sticky="w", padx=5)
        
        # Prefix 체크박스와 입력
        self.use_prefix = tk.BooleanVar(value=False)
        self.prefix = tk.StringVar()
        self.prefix_check = ttk.Checkbutton(rename_frame, text="접두사 사용", 
                                          variable=self.use_prefix)
        self.prefix_check.grid(row=1, column=0, sticky="w", padx=5)
        self.prefix_entry = ttk.Entry(rename_frame, textvariable=self.prefix, width=20, state="disabled")
        self.prefix_entry.grid(row=1, column=1, sticky="w", padx=5)
        
        # Suffix 체크박스와 입력
        self.use_suffix = tk.BooleanVar(value=False)
        self.suffix = tk.StringVar()
        self.suffix_check = ttk.Checkbutton(rename_frame, text="접미사 사용", 
                                          variable=self.use_suffix)
        self.suffix_check.grid(row=2, column=0, sticky="w", padx=5)
        self.suffix_entry = ttk.Entry(rename_frame, textvariable=self.suffix, width=20, state="disabled")
        self.suffix_entry.grid(row=2, column=1, sticky="w", padx=5)
        
        # Replace 체크박스와 입력
        self.use_replace = tk.BooleanVar(value=False)
        self.replace_from = tk.StringVar()
        self.replace_to = tk.StringVar()
        self.replace_check = ttk.Checkbutton(rename_frame, text="문자열 치환", 
                                           variable=self.use_replace)
        self.replace_check.grid(row=3, column=0, sticky="w", padx=5)
        
        replace_frame = ttk.Frame(rename_frame)
        replace_frame.grid(row=3, column=1, sticky="w", padx=5)
        
        self.replace_from_entry = ttk.Entry(replace_frame, textvariable=self.replace_from, 
                                          width=10, state="disabled")
        self.replace_from_entry.grid(row=0, column=0, padx=2)
        ttk.Label(replace_frame, text="→").grid(row=0, column=1, padx=2)
        self.replace_to_entry = ttk.Entry(replace_frame, textvariable=self.replace_to, 
                                        width=10, state="disabled")
        self.replace_to_entry.grid(row=0, column=2, padx=2)
        
        # 체크박스 상태에 따른 입력 필드 활성화/비활성화 함수들
        def update_all_options(*args):
            numbering_enabled = self.use_numbering.get()
            state = "disabled" if numbering_enabled else "normal"
            
            # 번호 매기기가 켜져있으면 다른 옵션들 비활성화
            self.prefix_check["state"] = state
            self.suffix_check["state"] = state
            self.replace_check["state"] = state
            
            if numbering_enabled:
                # 모든 옵션 강제 비활성화
                self.prefix_entry["state"] = "disabled"
                self.suffix_entry["state"] = "disabled"
                self.replace_from_entry["state"] = "disabled"
                self.replace_to_entry["state"] = "disabled"
            else:
                # 각 옵션의 체크 상태에 따라 활성화
                update_prefix_entry()
                update_suffix_entry()
                update_replace_entry()
        
        def update_prefix_entry(*args):
            if not self.use_numbering.get():
                self.prefix_entry["state"] = "normal" if self.use_prefix.get() else "disabled"
        
        def update_suffix_entry(*args):
            if not self.use_numbering.get():
                self.suffix_entry["state"] = "normal" if self.use_suffix.get() else "disabled"
        
        def update_replace_entry(*args):
            if not self.use_numbering.get():
                state = "normal" if self.use_replace.get() else "disabled"
                self.replace_from_entry["state"] = state
                self.replace_to_entry["state"] = state
        
        # 이벤트 연결
        self.use_numbering.trace_add("write", update_all_options)
        self.use_prefix.trace_add("write", update_prefix_entry)
        self.use_suffix.trace_add("write", update_suffix_entry)
        self.use_replace.trace_add("write", update_replace_entry)
        
        # 초기 상태 설정
        update_all_options()
        
        # 크롤링 옵션 프레임 추가
        crawling_frame = ttk.LabelFrame(self.root, text="크롤링 옵션", padding=10)
        crawling_frame.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        # 검색 엔진 선택
        self.use_google = tk.BooleanVar(value=True)
        self.use_naver = tk.BooleanVar(value=True) 
        self.use_artstation = tk.BooleanVar(value=False)

        ttk.Checkbutton(crawling_frame, text="Google 검색",
                        variable=self.use_google).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Checkbutton(crawling_frame, text="Naver 검색", 
                        variable=self.use_naver).grid(row=1, column=0, sticky="w", padx=5)
        ttk.Checkbutton(crawling_frame, text="ArtStation 검색",
                        variable=self.use_artstation).grid(row=2, column=0, sticky="w", padx=5)

        # 크롤링 상세 옵션
        crawl_options_frame = ttk.Frame(crawling_frame)
        crawl_options_frame.grid(row=0, column=1, rowspan=3, padx=10)

        self.full_resolution = tk.BooleanVar(value=False)
        self.face_search = tk.BooleanVar(value=False)
        self.skip_existing = tk.BooleanVar(value=True)
        self.filter_stock = tk.BooleanVar(value=False)
        self.thread_count = tk.StringVar(value="4")
        self.image_limit = tk.StringVar(value="0")

        ttk.Checkbutton(crawl_options_frame, text="고해상도 이미지 다운로드",
                        variable=self.full_resolution).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(crawl_options_frame, text="얼굴 검색 모드",
                        variable=self.face_search).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(crawl_options_frame, text="기존 파일 건너뛰기",
                        variable=self.skip_existing).grid(row=2, column=0, sticky="w")
        ttk.Checkbutton(crawl_options_frame, text="스톡 이미지 필터링",
                        variable=self.filter_stock).grid(row=3, column=0, sticky="w")

        thread_frame = ttk.Frame(crawl_options_frame)
        thread_frame.grid(row=4, column=0, sticky="w")
        ttk.Label(thread_frame, text="스레드 수:").grid(row=0, column=0)
        ttk.Entry(thread_frame, textvariable=self.thread_count, width=5).grid(row=0, column=1, padx=5)

        limit_frame = ttk.Frame(crawl_options_frame)
        limit_frame.grid(row=5, column=0, sticky="w")
        ttk.Label(limit_frame, text="이미지 제한(0=무제한):").grid(row=0, column=0)
        ttk.Entry(limit_frame, textvariable=self.image_limit, width=5).grid(row=0, column=1, padx=5)

        # 키워드 입력
        keyword_frame = ttk.LabelFrame(crawling_frame, text="검색 키워드", padding=10)
        keyword_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

        self.keyword = tk.StringVar()
        ttk.Entry(keyword_frame, textvariable=self.keyword).grid(row=0, column=0, sticky="ew", padx=5)
        
        # 실행 버튼
        self.run_button = ttk.Button(self.root, text="실행", command=self.run_processor)
        self.run_button.grid(row=7, column=0, pady=10)
        
    def browse_input(self):
        path = filedialog.askdirectory(title="입력 폴더 선택")
        if path:
            self.input_path.set(path)
            
    def browse_output(self):
        path = filedialog.askdirectory(title="출력 폴더 선택")
        if path:
            self.output_path.set(path)
            
    def run_processor(self):
        if not self.validate_inputs():
            return
            
        # 실행 버튼 비활성화
        self.run_button.configure(state="disabled")
        
        # 크롤링 모드인 경우
        if self.mode.get() == "crawl_images":
            thread = threading.Thread(target=self._crawl_in_thread)
            thread.start()
        else:
            # 기존 이미지 처리 로직
            thread = threading.Thread(target=self._process_in_thread)
            thread.start()

    def _process_in_thread(self):
        try:
            # 실행 커맨드 출력
            print("\n=== 실행 커맨드 ===")
            if self.mode.get() == "rename_only":
                print(f"모드: 이름 변경")
                print(f"입력 경로: {self.input_path.get()}")
                print(f"출력 경로: {self.output_path.get()}")
                print(f"번호 매기기: {'예' if self.use_numbering.get() else '아니오'}")
                print(f"접두사 사용: {'예' if self.use_prefix.get() else '아니오'}")
                if self.use_prefix.get():
                    print(f"접두사: {self.prefix.get()}")
                print(f"접미사 사용: {'예' if self.use_suffix.get() else '아니오'}")
                if self.use_suffix.get():
                    print(f"접미사: {self.suffix.get()}")
                print(f"문자열 치환 사용: {'예' if self.use_replace.get() else '아니오'}")
                if self.use_replace.get():
                    print(f"치환: {self.replace_from.get()} → {self.replace_to.get()}")
            elif self.mode.get() == "check_duplicates":
                print(f"모드: 중복 이미지 검사")
                print(f"검사 경로: {self.output_path.get()}")
            else:
                print(f"모드: {self.mode.get()}")
                print(f"입력 경로: {self.input_path.get()}")
                print(f"출력 경로: {self.output_path.get()}")
                print(f"작업자 수: {self.workers.get()}")
                print(f"리사이즈 사용: {'예' if self.resize_enabled.get() else '아니오'}")
                if self.resize_enabled.get():
                    print(f"리사이즈 크기: {self.resize_size.get()}px")
                print(f"패딩 색상: {self.padding_color.get()}")
                print(f"PNG로 저장: {'예' if self.save_as_png.get() else '아니오'}")
            print("==================\n")

            # 기존 처리 로직
            if self.mode.get() == "rename_only":
                processor = ProcessManager(
                    input_path=Path(self.input_path.get()),
                    output_path=Path(self.output_path.get()),
                    mode=ProcessingMode.RENAME_ONLY,
                    use_numbering=self.use_numbering.get(),
                    use_prefix=self.use_prefix.get(),
                    use_suffix=self.use_suffix.get(),
                    prefix=self.prefix.get(),
                    suffix=self.suffix.get(),
                    use_replace=self.use_replace.get(),
                    replace_from=self.replace_from.get(),
                    replace_to=self.replace_to.get()
                )
                processor.process_files()
            elif self.mode.get() == "check_duplicates":
                checker = ImageDuplicateChecker()
                self.progress_tracker = ProgressTracker(100)
                removed_count, removed_files = checker.remove_duplicates(
                    Path(self.output_path.get()), 
                    self.progress_tracker
                )
                self.process_result = (removed_count, removed_files)
                print("\n")  # 진행률 표시 후 새 줄
            else:
                # 이미지 처리 로직에도 이름 변경 옵션 추가
                processor = ProcessManager(
                    input_path=Path(self.input_path.get()),
                    output_path=Path(self.output_path.get()),
                    mode=ProcessingMode(self.mode.get()),
                    max_workers=int(self.workers.get()),
                    resize_size=int(self.resize_size.get()) if self.resize_enabled.get() else None,
                    padding_color=self.padding_color.get(),
                    save_as_png=self.save_as_png.get(),
                    use_numbering=self.use_numbering.get(),
                    use_prefix=self.use_prefix.get(),
                    use_suffix=self.use_suffix.get(),
                    prefix=self.prefix.get(),
                    suffix=self.suffix.get(),
                    use_replace=self.use_replace.get(),
                    replace_from=self.replace_from.get(),
                    replace_to=self.replace_to.get()
                )
                processor.process_files()
                
        except Exception as e:
            self.process_error = str(e)

        # 작업 완료 후 GUI 업데이트
        self.root.after(0, self._process_complete)

    def _process_complete(self):
        # 실행 버튼 다시 활성화
        self.run_button.configure(state="normal")
        
        if hasattr(self, 'process_error'):
            messagebox.showerror("오류", f"처리 중 오류가 발생했습니다:\n{self.process_error}")
            del self.process_error
        elif hasattr(self, 'process_result'):
            if self.mode.get() == "check_duplicates":
                removed_count, removed_files = self.process_result
                if removed_count == 0:
                    messagebox.showinfo("완료", "중복된 이미지가 없습니다.")
                else:
                    messagebox.showinfo("완료", f"총 {removed_count}개의 중복 파일이 제거되었습니다.")
                del self.process_result
        else:
            messagebox.showinfo("완료", "작업이 완료되었습니다!")

    def validate_inputs(self) -> bool:
        """
        사용자 입력값을 검증합니다.
        
        Returns:
            bool: 검증 성공 여부
        """
        # 중복 이미지 검사 모드나 텍스트만 생성 모드일 때는 출력 경로만 확인
        if self.mode.get() in ["check_duplicates", "text_only", "rename_only", "crawl_images"]:
            if not self.output_path.get().strip():
                messagebox.showerror("오류", "출력 폴더 경로를 지정해주세요.")
                return False
            if not Path(self.output_path.get()).exists():
                messagebox.showerror("오류", "출력 폴더가 존재하지 않습니다.")
                return False
            return True

        # 이미지 처리 모드일 때는 모든 필수 입력값 확인
        if not self.input_path.get().strip():
            messagebox.showerror("오류", "입력 폴더 경로를 지정해주세요.")
            return False
        
        if not self.output_path.get().strip():
            messagebox.showerror("오류", "출력 폴더 경로를 지정해주세요.")
            return False
        
        if not Path(self.input_path.get()).exists():
            messagebox.showerror("오류", "입력 폴더가 존재하지 않습니다.")
            return False
        
        try:
            workers = int(self.workers.get())
            if workers < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("오류", "작업자 스레드 수는 1 이상의 정수여야 합니다.")
            return False
        
        if self.resize_enabled.get():
            try:
                resize = int(self.resize_size.get())
                if resize not in [512, 1024]:
                    raise ValueError
            except ValueError:
                messagebox.showerror("오류", "리사이즈 크기는 512 또는 1024여야 합니다.")
                return False
            
        return True

    def _crawl_in_thread(self):
        try:
            from AutoCrawler.crawler_main import AutoCrawler
            from AutoCrawler.collect_links import CollectLinks
            
            # 출력 경로 정규화 - 절대 경로로 변환
            output_path = Path(self.output_path.get()).absolute()
            
            # keywords.txt 파일 생성
            keywords_path = output_path / 'keywords.txt'
            keywords_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(keywords_path, 'w', encoding='utf-8') as f:
                f.write(self.keyword.get())
            
            # 현재 작업 디렉토리를 출력 경로로 변경
            os.chdir(str(output_path))
            
            crawler = AutoCrawler(
                skip_already_exist=self.skip_existing.get(),
                n_threads=int(self.thread_count.get()),
                do_google=self.use_google.get(),
                do_naver=self.use_naver.get(),
                do_artstation=self.use_artstation.get(),
                download_path=str(output_path),  # 절대 경로 문자열로 전달
                full_resolution=self.full_resolution.get(),
                face=self.face_search.get(),
                no_gui=False,
                limit=int(self.image_limit.get()),
                filter_stock=self.filter_stock.get()
            )
            
            crawler.do_crawling()
            
        except Exception as e:
            self.process_error = str(e)
            print(f"Error: {e}")  # 에러 메시지 출력
        
        # 작업 완료 후 GUI 업데이트
        self.root.after(0, self._process_complete)

if __name__ == "__main__":
    root = tk.Tk()
    app = LoraPreprocessorGUI(root)
    root.mainloop() 