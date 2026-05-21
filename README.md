# Qwen Multimodal Assistant - Real-Time Quantum-Enhanced Edition

**Автор:** Крылосов Дмитрий Игоревич

Мультимодальный ассистент на 3 Qwen моделях (Vision + Coder + Audio) с GUI на tkinter, набором инструментов (Tools), рабочими процессами (Workflows), интерактивным обучением, **асинхронной архитектурой реального времени**, **глобальной картой устройств (GNOC)** и поддержкой **квантовых вычислений**.

## 🎯 Возможности

| Модуль | Описание |
|--------|----------|
| 📷 **VISION** | Анализ изображений, скриншотов, OCR, навигация по интерфейсу |
| 💻 **CODER** | Генерация, отладка, ревью и оптимизация кода |
| 🔊 **AUDIO** | Транскрипция, анализ интонаций, голосовое управление |
| 🔧 **TOOLS** | 27 инструментов: мышь, клавиатура, файлы, БД, OCR, OpenCV, система |
| ⚡ **WORKFLOWS** | Готовые сценарии автоматизации |
| 🌍 **GNOC** | Глобальная карта устройств, Neural Swarm (3 AI), анализ сети |
| 🔄 **REAL-TIME** | Асинхронная шина событий, единый контекст, неблокирующий GUI |
| ⚛️ **QUANTUM** | Квантовое ускорение оптимизации, гибридные алгоритмы |

## 🏗️ Архитектура

```
Принцип: Каждая модель делает то, что умеет лучше всего.
Связка: VISION видит → CODER думает → TOOLS делают → AUDIO слушает
Архитектура: Event Bus + Shared Context + Async Orchestrator
Ускорение: Квантовые сопроцессоры для оптимизационных задач
```

### Модели

- **Qwen2.5-VL-7B-Instruct** (GPU) — зрение, анализ изображений
- **Qwen3-Coder-30B-A3B-Instruct** (CPU) — код, логика
- **Qwen2-Audio-7B-Instruct** (GPU) — аудио, транскрипция

### Real-Time Компоненты

- **Event Bus** — асинхронная шина событий (Pub/Sub)
- **Shared Context** — единое хранилище состояния с версионированием
- **Async Orchestrator** — координация моделей без блокировки GUI
- **Realtime Monitor** — панель мониторинга всех событий системы

### GNOC Компоненты

- **WorldMapContext** — глобальная карта с 8+ узлами по миру
- **NeuralSwarmAnalyzer** — рой из 3 нейросетей (Security, Performance, Anomaly)
- **GNOC Dashboard** — веб-интерфейс с картой Leaflet.js и анализом в реальном времени

### Квантовые Компоненты

- **Quantum Optimizer** — квантовое приближённое решение оптимизационных задач
- **Hybrid Solver** — гибридные классическо-квантовые алгоритмы
- **QPU Interface** — интерфейс к квантовым процессорам (IBM Q, Rigetti, IonQ)

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

# Для квантовых вычислений (опционально)
pip install qiskit qiskit-aer qiskit-ibm-runtime pennylane
```

## 🚀 Запуск

```bash
# GUI (графический интерфейс с real-time мониторингом)
python app.py

# GNOC Dashboard (карта мира + 3 AI нейросети для анализа)
python -m src.presentation.gnoc_dashboard
# Откройте браузер: http://localhost:5000

# Или через run.py
python run.py

# CLI режим
python run.py --cli

# Показать конфиг
python run.py --config

# Тесты
python run.py --test

# Квантовый бенчмарк
python run.py --quantum-benchmark
```

## 💻 Требования к железу

| Компонент | Требование |
|-----------|------------|
| GPU | 8+ GB VRAM (для Vision и Audio) |
| RAM | 64 GB (для Coder на CPU) |
| Диск | ~50 GB для моделей |
| **Квантовый** | Доступ к QPU (облачный или локальный) - опционально |

## 📁 Структура проекта

```
PROJECT/
├── app.py                      # Точка входа: запуск GUI
├── run.py                      # Альтернативный запуск с CLI
├── models_manager.py           # Загрузка 3 Qwen моделей
├── requirements.txt            # Зависимости
├── README.md                   # Этот файл
├── REALTIME_ARCHITECTURE.md    # Документация real-time архитектуры
├── QUANTUM_ACCELERATION.md     # Документация квантового ускорения
├── config/
│   └── config.json             # Конфигурация
├── data/
│   └── knowledge.json          # База знаний (авто)
├── src/
│   ├── ai/
│   │   └── neural_swarm_analyzer.py    # Рой из 3 нейросетей для анализа
│   ├── presentation/
│   │   ├── app.py              # GUI: MainWindow
│   │   ├── gnoc_dashboard.py   # Веб-интерфейс GNOC с картой мира
│   │   ├── world_map_controller.py  # Контроллер карты устройств
│   │   └── realtime_monitor.py # Панель мониторинга
│   └── infrastructure/
│       ├── tools.py            # 27 инструментов
│       ├── orchestrator.py     # Координация моделей
│       ├── async_orchestrator.py # Асинхронный оркестратор
│       ├── async_event_bus.py  # Шина событий
│       ├── shared_context.py   # Единый контекст
│       ├── quantum_optimizer.py # Квантовая оптимизация
│       ├── hybrid_solver.py    # Гибридные алгоритмы
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
5. **quantum_optimization** — Задача → Квантовый солвер → Решение
6. **global_network_analysis** — Выбор узла на карте → Анализ 3 AI → Консенсус-отчет

