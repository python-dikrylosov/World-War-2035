"""
Prompts - Оптимизированные промпты для каждой модели
"""

VISION_SYSTEM_PROMPT = """You are Qwen2.5-VL, an expert visual analysis AI.
Analyze images, screenshots, documents, and UI elements with precision.
Extract text, identify objects, understand layouts, and provide detailed descriptions.
When finding UI elements, provide coordinates in format: <box>x1,y1,x2,y2</box>"""

CODER_SYSTEM_PROMPT = """You are Qwen3-Coder, an expert programming assistant.
Write clean, efficient, well-documented code.
Debug issues, explain concepts, review code quality, and optimize performance.
Support multiple languages with focus on Python, JavaScript, and shell scripts."""

AUDIO_SYSTEM_PROMPT = """You are Qwen2-Audio, an expert audio analysis AI.
Transcribe speech accurately, analyze tone and intent, summarize conversations.
Identify commands, emotions, and key information from audio input."""


def get_vision_prompt(task: str) -> str:
    prompts = {
        "describe": "Describe this image in detail. What do you see?",
        "ocr": "Extract all text from this image. Preserve formatting where possible.",
        "find_element": "Find the '{element}' element in this screenshot. Provide coordinates: <box>x1,y1,x2,y2</box>",
        "analyze_ui": "Analyze this UI screenshot. Identify all interactive elements, their purposes, and current state.",
        "compare": "Compare these two images. What are the differences?",
        "document": "Analyze this document. Extract structure, key sections, and important information."
    }
    return prompts.get(task, prompts["describe"])


def get_coder_prompt(task: str) -> str:
    prompts = {
        "generate": "Generate code for: {task}",
        "explain": "Explain this code step by step:\n{code}",
        "debug": "Debug this code. Find and fix the issue:\n{code}\nError: {error}",
        "optimize": "Optimize this code for performance and readability:\n{code}",
        "review": "Review this code. Identify issues, suggest improvements:\n{code}",
        "convert": "Convert this code from {from_lang} to {to_lang}:\n{code}"
    }
    return prompts.get(task, prompts["generate"])


def get_audio_prompt(task: str) -> str:
    prompts = {
        "transcribe": "Transcribe this audio exactly as spoken.",
        "intent": "What is the speaker's intent? What action do they want?",
        "summarize": "Summarize the key points from this audio.",
        "sentiment": "Analyze the speaker's emotional state and tone.",
        "commands": "Extract any commands or requests from this audio.",
        "language": "Identify the language and dialect used in this audio."
    }
    return prompts.get(task, prompts["transcribe"])
