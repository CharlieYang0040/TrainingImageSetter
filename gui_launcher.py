import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
from pathlib import Path

class LoraPreprocessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LoRA 학습용 이미지 전처리 도구")
        
        # 변수 초기화
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.selected_mode = tk.StringVar(value="copy_and_text")
        self.workers = tk.StringVar(value="4")
        self.debug_mode = tk.BooleanVar()
        self.check_duplicates = tk.BooleanVar()
        
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
        
        modes = [
            ("이미지만 복사", "copy_only"),
            ("이미지 복사 후 텍스트 생성", "copy_and_text"),
            ("텍스트 파일만 생성", "text_only")
        ]
        
        for i, (text, mode) in enumerate(modes):
            ttk.Radiobutton(mode_frame, text=text, value=mode, 
                          variable=self.selected_mode).grid(row=i, column=0, sticky="w")
        
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
        
        ttk.Checkbutton(options_frame, text="디버그 모드", variable=self.debug_mode).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(options_frame, text="중복 이미지 검사", variable=self.check_duplicates).grid(row=2, column=0, sticky="w")
        
        # 실행 버튼
        ttk.Button(self.root, text="실행", command=self.run_processor).grid(row=5, column=0, pady=10)
        
    def browse_input(self):
        path = filedialog.askdirectory(title="입력 폴더 선택")
        if path:
            self.input_path.set(path)
            
    def browse_output(self):
        path = filedialog.askdirectory(title="출력 폴더 선택")
        if path:
            self.output_path.set(path)
            
    def run_processor(self):
        if not self.input_path.get() or not self.output_path.get():
            tk.messagebox.showerror("오류", "입력 경로와 출력 경로를 모두 지정해주세요.")
            return

        mode = self.selected_mode.get()
        
        cmd = ["python", "main.py"]
        cmd.extend([self.input_path.get(), self.output_path.get()])
        cmd.extend(["--mode", mode])
        cmd.extend(["--workers", self.workers.get()])
        
        # 리사이즈 옵션이 활성화된 경우에만 관련 인자 추가
        if self.resize_enabled.get():
            cmd.extend(["--resize", self.resize_size.get()])
            cmd.extend(["--padding-color", self.padding_color.get()])
            if self.save_as_png.get():
                cmd.append("--save-as-png")
        
        if self.debug_mode.get():
            cmd.append("--debug")
            
        if self.check_duplicates.get():
            cmd.append("--check-duplicates")
            
        # 명령어 실행
        try:
            subprocess.run(cmd, check=True)
            tk.messagebox.showinfo("완료", "처리가 완료되었습니다.")
        except subprocess.CalledProcessError as e:
            tk.messagebox.showerror("오류", f"처리 중 오류가 발생했습니다.\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LoraPreprocessorGUI(root)
    root.mainloop() 