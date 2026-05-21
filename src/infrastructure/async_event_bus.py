"""
Async Event Bus - Асинхронная шина событий для реального времени
Единая система обмена сообщениями между всеми компонентами
"""
import asyncio
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class EventType(Enum):
    """Типы событий в системе"""
    # Vision события
    VISION_CAPTURED = "vision:captured"
    VISION_ANALYZED = "vision:analyzed"
    VISION_ERROR = "vision:error"
    
    # Audio события
    AUDIO_RECORDED = "audio:recorded"
    AUDIO_TRANSCRIBED = "audio:transcribed"
    AUDIO_INTENT = "audio:intent"
    AUDIO_ERROR = "audio:error"
    
    # Coder события
    CODER_GENERATING = "coder:generating"
    CODER_COMPLETE = "coder:complete"
    CODER_ERROR = "coder:error"
    
    # Tool события
    TOOL_EXECUTED = "tool:executed"
    TOOL_ERROR = "tool:error"
    
    # Database события
    DB_STORED = "db:stored"
    DB_UPDATED = "db:updated"
    DB_DELETED = "db:deleted"
    
    # Workflow события
    WORKFLOW_STARTED = "workflow:started"
    WORKFLOW_STEP = "workflow:step"
    WORKFLOW_COMPLETE = "workflow:complete"
    WORKFLOW_ERROR = "workflow:error"
    
    # System события
    SYSTEM_STATUS = "system:status"
    CONTEXT_UPDATED = "context:updated"


@dataclass
class Event:
    """Структура события"""
    type: EventType
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = ""
    correlation_id: str = ""  # Для связывания связанных событий


class EventBus:
    """
    Асинхронная шина событий типа Pub/Sub
    Позволяет компонентам общаться без прямых зависимостей
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._lock = asyncio.Lock()
        
    def subscribe(self, event_type: EventType, callback: Callable):
        """Подписаться на конкретный тип событий"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Отписаться от событий"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
            
    def subscribe_all(self, callback: Callable):
        """Подписаться на ВСЕ события (для логгирования/мониторинга)"""
        self._global_subscribers.append(callback)
        
    async def publish(self, event: Event):
        """Опубликовать событие (асинхронно)"""
        async with self._lock:
            # Сохраняем в историю
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
        
        # Получаем подписчиков
        subscribers = self._subscribers.get(event.type, []) + self._global_subscribers
        
        # Асинхронно уведомляем всех подписчиков
        tasks = []
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event))
                else:
                    # Запускаем синхронную функцию в executor
                    loop = asyncio.get_event_loop()
                    tasks.append(loop.run_in_executor(None, callback, event))
            except Exception as e:
                print(f"Error in subscriber callback: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def publish_sync(self, event: Event):
        """Опубликовать событие (синхронно, для совместимости)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.publish(event))
        finally:
            loop.close()
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 50) -> List[Event]:
        """Получить историю событий"""
        if event_type:
            filtered = [e for e in self._event_history if e.type == event_type]
            return filtered[-limit:]
        return self._event_history[-limit:]
    
    def clear_history(self):
        """Очистить историю"""
        self._event_history.clear()


# Глобальный экземпляр (singleton)
_global_event_bus: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    """Получить глобальную шину событий"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
