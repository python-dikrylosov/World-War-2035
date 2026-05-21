"""
Distributed Sensor Node for GNOC Sky Shield.
Превращает любой компьютер (домашний ПК, VPS) в узел пассивного мониторинга.

Особенности:
- Пассивное сканирование (SDR или сетевой трафик)
- Локальная предобработка AI (фильтрация шумов)
- Зашифрованная отправка событий в центральный GNOC
- Работа через нестабильный домашний интернет
"""

import asyncio
import json
import time
import uuid
import socket
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from datetime import datetime

# Имитация библиотек для работы с железом (SDR)
# В реальности здесь были бы: pyrtlsdr, gnuradio, scapy

@dataclass
class SensorEvent:
    node_id: str
    timestamp: float
    frequency: float
    signal_strength: float
    modulation: str
    location: Dict[str, float]  # lat, lon
    confidence: float
    raw_signature_hash: str  # Хеш сигнатуры для приватности

class LocalAIFilter:
    """Легковесная нейросеть для фильтрации шумов на краю (Edge AI)"""
    
    def __init__(self):
        self.threshold = 0.75
        print("🧠 [LocalAI] Инициализация легковесной модели детектирования...")
    
    async def analyze_chunk(self, signal_data: dict) -> Optional[Dict]:
        """
        Анализирует кусок сигнала локально.
        Возвращает событие только если уверенность > порога.
        Экономит трафик домашнего интернета.
        """
        await asyncio.sleep(0.05)  # Имитация инференса
        
        # Симуляция логики: если сигнал похож на известный паттерн БПЛА
        is_drone_like = signal_data.get('strength', 0) > -80 and signal_data.get('freq', 0) in [2400, 5800]
        
        if is_drone_like:
            return {
                "type": "SUSPECTED_UAV",
                "confidence": 0.92,
                "details": "Обнаружен протокол OcuSync/DJI"
            }
        return None

class DistributedSensorNode:
    def __init__(self, node_name: str, central_server_url: str, location: tuple):
        self.node_id = str(uuid.uuid4())[:8]
        self.node_name = node_name
        self.central_server = central_server_url
        self.location = {"lat": location[0], "lon": location[1]}
        self.ai_filter = LocalAIFilter()
        self.is_running = False
        self.stats = {"scans": 0, "events_sent": 0}
        
    async def scan_spectrum(self):
        """
        Эмуляция сканирования спектра через SDR.
        В реальности: чтение буфера RTL-SDR.
        """
        # Симуляция данных с эфира
        import random
        freqs = [2400.0, 2412.0, 5800.0, 900.0, 433.0]
        return {
            "freq": random.choice(freqs),
            "strength": random.uniform(-95, -40),
            "noise_floor": -100
        }

    async def send_event_securely(self, event: SensorEvent):
        """
        Отправка события в центральный GNOC через зашифрованный канал.
        Устойчиво к обрывам домашнего интернета (retry logic).
        """
        payload = json.dumps(asdict(event))
        retries = 3
        
        for attempt in range(retries):
            try:
                # Здесь был бы реальный HTTPS/MQTT over TLS запрос
                # requests.post(self.central_server, data=payload, timeout=5)
                
                print(f"📡 [{self.node_name}] ОТПРАВКА СОБЫТИЯ в GNOC:")
                print(f"   📍 Локация: {self.location}")
                print(f"   📉 Частота: {event.frequency} MHz, Сила: {event.signal_strength} dBm")
                print(f"   🤖 Вероятность: {event.confidence:.2%}")
                print(f"   🔒 Канал защищен (TLS 1.3)")
                
                self.stats["events_sent"] += 1
                return True
            except Exception as e:
                print(f"⚠️ Ошибка отправки (попытка {attempt+1}): {e}")
                await asyncio.sleep(2 ** attempt) # Exponential backoff
        
        return False

    async def run_cycle(self):
        """Основной цикл работы узла"""
        print(f"🚀 [{self.node_name}] Запуск узла мониторинга...")
        print(f"   ID: {self.node_id}")
        print(f"   Локация: {self.location}")
        print(f"   Цель: Мониторинг эфира и отправка алертов")
        
        self.is_running = True
        scan_count = 0
        
        while self.is_running:
            scan_count += 1
            self.stats["scans"] += 1
            
            # 1. Сканирование
            raw_data = await self.scan_spectrum()
            
            # 2. Локальный AI анализ (Edge Computing)
            analysis = await self.ai_filter.analyze_chunk(raw_data)
            
            if analysis:
                # 3. Формирование события
                event = SensorEvent(
                    node_id=self.node_id,
                    timestamp=time.time(),
                    frequency=raw_data['freq'],
                    signal_strength=raw_data['strength'],
                    modulation="OFDM",
                    location=self.location,
                    confidence=analysis['confidence'],
                    raw_signature_hash=uuid.uuid4().hex[:16]
                )
                
                # 4. Отправка в центр
                await self.send_event_securely(event)
            else:
                if scan_count % 10 == 0:
                    print(f"💤 [{self.node_name}] Сканирование продолжается... (Шумов нет)")
            
            # Асинхронная пауза (не блокирует систему)
            await asyncio.sleep(1.5) 

    def stop(self):
        self.is_running = False
        print(f"🛑 [{self.node_name}] Узел остановлен. Статистика: {self.stats}")

async def main():
    # Пример запуска узла в Москве (домашний ПК)
    moscow_node = DistributedSensorNode(
        node_name="Home_Moscow_Node",
        central_server_url="https://gnoc-central.military.local/api/ingest",
        location=(55.7558, 37.6173)
    )
    
    # Пример запуска узла на Урале (сервер друга)
    ural_node = DistributedSensorNode(
        node_name="Friend_Ekb_Node",
        central_server_url="https://gnoc-central.military.local/api/ingest",
        location=(56.8389, 60.6057)
    )

    # Запуск обоих узлов параллельно
    await asyncio.gather(
        moscow_node.run_cycle(),
        ural_node.run_cycle(),
        return_exceptions=True
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Завершение работы распределенной сети...")
