# Real-Time Architecture Guide

## Обзор

Этот документ описывает архитектуру для работы приложения в **реальном времени** с асинхронной обработкой событий, единой базой знаний и неблокирующим GUI.

## Проблемы оригинальной архитектуры

1. **Синхронные вызовы моделей** - блокируют GUI во время инференса
2. **Разрозненное состояние** - каждая панель хранит своё состояние
3. **Отсутствие коммуникации** - панели не знают о действиях друг друга
4. **Нет истории событий** - невозможно отследить что происходило

## Новая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      GUI (Tkinter)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Vision  │ │  Coder   │ │  Audio   │ │   Monitor    │   │
│  │  Panel   │ │  Panel   │ │  Panel   │ │    Panel     │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │
│       │            │            │              │           │
└───────┼────────────┼────────────┼──────────────┼───────────┘
        │            │            │              │
        ▼            ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Event Bus (Pub/Sub)                       │
│  • Асинхронная шина событий                                 │
│  • Типы: VISION, AUDIO, CODER, TOOL, WORKFLOW, DB          │
│  • История событий                                          │
└─────────────────────────────────────────────────────────────┘
        │            │            │              │
        ▼            ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│              Shared Context Manager                         │
│  • Единое хранилище состояния                               │
│  • Версионирование данных                                   │
│  • Подписка на изменения                                    │
│  • Персистентность (JSON)                                   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│               Async Orchestrator                            │
│  • Координация между моделями                               │
│  • Запуск в executor (не блокирует)                         │
│  • Публикация событий                                       │
│  • Workflows                                                │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Models & Tools                           │
│  Qwen2.5-VL │ Qwen3-Coder │ Qwen2-Audio │ 27 инструментов  │
└─────────────────────────────────────────────────────────────┘
```

## Компоненты

### 1. Event Bus (`async_event_bus.py`)

Асинхронная шина событий типа Publish/Subscribe.

**Ключевые возможности:**
- Подписка на конкретные типы событий или на все события
- Асинхронная рассылка событий подписчикам
- История событий (до 1000 последних)
- Correlation ID для связывания связанных событий

**Пример использования:**
```python
from src.infrastructure.async_event_bus import get_event_bus, EventType, Event

event_bus = get_event_bus()

# Подписка на событие
async def on_vision_analyzed(event):
    print(f"Vision analyzed: {event.payload}")

event_bus.subscribe(EventType.VISION_ANALYZED, on_vision_analyzed)

# Публикация события
await event_bus.publish(Event(
    type=EventType.VISION_ANALYZED,
    payload={"result": "image description"},
    source="orchestrator"
))
```

### 2. Shared Context Manager (`shared_context.py`)

Единое централизованное хранилище состояния приложения.

**Ключевые возможности:**
- Потокобезопасность через `asyncio.Lock`
- Версионирование данных (автоматическое увеличение version)
- Подписка на изменения контекста
- Персистентность (сохранение в JSON)
- Поиск по ключам и значениям

**Пример использования:**
```python
from src.infrastructure.shared_context import get_context_manager

context = get_context_manager()

# Установка значения
await context.set("vision:last_screenshot", {
    "path": "temp_screen.png",
    "analysis": "UI description"
})

# Получение значения
screenshot = await context.get("vision:last_screenshot")

# Поиск
results = await context.search("screenshot")

# Подписка на изменения
async def on_context_change(data):
    print(f"Context changed: {data['key']} = {data['value']}")

context.subscribe(on_context_change)
```

### 3. Async Orchestrator (`async_orchestrator.py`)

Асинхронная версия оркестратора для координации моделей.

**Ключевые возможности:**
- Все методы async (не блокируют GUI)
- Автоматическая публикация событий
- Интеграция с Shared Context
- Запуск синхронных функций в executor

**Пример использования:**
```python
from src.infrastructure.async_orchestrator import AsyncOrchestrator

orchestrator = AsyncOrchestrator(
    vision_model=vision,
    coder_model=coder,
    audio_model=audio,
    tool_registry=tools
)

# Асинхронный анализ изображения
result = await orchestrator.vision_analyze_async("image.png", task="describe")

# Workflow: скриншот → анализ → клик
result = await orchestrator.workflow_screen_to_action_async("button")

# Workflow: голос → транскрипция → действие
result = await orchestrator.workflow_voice_control_async("command.wav")
```

### 4. Realtime Monitor Panel (`realtime_monitor.py`)

Панель мониторинга в реальном времени для GUI.

**Ключевые возможности:**
- Лог всех событий системы
- Индикаторы статуса компонентов
- Превью текущего контекста
- Экспорт событий в JSON

## Интеграция с существующим кодом

### Шаг 1: Обновить `src/presentation/app.py`

Добавить импорт новых компонентов:
```python
from src.infrastructure.async_event_bus import get_event_bus
from src.infrastructure.shared_context import get_context_manager
from src.infrastructure.async_orchestrator import AsyncOrchestrator
from src.presentation.realtime_monitor import RealtimeMonitorPanel
```

### Шаг 2: Создать глобальные компоненты в `MainWindow.__init__`

```python
class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        # ... existing code ...
        
        # Инициализация новых компонентов
        self.event_bus = get_event_bus()
        self.context_manager = get_context_manager()
        self.async_orchestrator = None  # Будет создан после загрузки моделей
