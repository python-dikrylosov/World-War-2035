"""
Tools - 27 инструментов для автоматизации
"""
import pyautogui
import os
import json
import glob
import subprocess
import platform
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class ToolRegistry:
    """Реестр инструментов"""
    _tools = {}
    
    @classmethod
    def register(cls, name: str):
        def decorator(func):
            cls._tools[name] = func
            return func
        return decorator
    
    @classmethod
    def execute(cls, name: str, **kwargs) -> Any:
        if name not in cls._tools:
            raise ValueError(f"Unknown tool: {name}")
        return cls._tools[name](**kwargs)
    
    @classmethod
    def list_tools(cls) -> List[str]:
        return list(cls._tools.keys())


# === SCREEN TOOLS ===
@ToolRegistry.register("capture_screen")
def capture_screen() -> str:
    """Сделать скриншот всего экрана"""
    filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    return filename

@ToolRegistry.register("capture_region")
def capture_region(x: int, y: int, width: int, height: int) -> str:
    """Сделать скриншот области"""
    filename = f"temp_region_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    screenshot.save(filename)
    return filename

@ToolRegistry.register("screen_info")
def screen_info() -> Dict[str, int]:
    """Информация о экране"""
    return {
        "width": pyautogui.size().width,
        "height": pyautogui.size().height
    }


# === MOUSE TOOLS ===
@ToolRegistry.register("mouse_click")
def mouse_click(x: int, y: int, button: str = "left") -> str:
    """Клик мышью"""
    pyautogui.click(x, y, button=button)
    return f"Clicked at ({x}, {y}) with {button} button"

@ToolRegistry.register("mouse_scroll")
def mouse_scroll(clicks: int, x: int = None, y: int = None) -> str:
    """Прокрутка колеса"""
    pyautogui.scroll(clicks, x, y)
    return f"Scrolled {clicks} clicks"

@ToolRegistry.register("mouse_position")
def mouse_position() -> Dict[str, int]:
    """Позиция мыши"""
    pos = pyautogui.position()
    return {"x": pos.x, "y": pos.y}


# === KEYBOARD TOOLS ===
@ToolRegistry.register("keyboard_type")
def keyboard_type(text: str) -> str:
    """Напечатать текст"""
    pyautogui.write(text, interval=0.1)
    return f"Typed: {text}"

@ToolRegistry.register("keyboard_press")
def keyboard_press(key: str) -> str:
    """Нажать клавишу"""
    pyautogui.press(key)
    return f"Pressed: {key}"

@ToolRegistry.register("keyboard_write")
def keyboard_write(text: str) -> str:
    """Быстрый ввод текста"""
    pyautogui.write(text)
    return f"Wrote: {text}"


# === FILE TOOLS ===
@ToolRegistry.register("file_read")
def file_read(path: str) -> str:
    """Читать файл"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

@ToolRegistry.register("file_write")
def file_write(path: str, content: str) -> str:
    """Записать в файл"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"Written to {path}"

@ToolRegistry.register("file_list")
def file_list(directory: str = ".") -> List[str]:
    """Список файлов"""
    return os.listdir(directory)

@ToolRegistry.register("file_glob")
def file_glob(pattern: str) -> List[str]:
    """Поиск по шаблону"""
    return glob.glob(pattern)


# === DATABASE TOOLS ===
DB_PATH = "data/knowledge.json"

def _load_db() -> Dict:
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    return {}

def _save_db(data: Dict):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)

@ToolRegistry.register("db_store")
def db_store(key: str, value: Any) -> str:
    """Сохранить в базу знаний"""
    db = _load_db()
    db[key] = value
    _save_db(db)
    return f"Stored '{key}'"

@ToolRegistry.register("db_get")
def db_get(key: str) -> Any:
    """Получить из базы знаний"""
    db = _load_db()
    return db.get(key)

