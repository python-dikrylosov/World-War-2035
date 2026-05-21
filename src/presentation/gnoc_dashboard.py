"""
GNOC Dashboard - Интерактивная карта мира с устройствами и анализом нейросетей.
Запускает веб-интерфейс для мониторинга глобальной сети в реальном времени.
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Проверка наличия flask, если нет - используем простой HTTP сервер
try:
    from flask import Flask, jsonify, render_template_string
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from src.presentation.world_map_controller import global_map_context
from src.ai.neural_swarm_analyzer import neural_swarm, ConsensusReport

app = None if not FLASK_AVAILABLE else Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GNOC - Global Neural Operations Center</title>
    <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"/>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e1a; color: #e0e6ed; }
        .header { background: linear-gradient(135deg, #1a237e, #0d47a1); padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; color: #fff; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        .status-badge { background: #00c853; color: #000; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 12px; }
        .container { display: grid; grid-template-columns: 1fr 400px; gap: 15px; padding: 15px; height: calc(100vh - 70px); }
        #map { border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
        .sidebar { display: flex; flex-direction: column; gap: 15px; overflow-y: auto; }
        .panel { background: #151f32; border-radius: 10px; padding: 15px; border: 1px solid #2a3f5f; }
        .panel h3 { color: #64b5f6; margin-bottom: 10px; font-size: 16px; border-bottom: 1px solid #2a3f5f; padding-bottom: 8px; }
        .node-item { background: #1e2d4a; padding: 10px; margin: 5px 0; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
        .node-item:hover { background: #2a3f5f; transform: translateX(3px); }
        .node-item.selected { border-left: 3px solid #64b5f6; background: #253555; }
        .node-name { font-weight: bold; color: #fff; }
        .node-status { font-size: 12px; margin-top: 5px; }
        .status-online { color: #00c853; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #ff5252; }
        .metric { display: flex; justify-content: space-between; font-size: 13px; margin: 4px 0; }
        .metric-label { color: #90a4ae; }
        .metric-value { font-weight: bold; }
        .threat-high { color: #ff5252; }
        .threat-medium { color: #ffc107; }
        .threat-low { color: #00c853; }
        .analysis-report { background: #1a2744; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 13px; }
        .report-section { margin: 8px 0; }
        .report-label { color: #64b5f6; font-weight: bold; }
        .log-entry { font-size: 11px; padding: 4px 0; border-bottom: 1px solid #2a3f5f; color: #90a4ae; }
        .btn { background: #1976d2; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 10px; font-weight: bold; }
        .btn:hover { background: #1565c0; }
        .btn-analyze { background: linear-gradient(135deg, #7b1fa2, #4a148c); }
        .swarm-indicator { display: flex; gap: 5px; margin: 10px 0; }
        .swarm-node { width: 12px; height: 12px; border-radius: 50%; background: #424242; }
        .swarm-node.active { background: #00c853; animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌍 GNOC - Global Neural Operations Center</h1>
        <span class="status-badge" id="connectionStatus">● LIVE</span>
    </div>
    <div class="container">
        <div id="map"></div>
        <div class="sidebar">
            <div class="panel">
                <h3>🖥️ Устройства в сети (<span id="nodeCount">0</span>)</h3>
                <div id="nodeList"></div>
            </div>
            <div class="panel">
                <h3>🧠 Neural Swarm Analysis</h3>
                <div class="swarm-indicator">
                    <div class="swarm-node" id="swarm1" title="Security"></div>
                    <div class="swarm-node" id="swarm2" title="Performance"></div>
                    <div class="swarm-node" id="swarm3" title="Anomaly"></div>
                </div>
                <button class="btn btn-analyze" onclick="analyzeSelectedNode()">🔍 Запустить анализ (3 AI)</button>
                <div id="analysisResult"></div>
            </div>
            <div class="panel">
                <h3>📊 События в реальном времени</h3>
                <div id="eventLog" style="max-height: 150px; overflow-y: auto;"></div>
            </div>
        </div>
    </div>

    <script>
        let map, markers = {};
        let selectedNodeId = null;
        let nodesData = [];

        // Инициализация карты
        function initMap() {
            map = L.map('map').setView([20, 0], 2);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap &copy; CARTO',
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(map);
        }

        // Обновление данных
        async function fetchData() {
            try {
                const response = await fetch('/api/snapshot');
                const data = await response.json();
                updateMap(data.nodes, data.connections);
                updateNodeList(data.nodes);
                updateEventLog(data.recent_events);
                document.getElementById('nodeCount').textContent = data.nodes.length;
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        // Обновление маркеров на карте
        function updateMap(nodes, connections) {
            nodes.forEach(node => {
                if (markers[node.id]) {
                    map.removeLayer(markers[node.id]);
                }

                const color = node.status === 'online' ? '#00c853' : 
                              node.status === 'warning' ? '#ffc107' : '#ff5252';
                
                const circle = L.circleMarker([node.lat, node.lon], {
                    radius: 8 + (node.load / 20),
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.7
                }).addTo(map);

                circle.bindPopup(`
                    <b>${node.name}</b><br>
                    ID: ${node.id}<br>
                    Тип: ${node.type}<br>
                    Статус: ${node.status}<br>
                    Нагрузка: ${node.load.toFixed(1)}%<br>
                    Безопасность: ${(node.security * 100).toFixed(0)}%
                `);

                circle.on('click', () => selectNode(node.id));
                markers[node.id] = circle;
            });
        }

        // Обновление списка узлов
        function updateNodeList(nodes) {
            const container = document.getElementById('nodeList');
            container.innerHTML = nodes.map(node => `
                <div class="node-item ${node.id === selectedNodeId ? 'selected' : ''}" 
                     onclick="selectNode('${node.id}')">
                    <div class="node-name">${node.name} (${node.id})</div>
                    <div class="node-status status-${node.status}">● ${node.status.toUpperCase()}</div>
                    <div class="metric">
                        <span class="metric-label">Нагрузка:</span>
                        <span class="metric-value">${node.load.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Безопасность:</span>
                        <span class="metric-value">${(node.security * 100).toFixed(0)}%</span>
                    </div>
                </div>
            `).join('');
        }

        // Выбор узла
        function selectNode(nodeId) {
            selectedNodeId = nodeId;
            fetchData();
            document.getElementById('analysisResult').innerHTML = '';
        }

        // Запуск анализа
        async function analyzeSelectedNode() {
            if (!selectedNodeId) {
                alert('Выберите узел для анализа');
                return;
            }

            // Анимация активации роя
            [1,2,3].forEach(i => {
                document.getElementById(`swarm${i}`).classList.add('active');
            });

            try {
                const response = await fetch(`/api/analyze/${selectedNodeId}`, { method: 'POST' });
                const report = await response.json();
                
                setTimeout(() => {
                    [1,2,3].forEach(i => {
                        document.getElementById(`swarm${i}`).classList.remove('active');
                    });
                    displayAnalysis(report);
                }, 1500);
            } catch (error) {
                console.error('Analysis error:', error);
                [1,2,3].forEach(i => {
                    document.getElementById(`swarm${i}`).classList.remove('active');
                });
            }
        }

        // Отображение результатов анализа
        function displayAnalysis(report) {
            const threatClass = report.overall_threat_level > 0.5 ? 'threat-high' :
                                report.overall_threat_level > 0.2 ? 'threat-medium' : 'threat-low';
            
            const html = `
                <div class="analysis-report">
                    <div class="report-section">
                        <span class="report-label">Уровень угрозы:</span>
                        <span class="${threatClass}">${(report.overall_threat_level * 100).toFixed(0)}%</span>
                    </div>
                    <div class="report-section">
                        <span class="report-label">Согласовано:</span><br>
                        ${report.agreed_findings.map(f => '• ' + f).join('<br>')}
                    </div>
                    ${report.priority_actions.length > 0 ? `
                    <div class="report-section">
                        <span class="report-label">Действия:</span><br>
                        ${report.priority_actions.map(a => '→ ' + a).join('<br>')}
                    </div>` : ''}
                    <div style="font-size: 11px; color: #90a4ae; margin-top: 8px;">
                        Анализ завершен: ${new Date(report.timestamp).toLocaleTimeString()}
                    </div>
                </div>
            `;
            document.getElementById('analysisResult').innerHTML = html;
        }

        // Обновление лога событий
        function updateEventLog(events) {
            const container = document.getElementById('eventLog');
            container.innerHTML = events.slice(-10).reverse().map(event => {
                const time = new Date(event.timestamp).toLocaleTimeString();
                return `<div class="log-entry">[${time}] ${event.node_id}: ${event.type}</div>`;
            }).join('');
        }

        // Автообновление
        setInterval(fetchData, 2000);

        // Старт
        initMap();
        fetchData();
    </script>
</body>
</html>
"""

