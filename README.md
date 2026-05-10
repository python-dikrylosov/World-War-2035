# Python Torch Hugging Face Project

Проект для демонстрации работы с PyTorch и Hugging Face Transformers с постепенным усложнением функционала.

## План разработки

1.  **Этап 1: Базовый цикл**
    *   Инициализация простой модели.
    *   Запуск цикла инференса.
2.  **Этап 2: Чат-бот**
    *   Интеграция диалогового интерфейса.
    *   Контекстная память беседы.
3.  **Этап 3: Анализ экрана**
    *   Захват скриншота.
    *   Генерация текстового описания изображения (Vision-Language Model).

## Требования

*   Python 3.8+
*   PyTorch
*   Transformers (Hugging Face)
*   Gradio (для UI)
*   Pillow / PyAutoGUI (для работы с экраном)

## Установка

```bash
pip install torch transformers accelerate gradio pillow pyautogui
```

## Запуск

```bash
python main.py
```

## Структура проекта

*   `main.py` — основной скрипт приложения.
*   `requirements.txt` — зависимости.
*   `README.md` — документация.