## 🌍 GNOC - Global Neural Operations Center

### Возможности

- **Интерактивная карта мира** с 8+ узлами (NYC, LON, TOK, SYD, MOW, SIN, CAP, RIO)
- **Real-time мониторинг** статуса устройств, нагрузки и безопасности
- **Neural Swarm** - рой из 3 нейросетей для коллективного анализа:
  - NET-SEC-01: Security Analyst
  - PERF-02: Performance Analyst  
  - ANOM-03: Anomaly Detection
- **Консенсус-отчеты** с приоритетными действиями
- **Симуляция активности** сети в реальном времени

### Запуск GNOC

```bash
python -m src.presentation.gnoc_dashboard
# Откройте http://localhost:5000
```

### API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/` | GET | Веб-интерфейс GNOC |
| `/api/snapshot` | GET | Текущее состояние карты |
| `/api/analyze/<node_id>` | POST | Запуск анализа 3 нейросетями |

Подробнее: [GNOC_README.md](GNOC_README.md)

## ⚛️ Квантовое ускорение

### Что ускоряем?

Квантовые вычисления применяются для:

1. **Оптимизация маршрутов** — задача коммивояжёра для навигации по UI
2. **Поиск в базе знаний** — квантовый поиск Гровера для ускорения поиска
3. **Оптимизация гиперпараметров** — подбор оптимальных параметров моделей
4. **Кластеризация данных** — квантовые алгоритмы машинного обучения
5. **Решение CSP** — задачи удовлетворения ограничений для планирования

### Как это работает?

```
Классический подход:
  Задача → CPU/GPU → Решение (O(n²) или хуже)

Гибридный подход:
  Задача → Классическая предобработка → Квантовый сопроцессор → 
  Постобработка → Решение (O(√n) для некоторых задач)
```

### Пример использования

```python
from src.infrastructure.quantum_optimizer import QuantumOptimizer

optimizer = QuantumOptimizer(backend="qasm_simulator")

# Задача коммивояжёра для навигации по элементам UI
route = optimizer.solve_tsp(ui_elements_positions)

# Квантовый поиск в базе знаний
result = optimizer.grover_search(knowledge_base, query)
```

### Поддерживаемые бэкенды

- **qasm_simulator** — локальный симулятор (быстро, для тестов)
- **statevector_simulator** — точный симулятор (медленнее, точнее)
- **ibm_quantum** — реальные квантовые компьютеры IBM (облако)
- **rigetti** — квантовые компьютеры Rigetti (облако)
- **ionq** — квантовые компьютеры IonQ (облако)

### Производительность

| Задача | Классически | Квантово | Ускорение |
|--------|-------------|----------|-----------|
| Поиск в N элементах | O(N) | O(√N) | до 1000x |
| Оптимизация маршрута | O(n!) | O(2^n) | экспоненциальное |
| Кластеризация | O(n²) | O(n log n) | квадратичное |

> **Примечание:** Квантовое ускорение заметно на больших задачах. Для малых задач используется классический режим.

## 🔄 Real-Time Architecture

Подробная документация: [REALTIME_ARCHITECTURE.md](REALTIME_ARCHITECTURE.md)

### Преимущества

✅ **Неблокирующий GUI** — все операции в asyncio executor  
✅ **Единая база знаний** — Shared Context с версионированием  
✅ **Асинхронная коммуникация** — Event Bus с 18 типами событий  
✅ **Real-time мониторинг** — панель с логом событий и статусами  
✅ **4 готовых workflow** — voice_control, screen_to_action, document_processing, auto_navigation  

## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE)

## 🔗 Ссылки на модели

- [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)
- [Qwen3-Coder-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct)
- [Qwen2-Audio-7B-Instruct](https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct)

## 🔗 Квантовые ресурсы

- [Qiskit Documentation](https://qiskit.org/documentation/)
- [IBM Quantum Experience](https://quantum-computing.ibm.com/)
- [PennyLane](https://pennylane.ai/)
- [Rigetti Forest](https://www.rigetti.com/forest)
- [IonQ Cloud](https://ionq.com/cloud)

---

**Технологии:** PyTorch, Transformers, tkinter, pyautogui, OpenCV, pytesseract, **Qiskit**, **PennyLane**, **asyncio**