if FLASK_AVAILABLE:
    CORS(app)

    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)

    @app.route('/api/snapshot')
    def get_snapshot():
        async def fetch():
            return await global_map_context.get_snapshot()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return jsonify(loop.run_until_complete(fetch()))
        finally:
            loop.close()

    @app.route('/api/analyze/<node_id>', methods=['POST'])
    def analyze_node(node_id):
        async def run_analysis():
            node_data = global_map_context.nodes.get(node_id)
            if not node_data:
                return {"error": "Node not found"}, 404
            
            report = await neural_swarm.analyze_node(node_data.to_dict())
            return {
                "timestamp": report.timestamp,
                "overall_threat_level": report.overall_threat_level,
                "agreed_findings": report.agreed_findings,
                "disputed_points": report.disputed_points,
                "priority_actions": report.priority_actions
            }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_analysis())
            if isinstance(result, tuple):
                return result
            return jsonify(result)
        finally:
            loop.close()

    def run_dashboard(host='0.0.0.0', port=5000):
        print(f"\n🌍 GNOC Dashboard запущен!")
        print(f"   URL: http://localhost:{port}")
        print(f"   Режим: Real-time monitoring с Neural Swarm")
        print("\n   Откройте браузер для просмотра карты мира\n")
        app.run(host=host, port=port, debug=False, threaded=True)