```

### Шаг 3: Обновить загрузку моделей

```python
def load_models(self):
    # ... existing code ...
    def load():
        try:
            # Load vision model
            self.vision = Qwen25VL(device="cuda:0")
            self.vision.load()
            
            # Load coder model
            self.coder = Qwen3Coder(device="cpu")
            self.coder.load()
            
            # Load audio model
            self.audio = Qwen2Audio(device="cuda:0")
            self.audio.load()
            
            # Create async orchestrator
            self.async_orchestrator = AsyncOrchestrator(
                vision_model=self.vision,
                coder_model=self.coder,
                audio_model=self.audio,
                tool_registry=TOOLS,
                event_bus=self.event_bus,
                context_manager=self.context_manager
            )
            
            # Update UI
            self.root.after(0, lambda: self.status.set("✓ All systems ready", "#00ff00"))
            self.root.after(0, lambda: self.status.idle())
            
        except Exception as e:
            # ... error handling ...
    
    threading.Thread(target=load, daemon=True).start()
```

### Шаг 4: Добавить панель мониторинга в UI

```python
def setup_ui(self):
    # ... existing code ...
    
    # Add monitor panel at the bottom
    self.monitor_panel = RealtimeMonitorPanel(
        bottom, 
        event_bus=self.event_bus,
        context_manager=self.context_manager
    )
    self.monitor_panel.pack(fill="x", pady=(5, 0))
```

### Шаг 5: Обновить панели для использования async orchestrator

Пример для VisionPanel:
```python
async def run_task_async(self):
    if not self.app.async_orchestrator:
        self.log("[ERROR] Orchestrator not loaded")
        return
    
    path = self.input.get().strip()
    task = self.task_var.get()
    
    try:
        result = await self.app.async_orchestrator.vision_analyze_async(path, task)
        self.log(result[:2000])
    except Exception as e:
        self.log(f"[ERROR] {e}")

def run_task(self):
    # Запуск async функции в отдельном потоке
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_task_async())
    
    threading.Thread(target=run_async, daemon=True).start()
```

## Преимущества новой архитектуры

### 1. Неблокирующий GUI
- Все тяжёлые операции (инференс моделей) выполняются в executor
- GUI остаётся отзывчивым во время любых операций

### 2. Единое состояние
- Все компоненты видят одно и то же состояние
- Версионирование позволяет отслеживать изменения
- Персистентность сохраняет состояние между запусками

### 3. Событийная модель
- Компоненты не зависят друг от друга напрямую
- Легко добавлять новые обработчики событий
- Полная история происходящего в системе

### 4. Масштабируемость
- Легко добавить новые модели или инструменты
- Workflows можно комбинировать
- Поддержка нескольких клиентов (в будущем)

### 5. Отладка и мониторинг
- Realtime Monitor показывает всё происходящее
- Экспорт событий для анализа
- Correlation ID для отслеживания цепочек

## Пример workflow в реальном времени

```
1. Пользователь нажимает "Capture" в Vision Panel
   ↓
2. Публикуется событие: VISION_CAPTURED
   ↓
3. Shared Context обновляется: {"vision:last_screenshot": "temp.png"}
   ↓
4. Realtime Monitor показывает событие в логе
   ↓
5. Orchestrator начинает анализ (асинхронно)
   ↓
6. Публикуется событие: VISION_ANALYZED (started)
   ↓
7. Модель завершает анализ
   ↓
8. Публикуется событие: VISION_ANALYZED (complete)
   ↓
9. Shared Context обновляется с результатом
   ↓
10. Vision Panel получает результат и показывает пользователю
   ↓
11. Другие панели могут реагировать на событие (если подписаны)
```

## Миграция существующего кода

### Минимальные изменения (быстрый старт)

1. Создать Event Bus и Context Manager
2. Обернуть существующие вызовы моделей в `asyncio.to_thread()` или `run_in_executor`
3. Добавить публикацию событий после завершения операций

### Полная миграция (рекомендуется)

1. Переписать все панели на async/await
2. Использовать Async Orchestrator для всех операций
3. Сохранять все результаты в Shared Context
4. Добавить Realtime Monitor для отладки

## Производительность

### Рекомендации

1. **Executor pool size**: Настройте размер пула для CPU-bound операций
   ```python
   import concurrent.futures
   executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
   ```

2. **Event Bus history**: Ограничьте историю для экономии памяти
   ```python
   event_bus._max_history = 500  # вместо 1000
   ```

3. **Context persistence**: Отключите персистентность если не нужна
   ```python
   context = get_context_manager(persist_path=None)
   ```

4. **Batch events**: Для частых событий используйте batch обработку

## Будущие расширения

1. **WebSocket сервер** - удалённый мониторинг и управление
2. **REST API** - интеграция с другими системами
3. **Message Queue** (RabbitMQ/Kafka) - для распределённой архитектуры
4. **Database backend** - замена JSON на SQLite/PostgreSQL
5. **Plugin system** - динамическая загрузка инструментов

## Заключение

Новая архитектура обеспечивает:
- ✅ Работу в реальном времени
- ✅ Неблокирующий GUI
- ✅ Единую базу знаний
- ✅ Асинхронную коммуникацию
- ✅ Полный мониторинг системы

Все существующие функции и нейронки продолжают работать, но теперь они не блокируют интерфейс и могут общаться друг с другом через шину событий.
