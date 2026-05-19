"""
Workflows - Движок рабочих процессов + 4 готовых сценария
"""
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field


@dataclass
class WorkflowStep:
    """Шаг рабочего процесса"""
    name: str
    action: Callable
    params: Dict[str, Any] = field(default_factory=dict)
    on_success: Optional[str] = None
    on_failure: Optional[str] = None


@dataclass
class Workflow:
    """Рабочий процесс"""
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    
    def add_step(self, name: str, action: Callable, **params):
        step = WorkflowStep(name=name, action=action, params=params)
        self.steps.append(step)
        return self
    
    def execute(self, orchestrator) -> Dict[str, Any]:
        """Выполнить workflow"""
        results = {"workflow": self.name, "steps": []}
        for step in self.steps:
            try:
                result = step.action(**step.params)
                results["steps"].append({"name": step.name, "status": "success", "result": result})
            except Exception as e:
                results["steps"].append({"name": step.name, "status": "error", "error": str(e)})
                if step.on_failure:
                    break
        return results


class WorkflowEngine:
    """Движок workflows"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.workflows: Dict[str, Workflow] = {}
        self._register_presets()
    
    def _register_presets(self):
        """Регистрация пресетов"""
        self.register(self.screen_navigation())
        self.register(self.voice_to_action())
        self.register(self.document_processing())
        self.register(self.code_review())
    
    def register(self, workflow: Workflow):
        self.workflows[workflow.name] = workflow
    
    def get(self, name: str) -> Optional[Workflow]:
        return self.workflows.get(name)
    
    def list_workflows(self) -> List[str]:
        return list(self.workflows.keys())
    
    def execute(self, name: str) -> Dict[str, Any]:
        workflow = self.get(name)
        if not workflow:
            return {"error": f"Workflow '{name}' not found"}
        return workflow.execute(self.orchestrator)
    
    def create_custom_workflow(self, name: str, description: str) -> Workflow:
        workflow = Workflow(name=name, description=description)
        self.workflows[name] = workflow
        return workflow
    
    # === PRESET WORKFLOWS ===
    
    def screen_navigation(self) -> Workflow:
        """Скриншот → Анализ → Клик"""
        wf = Workflow(
            name="screen_navigation",
            description="Navigate UI by finding and clicking elements"
        )
        wf.add_step("capture", self.orchestrator.vision_capture)
        wf.add_step("analyze", self.orchestrator.vision_analyze, 
                   image_path="temp_screenshot.png", task="analyze_ui")
        wf.add_step("find", self.orchestrator.vision_find_element,
                   image_path="temp_screenshot.png", element="button")
        wf.add_step("click", self.orchestrator.tools.execute,
                   name="mouse_click", x=100, y=100)
        return wf
    
    def voice_to_action(self) -> Workflow:
        """Голос → Транскрипция → Интент → Действие"""
        wf = Workflow(
            name="voice_to_action",
            description="Convert voice command to action"
        )
        wf.add_step("transcribe", self.orchestrator.audio_transcribe,
                   audio_path="command.wav")
        wf.add_step("intent", self.orchestrator.audio_intent,
                   audio_path="command.wav")
        return wf
    
    def document_processing(self) -> Workflow:
        """Документ → OCR → Анализ → База"""
        wf = Workflow(
            name="document_processing",
            description="Process document with OCR and store in knowledge base"
        )
        wf.add_step("ocr", self.orchestrator.vision_read_text,
                   image_path="document.png")
        wf.add_step("summarize", self.orchestrator.coder_generate,
                   prompt="Summarize this document")
        wf.add_step("store", self.orchestrator.tools.execute,
                   name="db_store", key="doc", value={})
        return wf
    
    def code_review(self) -> Workflow:
        """Файл → Чтение → Ревью → Отчёт"""
        wf = Workflow(
            name="code_review",
            description="Review code file and generate report"
        )
        wf.add_step("read", self.orchestrator.tools.execute,
                   name="file_read", path="code.py")
        wf.add_step("review", self.orchestrator.coder_review,
                   code="")
        wf.add_step("report", self.orchestrator.tools.execute,
                   name="file_write", path="review.md", content="")
        return wf


class WorkflowRunner:
    """Исполнитель workflows"""
    
    def __init__(self, engine: WorkflowEngine):
        self.engine = engine
    
    def run(self, workflow_name: str, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Запустить workflow с опциональным callback"""
        result = self.engine.execute(workflow_name)
        if callback:
            callback(result)
        return result
    
    def run_all(self) -> Dict[str, Dict]:
        """Запустить все workflows"""
        results = {}
        for name in self.engine.list_workflows():
            results[name] = self.run(name)
        return results
