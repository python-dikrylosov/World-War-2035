# Qwen Multimodal Assistant

**Автор:** Крылосов Дмитрий Игоревич

Мультимодальный ассистент на 3 Qwen моделях (Vision + Coder + Audio) с GUI на tkinter, набором инструментов (Tools), рабочими процессами (Workflows) и интерактивным обучением.

## 🎯 Возможности

| Модуль | Описание |
|--------|----------|
| 📷 **VISION** | Анализ изображений, скриншотов, OCR, навигация по интерфейсу |
| 💻 **CODER** | Генерация, отладка, ревью и оптимизация кода |
| 🔊 **AUDIO** | Транскрипция, анализ интонаций, голосовое управление |
| 🔧 **TOOLS** | 27 инструментов: мышь, клавиатура, файлы, БД, OCR, OpenCV, система |
| ⚡ **WORKFLOWS** | Готовые сценарии автоматизации |

## 🏗️ Архитектура

```
Принцип: Каждая модель делает то, что умеет лучше всего.
Связка: VISION видит → CODER думает → TOOLS делают → AUDIO слушает
```

### Модели

- **Qwen2.5-VL-7B-Instruct** (GPU) — зрение, анализ изображений
- **Qwen3-Coder-30B-A3B-Instruct** (CPU) — код, логика
- **Qwen2-Audio-7B-Instruct** (GPU) — аудио, транскрипция

## 📦 Установка

```bash
# Клонировать репозиторий
git clone https://github.com/YOUR_USERNAME/qwen-multimodal-assistant.git
cd qwen-multimodal-assistant

# Установить зависимости
pip install -r requirements.txt

# Дополнительно для OCR
sudo apt-get install tesseract-ocr  # Linux
brew install tesseract              # macOS

# Скачать модели с HuggingFace
# 1. Qwen/Qwen2.5-VL-7B-Instruct (~16 GB)
# 2. Qwen/Qwen3-Coder-30B-A3B-Instruct (~18 GB)
# 3. Qwen/Qwen2-Audio-7B-Instruct (~16 GB)
```

## 🚀 Запуск

```bash
# GUI (графический интерфейс)
python app.py

# Или через run.py
python run.py

# CLI режим
python run.py --cli

# Показать конфиг
python run.py --config

# Тесты
python run.py --test
```

## 💻 Требования к железу

| Компонент | Требование |
|-----------|------------|
| GPU | 8+ GB VRAM (для Vision и Audio) |
| RAM | 64 GB (для Coder на CPU) |
| Диск | ~50 GB для моделей |

## 📁 Структура проекта

```
PROJECT/
├── app.py                      # Точка входа: запуск GUI
├── run.py                      # Альтернативный запуск с CLI
├── models_manager.py           # Загрузка 3 Qwen моделей
├── requirements.txt            # Зависимости
├── config/
│   └── config.json             # Конфигурация
├── data/
│   └── knowledge.json          # База знаний (авто)
├── src/
│   ├── presentation/
│   │   └── app.py              # GUI: MainWindow
│   └── infrastructure/
│       ├── tools.py            # 27 инструментов
│       ├── orchestrator.py     # Координация моделей
│       ├── prompts.py          # Промпты
│       └── workflows.py        # Движок workflows
└── models/                     # Папка для моделей
```

## 🔧 Инструменты (27 шт)

### Screen
- `capture_screen` — скриншот экрана
- `capture_region` — скриншот области
- `screen_info` — информация об экране

### Mouse
- `mouse_click` — клик мышью
- `mouse_scroll` — прокрутка
- `mouse_position` — позиция курсора

### Keyboard
- `keyboard_type` — ввод текста
- `keyboard_press` — нажать клавишу
- `keyboard_write` — быстрый ввод

### Files
- `file_read`, `file_write`, `file_list`, `file_glob`

### Database
- `db_store`, `db_get`, `db_search`, `db_list`

### OCR
- `ocr`, `ocr_boxes` (через pytesseract)

### OpenCV
- `cv_template`, `cv_detect`, `cv_roi`

### System
- `shell`, `system_info`, `window_info`

### Utils
- `wait`, `timestamp`, `echo`

## ⚡ Workflows

Готовые сценарии:

1. **screen_navigation** — Скриншот → Анализ → Клик
2. **voice_to_action** — Аудио → Интент → Действие
3. **document_processing** — Документ → OCR → База
4. **code_review** — Файл → Ревью → Отчёт

## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE)

## 🔗 Ссылки на модели

- [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)
- [Qwen3-Coder-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct)
- [Qwen2-Audio-7B-Instruct](https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct)

---

**Технологии:** PyTorch, Transformers, tkinter, pyautogui, OpenCV, pytesseract
