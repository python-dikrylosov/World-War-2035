"""
Orchestrator - Центральный дирижёр, связка всех моделей
"""
import re
import json
from typing import Dict, Any, List, Optional


class Orchestrator:
    """Координация между Vision, Coder, Audio и Tools"""
    
    def __init__(self, vision_model, coder_model, audio_model, tool_registry):
        self.vision = vision_model
        self.coder = coder_model
        self.audio = audio_model
        self.tools = tool_registry
        self.context = {}
    
    # === VISION SCENARIOS ===
    
    def vision_capture(self) -> str:
        """Сделать скриншот и вернуть путь"""
        return self.tools.execute("capture_screen")
    
    def vision_analyze(self, image_path: str, task: str = "describe") -> str:
        """Анализ изображения"""
        if task == "describe":
            return self.vision.describe_image(image_path)
        elif task == "ocr":
            return self.vision.read_text(image_path)
        elif task == "document":
            return self.vision.analyze_document(image_path)
        return self.vision.describe_image(image_path, task)
    
    def vision_find_element(self, image_path: str, element: str) -> Dict[str, int]:
        """Найти элемент на экране"""
        prompt = f"Find the '{element}' element. Provide coordinates: <box>x1,y1,x2,y2</box>"
        response = self.vision.describe_image(image_path, prompt)
        coords = self._parse_coordinates(response)
        if coords:
            return {"x": (coords[0] + coords[2]) // 2, "y": (coords[1] + coords[3]) // 2}
        return {}
    
    def _parse_coordinates(self, text: str) -> Optional[List[int]]:
        """Парсинг координат из ответа"""
        match = re.search(r'<box>(\d+),(\d+),(\d+),(\d+)</box>', text)
        if match:
            return [int(match.group(i)) for i in range(1, 5)]
        return None
    
    # === AUDIO SCENARIOS ===
    
    def audio_transcribe(self, audio_path: str) -> str:
        """Транскрипция аудио"""
        return self.audio.transcribe(audio_path)
    
    def audio_intent(self, audio_path: str) -> str:
        """Анализ интента"""
        transcription = self.audio.transcribe(audio_path)
        prompt = f"Analyze intent: '{transcription}'. What action should be taken?"
        return self.coder.generate(prompt)
    
    def audio_summarize(self, audio_path: str) -> str:
        """Саммари аудио"""
        transcription = self.audio.transcribe(audio_path)
        prompt = f"Summarize: '{transcription}'"
        return self.coder.generate(prompt)
    
    # === CODER SCENARIOS ===
    
    def coder_generate(self, prompt: str, context: str = "") -> str:
        """Генерация кода"""
        return self.coder.generate(prompt, context)
    
    def coder_explain(self, code: str) -> str:
        """Объяснение кода"""
        return self.coder.explain_code(code)
    
    def coder_debug(self, code: str, error: str = "") -> str:
        """Отладка кода"""
        return self.coder.debug_code(code, error)
    
    def coder_review(self, code: str) -> str:
        """Ревью кода"""
        return self.coder.generate(f"Review this code:\n\n```python\n{code}\n```")
    
    # === WORKFLOWS ===
    
    def workflow_voice_control(self, audio_path: str) -> Dict[str, Any]:
        """Голосовое управление: Audio → Intent → Action"""
        transcription = self.audio_transcribe(audio_path)
        intent = self.audio_intent(audio_path)
        
        # Парсим действие из интента
        action = self._parse_action(intent)
        if action:
            result = self.tools.execute(action["tool"], **action.get("params", {}))
            return {"transcription": transcription, "intent": intent, "action_result": result}
        return {"transcription": transcription, "intent": intent}
    
    def workflow_screen_to_action(self, element: str) -> Dict[str, Any]:
        """Скриншот → Vision → Клик"""
        screenshot = self.vision_capture()
        analysis = self.vision_analyze(screenshot, "analyze_ui")
        coords = self.vision_find_element(screenshot, element)
        
        if coords:
            result = self.tools.execute("mouse_click", x=coords["x"], y=coords["y"])
            return {"screenshot": screenshot, "analysis": analysis, "click_result": result}
        return {"screenshot": screenshot, "analysis": analysis, "error": "Element not found"}
    
    def workflow_document_processing(self, image_path: str) -> Dict[str, Any]:
        """Документ → OCR → База знаний"""
        text = self.vision.read_text(image_path)
        summary = self.coder.generate(f"Summarize this document:\n\n{text}")
        self.tools.execute("db_store", key=f"doc_{len(text)}", value={"text": text, "summary": summary})
        return {"text": text, "summary": summary}
    
    def workflow_auto_navigation(self, target: str, max_steps: int = 5) -> List[Dict]:
        """Авто-навигация: Vision → Action → Vision (loop)"""
        results = []
        for step in range(max_steps):
            screenshot = self.vision_capture()
            analysis = self.vision_analyze(screenshot, f"Find path to: {target}")
            
            if target.lower() in analysis.lower():
                results.append({"step": step, "status": "found", "analysis": analysis})
                break
            
            coords = self.vision_find_element(screenshot, "next button")
            if coords:
                self.tools.execute("mouse_click", x=coords["x"], y=coords["y"])
                results.append({"step": step, "action": "click_next", "coords": coords})
                self.tools.execute("wait", seconds=1)
            else:
                results.append({"step": step, "status": "stuck", "analysis": analysis})
                break
        
        return results
    
    def _parse_action(self, intent: str) -> Optional[Dict]:
        """Парсинг JSON действия из ответа"""
        try:
            match = re.search(r'\{[^}]*"tool"[^}]*\}', intent)
            if match:
                return json.loads(match.group())
        except:
            pass
        return None
