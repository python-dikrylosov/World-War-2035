"""
Realtime Monitor Panel - Панель мониторинга в реальном времени
Отображает события, контекст и статус системы без блокировки GUI
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import threading
from datetime import datetime
from typing import Optional

from .async_event_bus import EventBus, EventType, Event, get_event_bus
from .shared_context import SharedContextManager, get_context_manager


class RealtimeMonitorPanel(tk.Frame):
    """
    Панель мониторинга в реальном времени:
    - Лог событий (Event Log)
    - Текущий контекст (Context View)
    - Статус компонентов (Status Indicators)
    """
    
    def __init__(self, parent, event_bus: Optional[EventBus] = None, context_manager: Optional[SharedContextManager] = None):
        super().__init__(parent, bg="#0f0f23", relief="groove", bd=1)
        
        self.event_bus = event_bus or get_event_bus()
        self.context_manager = context_manager or get_context_manager()
        self.event_count = 0
        
        # Header
        header = tk.Frame(self, bg="#0a0a15")
        header.pack(fill="x")
        tk.Label(header, text="📊 REALTIME MONITOR", font=("Arial", 13, "bold"), fg="#ffff00", bg="#0a0a15").pack(pady=8, padx=10)
        
        # Status indicators
        status_frame = tk.Frame(self, bg="#0f0f23")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_labels = {}
        statuses = [
            ("vision", "Vision", "#00d9ff"),
            ("coder", "Coder", "#00ff88"),
            ("audio", "Audio", "#ff6600"),
            ("tools", "Tools", "#00ffff"),
            ("workflow", "Workflow", "#ffff00")
        ]
        
        for i, (key, name, color) in enumerate(statuses):
            frame = tk.Frame(status_frame, bg="#16213e", relief="flat", bd=1)
            frame.grid(row=0, column=i, padx=5, sticky="ew")
            status_frame.columnconfigure(i, weight=1)
            
            indicator = tk.Canvas(frame, width=12, height=12, bg="#16213e", highlightthickness=0)
            indicator.pack(side="left", padx=5, pady=5)
            self.status_labels[key] = {
                "indicator": indicator,
                "label": tk.Label(frame, text=name, font=("Consolas", 9), fg=color, bg="#16213e")
            }
            self.status_labels[key]["label"].pack(side="left", padx=(0, 5))
            self._set_status(key, "idle")
        
        # Event log
        log_header = tk.Frame(self, bg="#0f0f23")
        log_header.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(log_header, text="Event Log:", font=("Consolas", 10), fg="#888", bg="#0f0f23").pack(anchor="w")
        
        self.event_log = scrolledtext.ScrolledText(
            self, height=8, 
            font=("Consolas", 9), 
            bg="#0a0a15", 
            fg="#d4d4d4", 
            state="disabled"
        )
        self.event_log.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Context preview
        ctx_header = tk.Frame(self, bg="#0f0f23")
        ctx_header.pack(fill="x", padx=10, pady=(5, 0))
        tk.Label(ctx_header, text="Context Preview:", font=("Consolas", 10), fg="#888", bg="#0f0f23").pack(anchor="w")
        
        self.context_preview = scrolledtext.ScrolledText(
            self, height=4, 
            font=("Consolas", 8), 
            bg="#0a0a15", 
            fg="#888", 
            state="disabled"
        )
        self.context_preview.pack(fill="x", padx=10, pady=5)
        
        # Controls
        controls = tk.Frame(self, bg="#0f0f23")
        controls.pack(fill="x", padx=10, pady=5)
        tk.Button(controls, text="Clear Log", font=("Arial", 9), command=self.clear_log).pack(side="left", padx=2)
        tk.Button(controls, text="Refresh Context", font=("Arial", 9), command=self.refresh_context).pack(side="left", padx=2)
        tk.Button(controls, text="Export Events", font=("Arial", 9), command=self.export_events).pack(side="left", padx=2)
        
        # Subscribe to events
        self._subscribe_to_events()
        
        # Start async context updater
        self._start_context_updater()
    
    def _subscribe_to_events(self):
        """Подписаться на все события"""
        self.event_bus.subscribe_all(self._on_event)
    
    def _on_event(self, event: Event):
        """Обработчик событий"""
        self.event_count += 1
        timestamp = event.timestamp.split("T")[1].split(".")[0]
        event_type = event.type.value.split(":")[1].upper()
        source = f"[{event.source}]" if event.source else ""
        
        # Color by type
        color_map = {
            "VISION": "#00d9ff",
            "AUDIO": "#ff6600",
            "CODER": "#00ff88",
            "TOOL": "#00ffff",
            "DB": "#ff88ff",
            "WORKFLOW": "#ffff00",
            "SYSTEM": "#888888"
        }
        category = event.type.value.split(":")[0].upper()
        color = color_map.get(category, "#d4d4d4")
        
        # Update status indicator
        if category.lower() in self.status_labels:
            self._set_status(category.lower(), "active")
            self.after(2000, lambda: self._set_status(category.lower(), "idle"))
        
        # Add to log
        self.event_log.config(state="normal")
        self.event_log.insert(tk.END, f"{timestamp} ", "timestamp")
        self.event_log.insert(tk.END, f"{event_type:<12}", "type")
        self.event_log.insert(tk.END, f"{source:<8}", "source")
        payload_preview = str(event.payload)[:60].replace("\n", " ")
        self.event_log.insert(tk.END, f"{payload_preview}\n")
        self.event_log.see(tk.END)
        self.event_log.config(state="disabled")
        
        # Tags for syntax highlighting
        try:
            self.event_log.tag_config("timestamp", foreground="#555")
            self.event_log.tag_config("type", foreground=color)
            self.event_log.tag_config("source", foreground="#666")
        except:
            pass
    
    def _set_status(self, key: str, status: str):
        """Установить индикатор статуса"""
        indicator = self.status_labels[key]["indicator"]
        colors = {
            "idle": "#333333",
            "active": "#00ff00",
            "busy": "#ffff00",
            "error": "#ff0000"
        }
        indicator.delete("all")
        indicator.create_oval(2, 2, 10, 10, fill=colors.get(status, "#333333"))
    
    def _start_context_updater(self):
        """Запустить асинхронное обновление контекста"""
        async def update_loop():
            while True:
                await self._update_context_preview()
                await asyncio.sleep(2)
        
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(update_loop())
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    async def _update_context_preview(self):
        """Обновить превью контекста"""
        try:
            all_data = await self.context_manager.get_all()
            
            def update_ui():
                self.context_preview.config(state="normal")
                self.context_preview.delete("1.0", tk.END)
                
                if not all_data:
                    self.context_preview.insert(tk.END, "(empty)")
                else:
                    for key, value in list(all_data.items())[-5:]:  # Last 5 entries
                        preview = str(value)[:50].replace("\n", " ")
                        self.context_preview.insert(tk.END, f"{key}: {preview}\n")
                
                self.context_preview.config(state="disabled")
            
            # Update UI in main thread
            self.after(0, update_ui)
        except Exception as e:
            pass
    
    def clear_log(self):
        """Очистить лог"""
        self.event_log.config(state="normal")
        self.event_log.delete("1.0", tk.END)
        self.event_count = 0
        self.event_log.config(state="disabled")
    
    def refresh_context(self):
        """Обновить контекст вручную"""
        asyncio.get_event_loop().call_soon_threadsafe(
            asyncio.ensure_future,
            self._update_context_preview()
        )
    
    def export_events(self):
        """Экспортировать события"""
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            events = self.event_bus.get_history(limit=100)
            import json
            with open(path, 'w') as f:
                json.dump([
                    {
                        "type": e.type.value,
                        "timestamp": e.timestamp,
                        "source": e.source,
                        "payload": e.payload
                    }
                    for e in events
                ], f, indent=2)
