"""
Shared Context Manager - Единое хранилище состояния для всех компонентов
Асинхронная потокобезопасная база знаний в реальном времени
"""
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class ContextEntry:
    """Элемент контекста с метаданными"""
    key: str
    value: Any
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class SharedContextManager:
    """
    Централизованное управление состоянием приложения
    - Потокобезопасность через asyncio.Lock
    - Версионирование данных
    - Подписка на изменения
    - Персистентность (опционально)
    """
    
    def __init__(self, persist_path: Optional[str] = "data/context.json"):
        self._data: Dict[str, ContextEntry] = {}
        self._lock = asyncio.Lock()
        self._subscribers: List[Callable] = []
        self._persist_path = Path(persist_path) if persist_path else None
        
        # Загружаем сохранённый контекст
        if self._persist_path and self._persist_path.exists():
            self._load_from_disk()
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Получить значение по ключу"""
        async with self._lock:
            entry = self._data.get(key)
            return entry.value if entry else default
    
    async def set(self, key: str, value: Any, metadata: Dict[str, Any] = None):
        """Установить значение по ключу"""
        async with self._lock:
            now = datetime.now().isoformat()
            
            if key in self._data:
                # Обновляем существующий
                entry = self._data[key]
                entry.value = value
                entry.updated_at = now
                entry.version += 1
                if metadata:
                    entry.metadata.update(metadata)
            else:
                # Создаём новый
                entry = ContextEntry(
                    key=key,
                    value=value,
                    metadata=metadata or {}
                )
                self._data[key] = entry
            
            # Сохраняем на диск
            await self._save_to_disk()
        
        # Уведомляем подписчиков
        await self._notify_subscribers(key, value, "updated")
    
    async def delete(self, key: str) -> bool:
        """Удалить ключ"""
        async with self._lock:
            if key in self._data:
                del self._data[key]
                await self._save_to_disk()
                await self._notify_subscribers(key, None, "deleted")
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        async with self._lock:
            return key in self._data
    
    async def keys(self) -> List[str]:
        """Получить все ключи"""
        async with self._lock:
            return list(self._data.keys())
    
    async def get_all(self) -> Dict[str, Any]:
        """Получить все данные"""
        async with self._lock:
            return {k: v.value for k, v in self._data.items()}
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Поиск по ключам и значениям"""
        async with self._lock:
            results = []
            query_lower = query.lower()
            for key, entry in self._data.items():
                if (query_lower in key.lower() or 
                    query_lower in str(entry.value).lower()):
                    results.append({
                        "key": key,
                        "value": entry.value,
                        "metadata": entry.metadata,
                        "created_at": entry.created_at
                    })
            return results
    
    def subscribe(self, callback: Callable):
        """Подписаться на изменения контекста"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Отписаться от изменений"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    async def _notify_subscribers(self, key: str, value: Any, action: str):
        """Уведомить подписчиков об изменении"""
        event_data = {"key": key, "value": value, "action": action}
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_data)
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, callback, event_data)
            except Exception as e:
                print(f"Error in context subscriber: {e}")
    
    async def _save_to_disk(self):
        """Сохранить контекст на диск"""
        if not self._persist_path:
            return
        
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            data_to_save = {
                k: {
                    "value": v.value,
                    "created_at": v.created_at,
                    "updated_at": v.updated_at,
                    "version": v.version,
                    "metadata": v.metadata
                }
                for k, v in self._data.items()
            }
            with open(self._persist_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving context: {e}")
    
    def _load_from_disk(self):
        """Загрузить контекст с диска"""
        try:
            with open(self._persist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, entry_data in data.items():
                    self._data[key] = ContextEntry(
                        key=key,
                        value=entry_data["value"],
                        created_at=entry_data.get("created_at", ""),
                        updated_at=entry_data.get("updated_at", ""),
                        version=entry_data.get("version", 1),
                        metadata=entry_data.get("metadata", {})
                    )
        except Exception as e:
            print(f"Error loading context: {e}")
    
    async def clear(self):
        """Очистить весь контекст"""
        async with self._lock:
            self._data.clear()
            await self._save_to_disk()
            await self._notify_subscribers("*", None, "cleared")


# Глобальный экземпляр (singleton)
_global_context: Optional[SharedContextManager] = None

def get_context_manager(persist_path: Optional[str] = "data/context.json") -> SharedContextManager:
    """Получить глобальный менеджер контекста"""
    global _global_context
    if _global_context is None:
        _global_context = SharedContextManager(persist_path)
    return _global_context
