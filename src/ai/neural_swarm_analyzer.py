"""
Neural Analyst Swarm - Рой из 3 нейросетей для коллективного анализа.
Каждая сеть специализируется на своем аспекте, затем происходит консенсус.
"""
import asyncio
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnalysisResult:
    """Результат анализа от одной нейросети"""
    analyst_id: str
    confidence: float  # 0-1
    findings: List[str]
    threats: List[str]
    recommendations: List[str]
    raw_data: Dict

@dataclass
class ConsensusReport:
    """Сводный отчет после консенсуса 3 сетей"""
    timestamp: str
    overall_threat_level: float  # 0-1
    agreed_findings: List[str]
    disputed_points: List[str]
    priority_actions: List[str]
    individual_reports: List[AnalysisResult]

class NeuralAnalyst:
    """Индивидуальный аналитик-нейросеть"""
    
    def __init__(self, analyst_id: str, specialization: str):
        self.id = analyst_id
        self.specialization = specialization  # security, performance, anomaly
        self.model_loaded = False
    
    async def initialize(self):
        """Асинхронная загрузка модели"""
        await asyncio.sleep(0.5)  # Имитация загрузки
        self.model_loaded = True
        print(f"[{self.id}] {self.specialization} analyst loaded")
    
    async def analyze(self, data: Dict) -> AnalysisResult:
        """Анализ данных с учетом специализации"""
        if not self.model_loaded:
            await self.initialize()
        
        # Имитация работы нейросети
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        findings = []
        threats = []
        recommendations = []
        
        if self.specialization == "security":
            findings.append("Проверка уязвимостей завершена")
            if data.get('security_level', 1.0) < 0.9:
                threats.append("Обнаружены потенциальные уязвимости")
                recommendations.append("Рекомендуется обновить протоколы шифрования")
            else:
                findings.append("Уровень безопасности в норме")
                
        elif self.specialization == "performance":
            findings.append("Анализ производительности выполнен")
            if data.get('load', 0) > 70:
                threats.append("Высокая нагрузка на узел")
                recommendations.append("Требуется балансировка нагрузки")
            else:
                findings.append("Производительность оптимальна")
                
        elif self.specialization == "anomaly":
            findings.append("Поиск аномалий завершен")
            if random.random() > 0.8:
                threats.append("Обнаружена нестандартная активность")
                recommendations.append("Необходима дополнительная проверка логов")
            else:
                findings.append("Аномалий не выявлено")
        
        return AnalysisResult(
            analyst_id=self.id,
            confidence=random.uniform(0.85, 0.99),
            findings=findings,
            threats=threats,
            recommendations=recommendations,
            raw_data=data
        )

class NeuralSwarmAnalyzer:
    """
    Координатор роя из 3 нейросетей.
    Запускает параллельный анализ и достигает консенсуса.
    """
    
    def __init__(self):
        self.analysts = [
            NeuralAnalyst("NET-SEC-01", "security"),
            NeuralAnalyst("PERF-02", "performance"),
            NeuralAnalyst("ANOM-03", "anomaly")
        ]
        self.initialized = False
    
    async def initialize(self):
        """Параллельная инициализация всех аналитиков"""
        tasks = [a.initialize() for a in self.analysts]
        await asyncio.gather(*tasks)
        self.initialized = True
        print("🧠 Neural Swarm Ready (3 analysts)")
    
    async def analyze_node(self, node_data: Dict) -> ConsensusReport:
        """
        Параллельный анализ узла тремя сетями с последующим консенсусом.
        """
        if not self.initialized:
            await self.initialize()
        
        # Параллельный запуск всех трех аналитиков
        tasks = [analyst.analyze(node_data) for analyst in self.analysts]
        results = await asyncio.gather(*tasks)
        
        # Достижение консенсуса
        all_threats = []
        all_recommendations = []
        all_findings = []
        
        for result in results:
            all_findings.extend(result.findings)
            all_threats.extend(result.threats)
            all_recommendations.extend(result.recommendations)
        
        # Определение уровня угрозы
        threat_level = len(all_threats) / 3.0  # Простая эвристика
        
        # Выделение согласованных и спорных моментов
        agreed = [f for f in all_findings if all_findings.count(f) > 1]
        disputed = [f for f in all_findings if all_findings.count(f) == 1]
        
        # Приоритетные действия (те, что предлагают ≥2 сети)
        priority = [r for r in all_recommendations if all_recommendations.count(r) >= 2]
        if not priority:
            priority = all_recommendations[:2]  # Берем топ-2 если нет консенсуса
        
        return ConsensusReport(
            timestamp=datetime.now().isoformat(),
            overall_threat_level=threat_level,
            agreed_findings=list(set(agreed)),
            disputed_points=list(set(disputed)),
            priority_actions=priority,
            individual_reports=results
        )

# Глобальный экземпляр анализатора
neural_swarm = NeuralSwarmAnalyzer()

async def demo_swarm_analysis():
    """Демонстрация работы роя нейросетей"""
    print("\n" + "="*60)
    print("DEMO: Neural Swarm Analysis")
    print("="*60)
    
    # Тестовые данные узла
    test_node = {
        "id": "NYC",
        "name": "New York Server",
        "load": 85.0,
        "security_level": 0.75,
        "status": "online"
    }
    
    print(f"\nАнализ узла: {test_node['name']}")
    print(f"Нагрузка: {test_node['load']}%, Безопасность: {test_node['security_level']}")
    
    report = await neural_swarm.analyze_node(test_node)
    
    print(f"\n📊 CONSensus Report:")
    print(f"   Уровень угрозы: {report.overall_threat_level:.2f}")
    print(f"   Согласованные находки: {len(report.agreed_findings)}")
    print(f"   Спорные моменты: {len(report.disputed_points)}")
    print(f"   Приоритетные действия: {len(report.priority_actions)}")
    
    print(f"\n🔍 Детали:")
    for finding in report.agreed_findings:
        print(f"   ✓ {finding}")
    
    if report.disputed_points:
        print(f"\n⚠️  Спорные вопросы:")
        for point in report.disputed_points:
            print(f"   ? {point}")
    
    if report.priority_actions:
        print(f"\n🎯 Приоритетные действия:")
        for action in report.priority_actions:
            print(f"   → {action}")
    
    print("="*60 + "\n")
    return report

if __name__ == "__main__":
    asyncio.run(demo_swarm_analysis())
