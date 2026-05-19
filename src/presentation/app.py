"""
GUI Application - tkinter интерфейс с 4 панелями
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from PIL import Image, ImageTk
import os
import json
from typing import Optional


class MainWindow:
    """Главное окно приложения"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Qwen Multimodal Assistant")
        self.root.geometry("1300x900")
        self.root.configure(bg="#1e1e1e")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="#ffffff", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=5)
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#00ff88")
        
        self._create_ui()
        self.status_text = "Ready"
    
    def _create_ui(self):
        """Создание интерфейса"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top row: Vision, Coder, Audio, Tools
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.vision_panel = self._create_vision_panel(top_frame)
        self.vision_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.coder_panel = self._create_coder_panel(top_frame)
        self.coder_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.audio_panel = self._create_audio_panel(top_frame)
        self.audio_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.tools_panel = self._create_tools_panel(top_frame)
        self.tools_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Bottom row: Workflows
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.workflows_panel = self._create_workflows_panel(bottom_frame)
        self.workflows_panel.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text=self.status_text, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _create_vision_panel(self, parent) -> ttk.LabelFrame:
        """Панель VISION"""
        panel = ttk.LabelFrame(parent, text="📷 VISION", padding="10")
        
        # Buttons
        btn_frame = ttk.Frame(panel)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="📸 Capture", command=self._vision_capture).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📁 Load Image", command=self._vision_load).pack(side=tk.LEFT, padx=2)
        
        # Task selector
        task_var = tk.StringVar(value="describe")
        task_combo = ttk.Combobox(btn_frame, textvariable=task_var, values=[
            "describe", "ocr", "analyze_ui", "find_element", "document"
        ], width=15)
        task_combo.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="▶ Run", command=lambda: self._vision_run(task_var.get())).pack(side=tk.LEFT)
        
        # Result area
        result_text = scrolledtext.ScrolledText(panel, height=10, bg="#2d2d2d", fg="#ffffff", font=("Consolas", 9))
        result_text.pack(fill=tk.BOTH, expand=True)
        
        # Image preview
        self.vision_image_label = ttk.Label(panel, text="[No image]")
        self.vision_image_label.pack(pady=5)
        
        return panel
    
    def _create_coder_panel(self, parent) -> ttk.LabelFrame:
        """Панель CODER"""
        panel = ttk.LabelFrame(parent, text="💻 CODER", padding="10")
        
        # Buttons
        btn_frame = ttk.Frame(panel)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        tasks = ["Generate", "Explain", "Debug", "Optimize", "Review"]
        for task in tasks:
            ttk.Button(btn_frame, text=task, command=lambda t=task: self._coder_run(t)).pack(side=tk.LEFT, padx=2)
        
        # Input
        input_text = scrolledtext.ScrolledText(panel, height=5, bg="#2d2d2d", fg="#ffffff", font=("Consolas", 9))
        input_text.pack(fill=tk.X, pady=(0, 10))
        
        # Result
        result_text = scrolledtext.ScrolledText(panel, height=8, bg="#2d2d2d", fg="#ffffff", font=("Consolas", 9))
        result_text.pack(fill=tk.BOTH, expand=True)
        
        return panel
    
    def _create_audio_panel(self, parent) -> ttk.LabelFrame:
        """Панель AUDIO"""
        panel = ttk.LabelFrame(parent, text="🔊 AUDIO", padding="10")
        
        # Buttons
        btn_frame = ttk.Frame(panel)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="📁 Load Audio", command=self._audio_load).pack(side=tk.LEFT, padx=2)
        
        mode_var = tk.StringVar(value="transcribe")
        mode_combo = ttk.Combobox(btn_frame, textvariable=mode_var, values=[
            "transcribe", "intent", "summarize"
        ], width=15)
        mode_combo.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="▶ Process", command=lambda: self._audio_run(mode_var.get())).pack(side=tk.LEFT)
        
        # Result
        result_text = scrolledtext.ScrolledText(panel, height=12, bg="#2d2d2d", fg="#ffffff", font=("Consolas", 9))
        result_text.pack(fill=tk.BOTH, expand=True)
        
        self.audio_file_label = ttk.Label(panel, text="[No audio file]")
        self.audio_file_label.pack(pady=5)
        
        return panel
    
    def _create_tools_panel(self, parent) -> ttk.LabelFrame:
        """Панель TOOLS"""
        panel = ttk.LabelFrame(parent, text="🔧 TOOLS", padding="10")
        
        # Command input
        cmd_frame = ttk.Frame(panel)
        cmd_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(cmd_frame, text="$").pack(side=tk.LEFT)
        cmd_entry = ttk.Entry(cmd_frame, font=("Consolas", 10))
        cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        cmd_entry.bind("<Return>", lambda e: self._tools_execute(cmd_entry.get()))
        
        ttk.Button(cmd_frame, text="Run", command=lambda: self._tools_execute(cmd_entry.get())).pack(side=tk.LEFT)
        ttk.Button(cmd_frame, text="help", command=self._tools_help).pack(side=tk.LEFT, padx=5)
        
        # Output
        output_text = scrolledtext.ScrolledText(panel, height=12, bg="#2d2d2d", fg="#00ff88", font=("Consolas", 9))
        output_text.pack(fill=tk.BOTH, expand=True)
        
        return panel
    
    def _create_workflows_panel(self, parent) -> ttk.LabelFrame:
        """Панель WORKFLOWS"""
        panel = ttk.LabelFrame(parent, text="⚡ WORKFLOWS", padding="10")
        
        # Workflow selector
        sel_frame = ttk.Frame(panel)
        sel_frame.pack(fill=tk.X, pady=(0, 10))
        
        workflow_var = tk.StringVar(value="screen_navigation")
        workflows = ["screen_navigation", "voice_to_action", "document_processing", "code_review"]
        workflow_combo = ttk.Combobox(sel_frame, textvariable=workflow_var, values=workflows, width=25)
        workflow_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(sel_frame, text="▶ Launch", command=lambda: self._workflow_run(workflow_var.get())).pack(side=tk.LEFT)
        ttk.Button(sel_frame, text="📋 List", command=self._workflow_list).pack(side=tk.LEFT, padx=5)
        
        # Output
        output_text = scrolledtext.ScrolledText(panel, height=6, bg="#2d2d2d", fg="#ffffff", font=("Consolas", 9))
        output_text.pack(fill=tk.BOTH, expand=True)
        
        return panel
    
    # === EVENT HANDLERS ===
    
    def _vision_capture(self):
        self._update_status("Capturing screen...")
        # Placeholder - will connect to orchestrator
    
    def _vision_load(self):
        filename = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if filename:
            self._update_status(f"Loaded: {filename}")
    
    def _vision_run(self, task: str):
        self._update_status(f"Running vision task: {task}")
    
    def _coder_run(self, task: str):
        self._update_status(f"Running coder task: {task}")
    
    def _audio_load(self):
        filename = filedialog.askopenfilename(filetypes=[("Audio", "*.wav *.mp3 *.flac")])
        if filename:
            self._update_status(f"Loaded: {filename}")
    
    def _audio_run(self, mode: str):
        self._update_status(f"Running audio mode: {mode}")
    
    def _tools_execute(self, command: str):
        self._update_status(f"Executing: {command}")
    
    def _tools_help(self):
        self._update_status("Available tools: capture_screen, mouse_click, file_read, etc.")
    
    def _workflow_run(self, name: str):
        self._update_status(f"Running workflow: {name}")
    
    def _workflow_list(self):
        self._update_status("Workflows: screen_navigation, voice_to_action, document_processing, code_review")
    
    def _update_status(self, text: str):
        self.status_text = text
        self.status_bar.config(text=text)
    
    def run(self):
        self.root.mainloop()
