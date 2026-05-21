"""
Global Neural Network Operations Center (GNOC)
Модуль управления мировой картой устройств и сетевым анализом.
"""
import asyncio
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

@dataclass
class DeviceNode:
    """Узел устройства на карте мира"""
    id: str
    name: str
    latitude: float
    longitude: float
    device_type: str  # server, router, iot, sensor, quantum_node
    status: str  # online, offline, warning, critical
    load: float = 0.0  # 0-100%
    security_level: float = 1.0  # 0-1 (1 - безопасно)
    last_update: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "lat": self.latitude,
            "lon": self.longitude,
            "type": self.device_type,
            "status": self.status,
            "load": self.load,
            "security": self.security_level,
            "updated": self.last_update.isoformat(),
            "meta": self.metadata
        }

@dataclass
class NetworkConnection:
    """Связь между устройствами"""
    source_id: str
    target_id: str
    bandwidth: float  # Mbps
    latency: float    # ms
    packet_loss: float # %
    encrypted: bool

class WorldMapContext:
    """
    Единое состояние мировой карты с устройствами и связями.
    Поддерживает реальное время обновление и историю событий.
    """
    def __init__(self):
        self.nodes: Dict[str, DeviceNode] = {}
        self.connections: List[NetworkConnection] = []
        self.events: List[Dict] = []
        self.lock = asyncio.Lock()
        self._subscribers = []
        
        # Инициализация демо-данных
        self._init_demo_network()

    def _init_demo_network(self):
        """Создание демо-сети по всему миру"""
        major_cities = [
            ("NYC", "New York Server", 40.7128, -74.0060, "server"),
            ("LON", "London Hub", 51.5074, -0.1278, "router"),
            ("TOK", "Tokyo Node", 35.6762, 139.6503, "quantum_node"),
            ("SYD", "Sydney Sensor", -33.8688, 151.2093, "sensor"),
            ("MOW", "Moscow Core", 55.7558, 37.6173, "server"),
            ("SIN", "Singapore Switch", 1.3521, 103.8198, "router"),
            ("CAP", "Cape Town IoT", -33.9249, 18.4241, "iot"),
            ("RIO", "Rio Gateway", -22.9068, -43.1729, "router"),
        ]
        
        for code, name, lat, lon, dtype in major_cities:
            node = DeviceNode(
                id=code,
                name=name,
                latitude=lat,
                longitude=lon,
                device_type=dtype,
                status="online",
                load=random.uniform(10, 80),
                security_level=random.uniform(0.8, 1.0)
            )
            self.nodes[code] = node

        # Создание связей
        keys = list(self.nodes.keys())
        for i in range(len(keys)):
            for j in range(i+1, len(keys)):
                if random.random() > 0.6: # 40% вероятности связи
                    conn = NetworkConnection(
                        source_id=keys[i],
                        target_id=keys[j],
                        bandwidth=random.uniform(100, 10000),
                        latency=random.uniform(10, 200),
                        packet_loss=random.uniform(0, 2),
                        encrypted=random.random() > 0.2
                    )
                    self.connections.append(conn)

    async def update_node_status(self, node_id: str, **kwargs):
        """Асинхронное обновление статуса узла"""
        async with self.lock:
            if node_id not in self.nodes:
                return False
            
            node = self.nodes[node_id]
            for key, value in kwargs.items():
                if hasattr(node, key):
                    setattr(node, key, value)
            
            node.last_update = datetime.now()
            
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": "node_update",
                "node_id": node_id,
                "changes": kwargs
            }
            self.events.append(event)
            if len(self.events) > 1000:
                self.events = self.events[-1000:]
            
            await self._notify_subscribers(event)
            return True

    async def get_snapshot(self) -> Dict:
        """Получение текущего снимка состояния карты"""
        async with self.lock:
            return {
                "nodes": [n.to_dict() for n in self.nodes.values()],
                "connections": [
                    {
                        "source": c.source_id,
                        "target": c.target_id,
                        "bandwidth": c.bandwidth,
                        "latency": c.latency,
                        "encrypted": c.encrypted
                    } for c in self.connections
                ],
                "recent_events": self.events[-50:],
                "timestamp": datetime.now().isoformat()
            }

    def subscribe(self, callback):
        """Подписка на обновления в реальном времени"""
        self._subscribers.append(callback)

    async def _notify_subscribers(self, event):
        """Уведомление подписчиков об событии"""
        for cb in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event)
                else:
                    cb(event)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")

# Глобальный экземпляр контекста карты
global_map_context = WorldMapContext()