else:
    def run_dashboard(host='0.0.0.0', port=5000):
        print("\n❌ Flask не установлен!")
        print("   Установите: pip install flask flask-cors")
        print("\n   Или используйте альтернативный режим:")
        print("   python -m src.presentation.cli_monitor\n")

async def simulate_network_activity():
    """Фоновая симуляция активности сети"""
    while True:
        await asyncio.sleep(5)
        node_ids = list(global_map_context.nodes.keys())
        random_node = random.choice(node_ids)
        
        changes = {}
        if random.random() > 0.7:
            changes['load'] = min(100, max(0, global_map_context.nodes[random_node].load + random.uniform(-15, 15)))
        if random.random() > 0.8:
            changes['security_level'] = min(1.0, max(0.5, global_map_context.nodes[random_node].security_level + random.uniform(-0.1, 0.1)))
        
        if changes:
            await global_map_context.update_node_status(random_node, **changes)
            print(f"[SIM] Updated {random_node}: {changes}")

if __name__ == "__main__":
    import random
    
    print("\n" + "="*60)
    print("🌍 GNOC - Global Neural Operations Center")
    print("="*60)
    print("\nЗапуск системы...")
    
    # Инициализация нейросетей
    asyncio.run(neural_swarm.initialize())
    
    # Запуск дашборда и симуляции
    if FLASK_AVAILABLE:
        # Запуск в отдельных потоках
        import threading
        
        sim_thread = threading.Thread(target=lambda: asyncio.run(simulate_network_activity()), daemon=True)
        sim_thread.start()
        
        run_dashboard()
    else:
        print("\nВеб-интерфейс недоступен без Flask.")
        print("Запуск CLI мониторинга...")
        # Здесь можно добавить CLI режим