@ToolRegistry.register("db_search")
def db_search(query: str) -> List[Dict]:
    """Поиск в базе знаний"""
    db = _load_db()
    results = []
    for key, value in db.items():
        if query.lower() in key.lower() or query.lower() in str(value).lower():
            results.append({"key": key, "value": value})
    return results

@ToolRegistry.register("db_list")
def db_list() -> List[str]:
    """Список ключей"""
    return list(_load_db().keys())


# === OCR TOOLS ===
@ToolRegistry.register("ocr")
def ocr(image_path: str) -> str:
    """Распознать текст на изображении"""
    if not TESSERACT_AVAILABLE:
        return "Tesseract not available"
    try:
        from PIL import Image
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"OCR error: {e}"

@ToolRegistry.register("ocr_boxes")
def ocr_boxes(image_path: str) -> List[Dict]:
    """Распознать текст с координатами"""
    if not TESSERACT_AVAILABLE:
        return []
    try:
        from PIL import Image
        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        boxes = []
        for i in range(len(data['text'])):
            if data['text'][i].strip():
                boxes.append({
                    "text": data['text'][i],
                    "x": data['left'][i],
                    "y": data['top'][i],
                    "width": data['width'][i],
                    "height": data['height'][i]
                })
        return boxes
    except Exception as e:
        return []


# === OPENCV TOOLS ===
@ToolRegistry.register("cv_template")
def cv_template(image_path: str, template_path: str, threshold: float = 0.8) -> List[Dict]:
    """Найти шаблон на изображении"""
    if not OPENCV_AVAILABLE:
        return []
    try:
        img = cv2.imread(image_path)
        template = cv2.imread(template_path)
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        matches = []
        for pt in zip(*locations[::-1]):
            matches.append({"x": pt[0], "y": pt[1], "confidence": float(result[pt])})
        return matches
    except Exception as e:
        return []

@ToolRegistry.register("cv_detect")
def cv_detect(image_path: str, cascade: str = "haarcascade_frontalface_default.xml") -> List[Dict]:
    """Обнаружить объекты"""
    if not OPENCV_AVAILABLE:
        return []
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        classifier = cv2.CascadeClassifier(cv2.data.__file__.replace("__init__.py", cascade))
        objects = classifier.detectMultiScale(gray, 1.1, 4)
        return [{"x": x, "y": y, "w": w, "h": h} for (x, y, w, h) in objects]
    except Exception as e:
        return []

@ToolRegistry.register("cv_roi")
def cv_roi(image_path: str, x: int, y: int, w: int, h: int) -> str:
    """Вырезать область"""
    if not OPENCV_AVAILABLE:
        return ""
    try:
        img = cv2.imread(image_path)
        roi = img[y:y+h, x:x+w]
        filename = f"temp_roi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(filename, roi)
        return filename
    except Exception as e:
        return f"Error: {e}"


# === SYSTEM TOOLS ===
@ToolRegistry.register("shell")
def shell(command: str) -> str:
    """Выполнить команду в shell"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

@ToolRegistry.register("system_info")
def system_info() -> Dict[str, Any]:
    """Информация о системе"""
    info = {
        "platform": platform.system(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }
    if PSUTIL_AVAILABLE:
        info["cpu_count"] = psutil.cpu_count()
        info["memory_total"] = psutil.virtual_memory().total
    return info

@ToolRegistry.register("window_info")
def window_info() -> List[Dict]:
    """Информация об окнах"""
    try:
        import pygetwindow as gw
        windows = gw.getAllWindows()
        return [{"title": w.title, "left": w.left, "top": w.top, "width": w.width, "height": w.height} for w in windows]
    except ImportError:
        return []


# === UTILITY TOOLS ===
@ToolRegistry.register("wait")
def wait(seconds: float) -> str:
    """Пауза"""
    time.sleep(seconds)
    return f"Waited {seconds} seconds"

@ToolRegistry.register("timestamp")
def timestamp() -> str:
    """Текущее время"""
    return datetime.now().isoformat()

@ToolRegistry.register("echo")
def echo(message: str) -> str:
    """Вернуть сообщение"""
    return message
