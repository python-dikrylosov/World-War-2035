"""
Async Orchestrator - Асинхронная версия оркестратора для работы в реальном времени
Интеграция с Event Bus и Shared Context
"""
import asyncio
import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .async_event_bus import EventBus, EventType, Event, get_event_bus
from .shared_context import SharedContextManager, get_context_manager


class AsyncOrchestrator:
    """
    Асинхронный координатор между Vision, Coder, Audio и Tools
    - Не блокирует GUI
    - Публикует события в шину
    - Использует единый контекст
    """
    
    def __init__(
        self, 
        vision_model=None, 
        coder_model=None, 
        audio_model=None, 
        tool_registry=None,
        event_bus: Optional[EventBus] = None,
        context_manager: Optional[SharedContextManager] = None
    ):
        self.vision = vision_model
        self.coder = coder_model
        self.audio = audio_model
        self.tools = tool_registry
        self.event_bus = event_bus or get_event_bus()
        self.context = context_manager or get_context_manager()
        self._correlation_counter = 0
    
    def _generate_correlation_id(self) -> str:
        """Создать ID для связывания связанных событий"""
        self._correlation_counter += 1
        return f"corr_{self._correlation_counter}"
    
    async def _publish(self, event_type: EventType, payload: Dict[str, Any], source: str = "", correlation_id: str = ""):
        """Опубликовать событие в шину"""
        event = Event(
            type=event_type,
            payload=payload,
            source=source,
            correlation_id=correlation_id
        )
        await self.event_bus.publish(event)
    
    # === VISION SCENARIOS ===
    
    async def vision_capture_async(self) -> str:
        """Асинхронный скриншот"""
        corr_id = self._generate_correlation_id()
        
        try:
            if asyncio.iscoroutinefunction(self.tools.execute):
                path = await self.tools.execute("capture_screen")
            else:
                loop = asyncio.get_event_loop()
                path = await loop.run_in_executor(None, self.tools.execute, "capture_screen")
            
            await self._publish(
                EventType.VISION_CAPTURED,
                {"path": path},
                source="orchestrator",
                correlation_id=corr_id
            )
            return path
        except Exception as e:
            await self._publish(
                EventType.VISION_ERROR,
                {"error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    async def vision_analyze_async(self, image_path: str, task: str = "describe") -> str:
        """Асинхронный анализ изображения"""
        corr_id = self._generate_correlation_id()
        
        try:
            await self._publish(
                EventType.VISION_ANALYZED,
                {"status": "started", "path": image_path, "task": task},
                source="orchestrator",
                correlation_id=corr_id
            )
            
            if task == "describe":
                result = await self._run_in_executor(
                    self.vision.describe_image, image_path
                )
            elif task == "ocr":
                result = await self._run_in_executor(
                    self.vision.read_text, image_path
                )
            elif task == "document":
                result = await self._run_in_executor(
                    self.vision.analyze_document, image_path
                )
            else:
                result = await self._run_in_executor(
                    self.vision.describe_image, image_path, task
                )
            
            # Сохраняем результат в контекст
            await self.context.set(f"vision:last_result", {
                "path": image_path,
                "task": task,
                "result": result
            })
            
            await self._publish(
                EventType.VISION_ANALYZED,
                {"status": "complete", "result": result[:500]},
                source="orchestrator",
                correlation_id=corr_id
            )
            return result
        except Exception as e:
            await self._publish(
                EventType.VISION_ERROR,
                {"error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    async def vision_find_element_async(self, image_path: str, element: str) -> Dict[str, int]:
        """Асинхронный поиск элемента на экране"""
        corr_id = self._generate_correlation_id()
        
        try:
            prompt = f"Find the '{element}' element. Provide coordinates: <box>x1,y1,x2,y2</box>"
            response = await self._run_in_executor(
                self.vision.describe_image, image_path, prompt
            )
            coords = self._parse_coordinates(response)
            
            if coords:
                result = {"x": (coords[0] + coords[2]) // 2, "y": (coords[1] + coords[3]) // 2}
                await self.context.set(f"vision:last_coords", result)
                return result
            return {}
        except Exception as e:
            await self._publish(
                EventType.VISION_ERROR,
                {"error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    # === AUDIO SCENARIOS ===
    
    async def audio_transcribe_async(self, audio_path: str) -> str:
        """Асинхронная транскрипция"""
        corr_id = self._generate_correlation_id()
        
        try:
            result = await self._run_in_executor(
                self.audio.transcribe, audio_path
            )
            
            await self.context.set(f"audio:last_transcription", {
                "path": audio_path,
                "text": result
            })
            
            await self._publish(
                EventType.AUDIO_TRANSCRIBED,
                {"path": audio_path, "text": result},
                source="orchestrator",
                correlation_id=corr_id
            )
            return result
        except Exception as e:
            await self._publish(
                EventType.AUDIO_ERROR,
                {"error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    async def audio_intent_async(self, audio_path: str) -> str:
        """Асинхронный анализ интента"""
        corr_id = self._generate_correlation_id()
        
        try:
            transcription = await self.audio_transcribe_async(audio_path)
            prompt = f"Analyze intent: '{transcription}'. What action should be taken?"
            
            result = await self._run_in_executor(
                self.coder.generate, prompt
            )
            
            await self._publish(
                EventType.AUDIO_INTENT,
                {"transcription": transcription, "intent": result},
                source="orchestrator",
                correlation_id=corr_id
            )
            return result
        except Exception as e:
            await self._publish(
                EventType.AUDIO_ERROR,
                {"error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    # === CODER SCENARIOS ===
    
    async def coder_generate_async(self, prompt: str, context: str = "") -> str:
        """Асинхронная генерация кода"""
        corr_id = self._generate_correlation_id()
        
        try:
            await self._publish(
                EventType.CODER_GENERATING,
                {"prompt": prompt[:100], "context": context[:100]},
                source="orchestrator",
                correlation_id=corr_id
            )
            
            result = await self._run_in_executor(
                self.coder.generate, prompt, context
            )
            
            await self._publish(
                EventType.CODER_COMPLETE,
                {"result": result[:500]},
                source="orchestrator",
                correlation_id=corr_id
            )
            return result
        except Exception as e:
            await self._publish(
                EventType.CODER_ERROR,
                {"error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    async def coder_explain_async(self, code: str) -> str:
        """Асинхронное объяснение кода"""
        return await self.coder_generate_async(f"Explain this code:\n\n```python\n{code}\n```")
    
    async def coder_debug_async(self, code: str, error: str = "") -> str:
        """Асинхронная отладка кода"""
        prompt = f"Debug this code"
        if error:
            prompt += f". Error: {error}"
        prompt += f":\n\n```python\n{code}\n```"
        return await self.coder_generate_async(prompt)
    
    # === WORKFLOWS ===
    
    async def workflow_voice_control_async(self, audio_path: str) -> Dict[str, Any]:
        """Голосовое управление: Audio → Intent → Action"""
        corr_id = self._generate_correlation_id()
        
        await self._publish(
            EventType.WORKFLOW_STARTED,
            {"workflow": "voice_control", "audio_path": audio_path},
            source="orchestrator",
            correlation_id=corr_id
        )
        
        try:
            transcription = await self.audio_transcribe_async(audio_path)
            intent = await self.audio_intent_async(audio_path)
            
            action = self._parse_action(intent)
            action_result = None
            if action:
                action_result = await self._run_in_executor(
                    self.tools.execute, action["tool"], **action.get("params", {})
                )
            
            result = {
                "transcription": transcription,
                "intent": intent,
                "action_result": action_result
            }
            
            await self._publish(
                EventType.WORKFLOW_COMPLETE,
                {"workflow": "voice_control", "result": result},
                source="orchestrator",
                correlation_id=corr_id
            )
            return result
        except Exception as e:
            await self._publish(
                EventType.WORKFLOW_ERROR,
                {"workflow": "voice_control", "error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    async def workflow_screen_to_action_async(self, element: str) -> Dict[str, Any]:
        """Скриншот → Vision → Клик"""
        corr_id = self._generate_correlation_id()
        
        await self._publish(
            EventType.WORKFLOW_STARTED,
            {"workflow": "screen_to_action", "element": element},
            source="orchestrator",
            correlation_id=corr_id
        )
        
        try:
            screenshot = await self.vision_capture_async()
            analysis = await self.vision_analyze_async(screenshot, "analyze_ui")
            coords = await self.vision_find_element_async(screenshot, element)
            
            click_result = None
            if coords:
                click_result = await self._run_in_executor(
                    self.tools.execute, "mouse_click", x=coords["x"], y=coords["y"]
                )
            
            result = {
                "screenshot": screenshot,
                "analysis": analysis,
                "click_result": click_result
            }
            
            await self._publish(
                EventType.WORKFLOW_COMPLETE,
                {"workflow": "screen_to_action", "result": result},
                source="orchestrator",
                correlation_id=corr_id
            )
            return result
        except Exception as e:
            await self._publish(
                EventType.WORKFLOW_ERROR,
                {"workflow": "screen_to_action", "error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    async def workflow_document_processing_async(self, image_path: str) -> Dict[str, Any]:
        """Документ → OCR → База знаний"""
        corr_id = self._generate_correlation_id()
        
        await self._publish(
            EventType.WORKFLOW_STARTED,
            {"workflow": "document_processing", "path": image_path},
            source="orchestrator",
            correlation_id=corr_id
        )
        
        try:
            text = await self._run_in_executor(self.vision.read_text, image_path)
            summary = await self.coder_generate_async(f"Summarize this document:\n\n{text}")
            
            await self._run_in_executor(
                self.tools.execute, "db_store", key=f"doc_{len(text)}", value={"text": text, "summary": summary}
            )
            
            result = {"text": text, "summary": summary}
            
            await self._publish(
                EventType.WORKFLOW_COMPLETE,
                {"workflow": "document_processing", "result": result},
                source="orchestrator",
                correlation_id=corr_id
            )
            return result
        except Exception as e:
            await self._publish(
                EventType.WORKFLOW_ERROR,
                {"workflow": "document_processing", "error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    async def workflow_auto_navigation_async(self, target: str, max_steps: int = 5) -> List[Dict]:
        """Авто-навигация: Vision → Action → Vision (loop)"""
        corr_id = self._generate_correlation_id()
        results = []
        
        await self._publish(
            EventType.WORKFLOW_STARTED,
            {"workflow": "auto_navigation", "target": target},
            source="orchestrator",
            correlation_id=corr_id
        )
        
        try:
            for step in range(max_steps):
                await self._publish(
                    EventType.WORKFLOW_STEP,
                    {"step": step, "target": target},
                    source="orchestrator",
                    correlation_id=corr_id
                )
                
                screenshot = await self.vision_capture_async()
                analysis = await self.vision_analyze_async(screenshot, f"Find path to: {target}")
                
                if target.lower() in analysis.lower():
                    results.append({"step": step, "status": "found", "analysis": analysis})
                    break
                
                coords = await self.vision_find_element_async(screenshot, "next button")
                if coords:
                    await self._run_in_executor(
                        self.tools.execute, "mouse_click", x=coords["x"], y=coords["y"]
                    )
                    results.append({"step": step, "action": "click_next", "coords": coords})
                    await asyncio.sleep(1)
                else:
                    results.append({"step": step, "status": "stuck", "analysis": analysis})
                    break
            
            await self._publish(
                EventType.WORKFLOW_COMPLETE,
                {"workflow": "auto_navigation", "results": results},
                source="orchestrator",
                correlation_id=corr_id
            )
            return results
        except Exception as e:
            await self._publish(
                EventType.WORKFLOW_ERROR,
                {"workflow": "auto_navigation", "error": str(e)},
                source="orchestrator",
                correlation_id=corr_id
            )
            raise
    
    # === UTILS ===
    
    async def _run_in_executor(self, func, *args, **kwargs):
        """Запустить синхронную функцию в executor"""
        loop = asyncio.get_event_loop()
        if kwargs:
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return await loop.run_in_executor(None, func, *args)
    
    def _parse_coordinates(self, text: str) -> Optional[List[int]]:
        """Парсинг координат из ответа"""
        match = re.search(r'<box>(\d+),(\d+),(\d+),(\d+)</box>', text)
        if match:
            return [int(match.group(i)) for i in range(1, 5)]
        return None
    
    def _parse_action(self, intent: str) -> Optional[Dict]:
        """Парсинг JSON действия из ответа"""
        try:
            match = re.search(r'\{[^}]*"tool"[^}]*\}', intent)
            if match:
                return json.loads(match.group())
        except:
            pass
        return None
