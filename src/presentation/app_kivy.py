"""
Qwen Multimodal Assistant — мультиплатформенная GUI (Kivy)
==========================================================
Аналог tkinter-версии (src/presentation/app.py), но на Kivy:
работает на Windows, macOS, Linux, а также на Android/iOS (buildozer/kivy-ios).

Запуск:            python app_kivy.py
Сборка Android:    buildozer android debug  (см. buildozer.spec)
"""

import threading
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.utils import platform

from models_manager import Qwen25VL, Qwen3Coder, Qwen2Audio


DARK_BG = [0.08, 0.08, 0.12, 1]
PANEL_BG = [0.09, 0.13, 0.24, 1]
OUTPUT_BG = [0.04, 0.04, 0.08, 1]

PANEL_COLORS = {
    "Vision": [0.0, 0.8, 1.0, 1],
    "Coder": [0.0, 1.0, 0.4, 1],
    "Audio": [1.0, 0.6, 0.0, 1],
    "Tools": [1.0, 0.3, 0.6, 1],
}


class LogView(ScrollView):
    """Прокручиваемый лог панели."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bar_width = 12
        self._label = Label(
            size_hint_y=None,
            halign="left",
            valign="top",
            font_size="13sp",
            color=[0.83, 0.83, 0.83, 1],
            background_color=OUTPUT_BG,
        )
        self._label.bind(texture_size=self._label.setter("size"))
        self.add_widget(self._label)

    def log(self, text: str):
        self._label.text += text + "\n"
        Clock.schedule_once(lambda *_: self.scroll_to(self._label, timeout=0))


class ModelPanel(BoxLayout):
    """Универсальная панель модели: заголовок + статус + лог + ввод + кнопка."""

    def __init__(self, title: str, color_key: str, on_run, placeholder: str = "", **kwargs):
        super().__init__(orientation="vertical", spacing=4, padding=6, **kwargs)
        with self.canvas.before:
            Color(*PANEL_BG)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._rect, "pos", self.pos),
                  size=lambda *_: setattr(self._rect, "size", self.size))

        header = BoxLayout(size_hint_y=None, height=32, spacing=4)
        self.title_label = Label(
            text=title, bold=True, font_size="16sp", color=PANEL_COLORS[color_key],
            size_hint_x=0.7, halign="left",
        )
        self.status_label = Label(
            text="○ Loading", font_size="12sp", color=[0.4, 0.4, 0.4, 1], size_hint_x=0.3,
        )
        header.add_widget(self.title_label)
        header.add_widget(self.status_label)
        self.add_widget(header)

        self.log_view = LogView(size_hint_y=1)
        self.add_widget(self.log_view)

        input_row = BoxLayout(size_hint_y=None, height=44, spacing=4)
        self.input = TextInput(
            hint_text=placeholder, multiline=False, font_size="14sp",
            background_color=[0.06, 0.06, 0.13, 1], foreground_color=[1, 1, 1, 1],
        )
        self.btn = Button(
            text="▶ Run", size_hint_x=None, width=100, bold=True,
            background_color=PANEL_COLORS[color_key], color=[0, 0, 0, 1],
        )
        self.btn.bind(on_release=lambda *_: on_run(self.input.text))
        self.input.bind(on_text_validate=lambda *_: on_run(self.input.text))
        input_row.add_widget(self.input)
        input_row.add_widget(self.btn)
        self.add_widget(input_row)

    def set_status(self, text: str, color):
        self.status_label.text = text
        self.status_label.color = color

    def log(self, text: str):
        self.log_view.log(text)


class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=4, padding=6, **kwargs)
        self.vision = None
        self.coder = None
        self.audio = None

        title = Label(
            text="⚡ Qwen Multimodal Assistant (Kivy)",
            size_hint_y=None, height=36, bold=True, font_size="18sp",
            color=[1, 1, 1, 1],
        )
        self.add_widget(title)

        tabs = TabbedPanel(do_default_tab=False, tab_height=40, tab_width=140)
        self.add_widget(tabs)

        for name, placeholder, handler in (
            ("Vision", "Путь к изображению / вопрос…", self.run_vision),
            ("Coder", "Запрос к Qwen3-Coder…", self.run_coder),
            ("Audio", "Путь к аудио…", self.run_audio),
        ):
            item = TabbedPanelItem(text=name)
            panel = ModelPanel(name, name, handler, placeholder)
            setattr(self, f"{name.lower()}_panel", panel)
            item.add_widget(panel)
            tabs.add_widget(item)

        tools_item = TabbedPanelItem(text="Status")
        self.status_panel = ModelPanel("Status", "Tools", lambda _: self.load_models(),
                                       placeholder="")
        tools_item.add_widget(self.status_panel)
        tabs.add_widget(tools_item)

        self.status_bar = Label(
            text="Initializing…", size_hint_y=None, height=26, font_size="12sp",
            color=[0.5, 0.5, 0.5, 1], halign="left",
        )
        self.add_widget(self.status_bar)

    # ---------- Логика ----------

    def _set_status(self, text):
        Clock.schedule_once(lambda *_: setattr(self.status_bar, "text", text))

    def load_models(self):
        device_pref = "cuda:0" if platform == "linux" else "cpu"

        def load():
            try:
                Clock.schedule_once(lambda *_: self.vision_panel.set_status("◉ Loading", [1, 1, 0, 1]))
                self.vision = Qwen25VL(device=device_pref)
                self.vision.load()
                Clock.schedule_once(lambda *_: self.vision_panel.set_status("● Loaded", [0, 1, 0, 1]))
            except Exception as e:
                Clock.schedule_once(lambda *_: self.vision_panel.set_status("● Error", [1, 0.2, 0.2, 1]))
                Clock.schedule_once(lambda *_: self.vision_panel.log(f"[ERROR] {e}"))
            try:
                Clock.schedule_once(lambda *_: self.coder_panel.set_status("◉ Loading", [1, 1, 0, 1]))
                self.coder = Qwen3Coder(device="cpu")
                self.coder.load()
                Clock.schedule_once(lambda *_: self.coder_panel.set_status("● Loaded", [0, 1, 0, 1]))
            except Exception as e:
                Clock.schedule_once(lambda *_: self.coder_panel.set_status("● Error", [1, 0.2, 0.2, 1]))
                Clock.schedule_once(lambda *_: self.coder_panel.log(f"[ERROR] {e}"))
            try:
                Clock.schedule_once(lambda *_: self.audio_panel.set_status("◉ Loading", [1, 1, 0, 1]))
                self.audio = Qwen2Audio(device=device_pref)
                self.audio.load()
                Clock.schedule_once(lambda *_: self.audio_panel.set_status("● Loaded", [0, 1, 0, 1]))
            except Exception as e:
                Clock.schedule_once(lambda *_: self.audio_panel.set_status("● Error", [1, 0.2, 0.2, 1]))
                Clock.schedule_once(lambda *_: self.audio_panel.log(f"[ERROR] {e}"))
            self._set_status("✓ All systems ready")

        self._set_status("Loading models…")
        threading.Thread(target=load, daemon=True).start()

    def _task(self, panel, fn):
        def run():
            try:
                result = fn()
                Clock.schedule_once(lambda *_: panel.log(str(result)))
            except Exception as e:
                Clock.schedule_once(lambda *_: panel.log(f"[ERROR] {e}"))
        threading.Thread(target=run, daemon=True).start()

    def run_vision(self, text):
        if not text.strip():
            return
        panel = self.vision_panel
        panel.log(f"> {text}")
        if not self.vision:
            panel.log("[!] Модель не загружена")
            return
        path = Path(text.split("|")[0].strip())
        prompt = (text.split("|", 1)[1].strip() if "|" in text
                  else "Опиши, что изображено на картинке.")
        if path.exists():
            self._task(panel, lambda: self.vision.describe_image(str(path), prompt))
        else:
            self._task(panel, lambda: self.vision.describe_image(None, prompt))

    def run_coder(self, text):
        if not text.strip():
            return
        panel = self.coder_panel
        panel.log(f"> {text}")
        if not self.coder:
            panel.log("[!] Модель не загружена")
            return
        self._task(panel, lambda: self.coder.generate(text))

    def run_audio(self, text):
        if not text.strip():
            return
        panel = self.audio_panel
        panel.log(f"> {text}")
        if not self.audio:
            panel.log("[!] Модель не загружена")
            return
        path = Path(text.strip())
        if not path.exists():
            panel.log("[!] Файл не найден")
            return
        self._task(panel, lambda: self.audio.transcribe(str(path)))


class QwenKivyApp(App):
    title = "Qwen Multimodal Assistant"

    def build(self):
        screen = MainScreen()
        screen.load_models()
        return screen


def main():
    QwenKivyApp().run()


if __name__ == "__main__":
    main()
