"""
Qwen Multimodal Assistant
==========================
GUI с 4 панелями: Vision, Coder, Audio, Tools + Workflows.

Запуск: python app.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from pathlib import Path
import pyautogui
import json

from models_manager import Qwen25VL, Qwen3Coder, Qwen2Audio
from src.infrastructure.tools import TOOLS
from src.infrastructure.prompts import get_vision_prompt, get_audio_prompt, get_coder_prompt, WORKFLOWS
from src.infrastructure.workflows import parse_coordinates, parse_json_response


class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#1a1a2e", height=30)
        self.pack(fill="x", side="bottom")
        self.label = tk.Label(self, text="Initializing...", font=("Consolas", 10), fg="#888", bg="#1a1a2e", anchor="w")
        self.label.pack(side="left", padx=10, pady=5)
        self.spinner = ttk.Progressbar(self, mode="indeterminate", length=100)

    def set(self, text, color="#888"):
        self.label.config(text=text, fg=color)

    def busy(self):
        self.spinner.pack(side="right", padx=10)
        self.spinner.start(10)

    def idle(self):
        self.spinner.stop()
        self.spinner.pack_forget()


class ModelPanel(tk.Frame):
    """Базовая панель модели"""
    def __init__(self, parent, title, color, icon):
        super().__init__(parent, bg="#16213e", relief="groove", bd=1)
        self.color = color
        header = tk.Frame(self, bg="#0f0f23")
        header.pack(fill="x")
        tk.Label(header, text=f"{icon} {title}", font=("Arial", 13, "bold"), fg=color, bg="#0f0f23").pack(pady=8, padx=10, side="left")
        self.status = tk.Label(header, text="○ Loading", font=("Consolas", 9), fg="#555", bg="#0f0f23")
        self.status.pack(side="right", padx=10)
        self.content = tk.Frame(self, bg="#16213e")
        self.content.pack(fill="both", expand=True, padx=10, pady=5)
        self.output = scrolledtext.ScrolledText(self.content, height=8, font=("Consolas", 10), bg="#0a0a15", fg="#d4d4d4", state="disabled", wrap="word")
        self.output.pack(fill="both", expand=True)
        input_row = tk.Frame(self, bg="#16213e")
        input_row.pack(fill="x", padx=10, pady=(5, 10))
        self.input = tk.Entry(input_row, font=("Arial", 11), bg="#0f0f23", fg="#fff")
        self.input.pack(side="left", fill="x", expand=True)
        self.btn = tk.Button(input_row, text="▶", font=("Arial", 10, "bold"), bg=color, fg="#000", width=3)
        self.btn.pack(side="left", padx=(5, 0))

    def log(self, text):
        self.output.config(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state="disabled")

    def set_status(self, text, color):
        self.status.config(text=text, fg=color)


class VisionPanel(ModelPanel):
    """Vision — анализ экрана"""
    def __init__(self, parent, app):
        super().__init__(parent, "VISION", "#00d9ff", "📷")
        self.app = app
        self.model = None
        row = tk.Frame(self, bg="#16213e")
        row.pack(fill="x", padx=10, pady=(0, 5))
        tk.Button(row, text="📸 Capture", font=("Arial", 9), command=self.capture).pack(side="left")
        tk.Button(row, text="📁 Browse", font=("Arial", 9), command=self.browse).pack(side="left", padx=(5, 0))
        self.task_var = tk.StringVar(value="ui_analysis")
        tasks = ["ui_analysis", "find_element", "ocr_text", "document", "game_navigation", "error_detection"]
        task_combo = ttk.Combobox(row, textvariable=self.task_var, values=tasks, width=15, state="readonly")
        task_combo.pack(side="left", padx=5)
        self.path_var = tk.StringVar()
        tk.Label(row, textvariable=self.path_var, font=("Consolas", 9), fg="#666", bg="#16213e").pack(side="left", padx=10)
        self.btn.config(command=self.run_task)
        self.input.bind("<Return>", lambda e: self.run_task())

    def capture(self):
        path = "temp_screen.png"
        pyautogui.screenshot().save(path)
        self.path_var.set("captured")
        self.input.delete(0, tk.END)
        self.input.insert(0, path)
        self.log("[Screen captured]")

    def browse(self):
        path = filedialog.askopenfilename(title="Select Image", filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All", "*.*")])
        if path:
            self.path_var.set(Path(path).name)
            self.input.delete(0, tk.END)
            self.input.insert(0, path)

    def run_task(self):
        if not self.model:
            self.log("[ERROR] Model not loaded"); return
        path = self.input.get().strip()
        if not path:
            self.log("[ERROR] Enter image path"); return
        task = self.task_var.get()
        self.set_status("◉ Analyzing", "#ffff00")
        def task_thread():
            try:
                self.log(f"\n[{task}] Analyzing: {path}"); self.log("-" * 40)
                prompt = get_vision_prompt(task)
                result = self.model.describe_image(path, prompt)
                self.log(result[:2000])
                coords = parse_coordinates(result)
                if coords:
                    self.log(f"\n[COORDINATES FOUND: {coords}]")
                self.log("-" * 40); self.set_status("● Ready", "#00ff00")
            except Exception as e:
                self.log(f"[ERROR] {e}"); self.set_status("● Error", "#ff4444")
        threading.Thread(target=task_thread, daemon=True).start()


class CoderPanel(ModelPanel):
    """Coder — генерация и анализ кода"""
    def __init__(self, parent, app):
        super().__init__(parent, "CODER", "#00ff88", "💻")
        self.app = app
        row = tk.Frame(self, bg="#16213e")
        row.pack(fill="x", padx=10, pady=(0, 5))
        self.task_var = tk.StringVar(value="generate")
        for task in ["Generate", "Explain", "Debug", "Optimize", "Review"]:
            tk.Button(row, text=task, font=("Arial", 9), command=lambda t=task.lower(): self.use_template(t)).pack(side="left", padx=2)
        tk.Button(row, text="📁 File", font=("Arial", 9), command=self.load_file).pack(side="right")
        self.btn.config(command=self.run_task)
        self.input.bind("<Return>", lambda e: self.run_task())

    def use_template(self, task):
        self.task_var.set(task)
        templates = {"generate": "Write Python code that: ", "explain": "Explain this code:\n", "debug": "Fix errors in:\n", "optimize": "Optimize this code:\n", "review": "Review this code:\n"}
        self.input.delete(0, tk.END)
        self.input.insert(0, templates.get(task, ""))

    def load_file(self):
        path = filedialog.askopenfilename(title="Open Code", filetypes=[("Python", "*.py"), ("All", "*.*")])
        if path:
            try:
                content = Path(path).read_text(encoding="utf-8", errors="ignore")[:2000]
                self.input.delete(0, tk.END)
                self.input.insert(0, f"Explain this code:\n{content}")
                self.log(f"[Loaded: {Path(path).name}]")
            except Exception as e:
                self.log(f"[ERROR] {e}")

    def run_task(self):
        if not self.app.coder:
            self.log("[ERROR] Model not loaded"); return
        text = self.input.get().strip()
        if not text:
            self.log("[ERROR] Enter prompt"); return
        task = self.task_var.get()
        self.set_status("◉ Thinking", "#ffff00")
        def task_thread():
            try:
                self.log(f"\n[{task}] Processing..."); self.log("-" * 40)
                prompt = get_coder_prompt(task, code=text, task=text, error="")
                result = self.app.coder.generate(prompt, max_new_tokens=2500)
                self.log(result[:3000]); self.log("-" * 40)
                self.set_status("● Ready", "#00ff00")
            except Exception as e:
                self.log(f"[ERROR] {e}"); self.set_status("● Error", "#ff4444")
        threading.Thread(target=task_thread, daemon=True).start()


class AudioPanel(ModelPanel):
    """Audio — транскрипция и голосовое управление"""
    def __init__(self, parent, app):
        super().__init__(parent, "AUDIO", "#ff6600", "🔊")
        self.app = app
        self.model = None
        row = tk.Frame(self, bg="#16213e")
        row.pack(fill="x", padx=10, pady=(0, 5))
        tk.Button(row, text="📁 Browse", font=("Arial", 9), command=self.browse).pack(side="left")
        self.task_var = tk.StringVar(value="transcribe")
        for mode, label in [("transcribe", "Transcribe"), ("intent", "Intent"), ("summarize", "Summarize")]:
            tk.Radiobutton(row, text=label, variable=self.task_var, value=mode, fg="#ff6600", bg="#16213e", selectcolor="#0f0f23").pack(side="left", padx=5)
        self.path_var = tk.StringVar()
        tk.Label(row, textvariable=self.path_var, font=("Consolas", 9), fg="#666", bg="#16213e").pack(side="left", padx=10)
        self.btn.config(command=self.run_task)
        self.input.bind("<Return>", lambda e: self.run_task())

    def browse(self):
        path = filedialog.askopenfilename(title="Select Audio", filetypes=[("Audio", "*.wav *.mp3 *.m4a"), ("All", "*.*")])
        if path:
            self.path_var.set(Path(path).name)
            self.input.delete(0, tk.END)
            self.input.insert(0, path)

    def run_task(self):
        if not self.app.audio:
            self.log("[ERROR] Model not loaded"); return
        path = self.input.get().strip()
        if not path:
            self.log("[ERROR] Enter audio path"); return
        task = self.task_var.get()
        self.set_status("◉ Processing", "#ffff00")
        def task_thread():
            try:
                self.log(f"\n[{task}] Processing: {path}"); self.log("-" * 40)
                prompt = get_audio_prompt(task)
                result = self.app.audio.analyze_audio(path, prompt)
                self.log(result[:2000])
                json_data = parse_json_response(result)
                if json_data:
                    self.log(f"\n[JSON PARSED: {json_data}]")
                self.log("-" * 40); self.set_status("● Ready", "#00ff00")
            except Exception as e:
                self.log(f"[ERROR] {e}"); self.set_status("● Error", "#ff4444")
        threading.Thread(target=task_thread, daemon=True).start()


class ToolsPanel(tk.Frame):
    """Панель инструментов"""
    def __init__(self, parent):
        super().__init__(parent, bg="#16213e", relief="groove", bd=1)
        header = tk.Frame(self, bg="#0f0f23")
        header.pack(fill="x")
        tk.Label(header, text="🔧 TOOLS", font=("Arial", 13, "bold"), fg="#00ffff", bg="#0f0f23").pack(pady=8, padx=10)
        self.content = tk.Frame(self, bg="#16213e")
        self.content.pack(fill="both", expand=True, padx=10, pady=5)
        self.output = scrolledtext.ScrolledText(self.content, height=5, font=("Consolas", 9), bg="#0a0a15", fg="#aaa", state="disabled")
        self.output.pack(fill="both")
        input_row = tk.Frame(self, bg="#16213e")
        input_row.pack(fill="x", padx=10, pady=(5, 10))
        self.input = tk.Entry(input_row, font=("Consolas", 10), bg="#0f0f23", fg="#fff")
        self.input.pack(side="left", fill="x", expand=True)
        self.input.bind("<Return>", lambda e: self.run_tool())
        tk.Button(input_row, text="Run", font=("Arial", 10, "bold"), bg="#00ffff", fg="#000", command=self.run_tool).pack(side="left", padx=(5, 0))

    def log(self, text):
        self.output.config(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state="disabled")

    def run_tool(self):
        cmd = self.input.get().strip()
        if not cmd:
            return
        self.log(f"\n> {cmd}")
        if cmd == "help":
            self.log("\n" + TOOLS.help()); return
        parts = cmd.split(maxsplit=1)
        tool_name = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        try:
            if tool_name in ("capture_screen", "screen_info", "db_list", "mouse_position", "timestamp", "echo", "window_info"):
                result = TOOLS.execute(tool_name)
            elif tool_name in ("file_read", "file_list", "file_glob", "capture_region", "ocr", "ocr_boxes"):
                result = TOOLS.execute(tool_name, path=args)
            elif tool_name in ("db_store", "db_get", "db_search"):
                k, v = (args.split(maxsplit=1) + [""])[:2]
                result = TOOLS.execute(tool_name, key=k, value=v)
            elif tool_name in ("mouse_click",):
                coords = args.split()
                if len(coords) >= 2:
                    result = TOOLS.execute(tool_name, x=int(coords[0]), y=int(coords[1]))
                else:
                    result = TOOLS.execute(tool_name)
            elif tool_name in ("file_write",):
                p, rest = args.split(maxsplit=1)
                result = TOOLS.execute(tool_name, path=p, content=rest)
            elif tool_name in ("sys_info",):
                result = TOOLS.execute("system_info", info=args or "all")
            elif tool_name in ("keyboard_type", "shell", "wait"):
                result = TOOLS.execute(tool_name, command=args) if tool_name == "shell" else TOOLS.execute(tool_name, text=args)
            else:
                result = TOOLS.execute(tool_name, path=args)
        except Exception as e:
            result = f"ERROR: {e}"
        self.log(result[:500])


class WorkflowPanel(tk.Frame):
    """Панель workflow"""
    def __init__(self, parent, app):
        super().__init__(parent, bg="#16213e", relief="groove", bd=1)
        self.app = app
        header = tk.Frame(self, bg="#0f0f23")
        header.pack(fill="x")
        tk.Label(header, text="⚡ WORKFLOWS", font=("Arial", 13, "bold"), fg="#ffff00", bg="#0f0f23").pack(pady=8, padx=10)
        self.content = tk.Frame(self, bg="#16213e")
        self.content.pack(fill="both", expand=True, padx=10, pady=5)
        self.output = scrolledtext.ScrolledText(self.content, height=5, font=("Consolas", 9), bg="#0a0a15", fg="#aaa", state="disabled")
        self.output.pack(fill="both")
        row = tk.Frame(self, bg="#16213e")
        row.pack(fill="x", padx=10, pady=(5, 10))
        self.workflow_var = tk.StringVar()
        workflow_combo = ttk.Combobox(row, textvariable=self.workflow_var, values=list(WORKFLOWS.keys()), width=20, state="readonly")
        workflow_combo.pack(side="left")
        workflow_combo.bind("<<ComboboxSelected>>", lambda e: self.select_workflow())
        tk.Button(row, text="▶ Run Workflow", font=("Arial", 10, "bold"), bg="#ffff00", fg="#000", command=self.run_workflow).pack(side="left", padx=(5, 0))
        self.workflow_info = tk.StringVar(value="Select workflow to see description")
        tk.Label(row, textvariable=self.workflow_info, font=("Consolas", 8), fg="#666", bg="#16213e").pack(side="left", padx=10)

    def log(self, text):
        self.output.config(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state="disabled")

    def select_workflow(self):
        name = self.workflow_var.get()
        if name in WORKFLOWS:
            self.workflow_info.set(WORKFLOWS[name]["description"])

    def run_workflow(self):
        name = self.workflow_var.get()
        if not name:
            self.log("[ERROR] Select workflow first"); return
        self.log(f"\n[Starting: {name}]"); self.log("-" * 40)
        if name == "screen_to_action":
            self.run_screen_navigation()
        elif name == "voice_control":
            self.run_voice_action()
        elif name == "document_processing":
            self.run_document()
        elif name == "code_review":
            self.run_code_review()

    def run_screen_navigation(self):
        try:
            path = "temp_screen.png"
            pyautogui.screenshot().save(path)
            self.log(f"[Captured: {path}]")
            if self.app.vision:
                result = self.app.vision.describe_image(path, "Find the primary action button. Return coordinates in format: <box>x1,y1,x2,y2</box>")
                self.log(f"[Vision]: {result[:200]}")
                coords = parse_coordinates(result)
                if coords and len(coords) == 4:
                    x, y = (coords[0] + coords[2]) // 2, (coords[1] + coords[3]) // 2
                    self.log(f"[Clicking: {x}, {y}]")
                    pyautogui.click(x, y)
                    self.log("[SUCCESS] Click executed")
                else:
                    self.log("[ERROR] No coordinates found")
        except Exception as e:
            self.log(f"[ERROR] {e}")

    def run_voice_action(self):
        self.log("[Voice workflow - record audio first]")

    def run_document(self):
        path = filedialog.askopenfilename(title="Select Document", filetypes=[("Images", "*.png *.jpg *.pdf"), ("All", "*.*")])
        if path and self.app.vision:
            try:
                self.log(f"[Processing: {path}]")
                result = self.app.vision.describe_image(path, "Extract text and key-value pairs.")
                self.log(f"[Result]: {result[:500]}")
                TOOLS.execute("db_store", key="document", value=result)
                self.log("[Saved to database]")
            except Exception as e:
                self.log(f"[ERROR] {e}")

    def run_code_review(self):
        path = filedialog.askopenfilename(title="Select Code", filetypes=[("Python", "*.py"), ("All", "*.*")])
        if path and self.app.coder:
            try:
                code = Path(path).read_text(encoding="utf-8", errors="ignore")[:2000]
                self.log(f"[Reviewing: {path}]")
                prompt = get_coder_prompt("review", code=code, task="", error="")
                result = self.app.coder.generate(prompt, max_new_tokens=2000)
                self.log(f"[Review]: {result[:1000]}")
            except Exception as e:
                self.log(f"[ERROR] {e}")


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Qwen Multimodal Assistant")
        self.root.geometry("1300x900")
        self.root.configure(bg="#0a0a15")
        self.vision = None
        self.coder = None
        self.audio = None
        self.setup_ui()
        self.load_models()

    def setup_ui(self):
        title = tk.Frame(self.root, bg="#0f0f23", height=55)
        title.pack(fill="x")
        tk.Label(title, text="◈ Qwen Multimodal Assistant", font=("Arial", 20, "bold"), fg="#00d9ff", bg="#0f0f23").pack(pady=12)
        main = tk.Frame(self.root, bg="#0a0a15")
        main.pack(fill="both", expand=True, padx=10, pady=10)
        left = tk.Frame(main, bg="#0a0a15")
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.vision_panel = VisionPanel(left, self)
        self.vision_panel.pack(fill="both", expand=True, pady=(0, 5))
        self.tools_panel = ToolsPanel(left)
        self.tools_panel.pack(fill="x", pady=(5, 0))
        right = tk.Frame(main, bg="#0a0a15")
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.coder_panel = CoderPanel(right, self)
        self.coder_panel.pack(fill="both", expand=True, pady=(0, 5))
        self.audio_panel = AudioPanel(right, self)
        self.audio_panel.pack(fill="both", expand=True, pady=(5, 0))
        bottom = tk.Frame(main, bg="#0a0a15")
        bottom.pack(fill="x", pady=(5, 0))
        self.workflow_panel = WorkflowPanel(bottom, self)
        self.workflow_panel.pack(fill="x")
        self.status = StatusBar(self.root)

    def load_models(self):
        self.status.set("Loading models...", "#ffff00")
        self.status.busy()
        def load():
            try:
                self.root.after(0, lambda: self.vision_panel.set_status("◉ Loading", "#ffff00"))
                self.vision = Qwen25VL(device="cuda:0")
                self.vision.load()
                self.root.after(0, lambda: self.vision_panel.set_status("● Loaded", "#00ff00"))
                self.root.after(0, lambda: self.vision_panel.log("[OK] Qwen2.5-VL ready"))
            except Exception as e:
                self.root.after(0, lambda: self.vision_panel.set_status("● Error", "#ff4444"))
                self.root.after(0, lambda: self.vision_panel.log(f"[ERROR] {e}"))
            try:
                self.root.after(0, lambda: self.coder_panel.set_status("◉ Loading", "#ffff00"))
                self.coder = Qwen3Coder(device="cpu")
                self.coder.load()
                self.root.after(0, lambda: self.coder_panel.set_status("● Loaded", "#00ff00"))
                self.root.after(0, lambda: self.coder_panel.log("[OK] Qwen3-Coder ready"))
            except Exception as e:
                self.root.after(0, lambda: self.coder_panel.set_status("● Error", "#ff4444"))
                self.root.after(0, lambda: self.coder_panel.log(f"[ERROR] {e}"))
            try:
                self.root.after(0, lambda: self.audio_panel.set_status("◉ Loading", "#ffff00"))
                self.audio = Qwen2Audio(device="cuda:0")
                self.audio.load()
                self.root.after(0, lambda: self.audio_panel.set_status("● Loaded", "#00ff00"))
                self.root.after(0, lambda: self.audio_panel.log("[OK] Qwen2-Audio ready"))
            except Exception as e:
                self.root.after(0, lambda: self.audio_panel.set_status("● Error", "#ff4444"))
                self.root.after(0, lambda: self.audio_panel.log(f"[ERROR] {e}"))
            self.root.after(0, lambda: self.status.set("✓ All systems ready", "#00ff00"))
            self.root.after(0, lambda: self.status.idle())
        threading.Thread(target=load, daemon=True).start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
