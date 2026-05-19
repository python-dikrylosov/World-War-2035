"""
Models Manager - Загрузка и работа с 3 Qwen моделями
"""
import torch
from transformers import AutoModelForCausalLM, AutoProcessor, AutoTokenizer
from PIL import Image
import soundfile as sf
import numpy as np
from typing import Optional, Dict, Any


class ModelLoader:
    """Синглтон для загрузки моделей с кэшированием"""
    _instances = {}
    
    @classmethod
    def get_instance(cls, model_type: str, config: dict):
        if model_type not in cls._instances:
            if model_type == "vision":
                cls._instances[model_type] = Qwen25VL(config)
            elif model_type == "coder":
                cls._instances[model_type] = Qwen3Coder(config)
            elif model_type == "audio":
                cls._instances[model_type] = Qwen2Audio(config)
        return cls._instances[model_type]


class Qwen25VL:
    """Qwen2.5-VL-7B-Instruct для анализа изображений и видео"""
    
    def __init__(self, config: dict):
        self.config = config
        self.device = config.get("device", "cuda:0")
        self.model_name = config.get("name", "Qwen/Qwen2.5-VL-7B-Instruct")
        self.model = None
        self.processor = None
        self._load()
    
    def _load(self):
        print(f"Loading Vision model: {self.model_name} on {self.device}")
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map=self.device,
            trust_remote_code=True,
            attn_implementation="eager",
            torch_dtype=torch.float16 if self.device.startswith("cuda") else torch.float32
        )
        print("Vision model loaded successfully")
    
    def describe_image(self, image_path: str, prompt: str = "Describe this image") -> str:
        image = Image.open(image_path).convert("RGB")
        messages = [
            {"role": "user", "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt}
            ]}
        ]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[image], return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(**inputs, max_new_tokens=512)
        response = self.processor.decode(generated_ids[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        return response
    
    def read_text(self, image_path: str) -> str:
        return self.describe_image(image_path, "Extract all text from this image (OCR)")
    
    def analyze_document(self, image_path: str) -> str:
        return self.describe_image(image_path, "Analyze this document: structure, content, key information")
    
    def compare_images(self, image1_path: str, image2_path: str, prompt: str = "Compare these images") -> str:
        image1 = Image.open(image1_path).convert("RGB")
        image2 = Image.open(image2_path).convert("RGB")
        messages = [
            {"role": "user", "content": [
                {"type": "image", "image": image1},
                {"type": "image", "image": image2},
                {"type": "text", "text": prompt}
            ]}
        ]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[image1, image2], return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(**inputs, max_new_tokens=512)
        response = self.processor.decode(generated_ids[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        return response


class Qwen3Coder:
    """Qwen3-Coder-30B-A3B-Instruct для работы с кодом"""
    
    def __init__(self, config: dict):
        self.config = config
        self.device = config.get("device", "cpu")
        self.model_name = config.get("name", "Qwen/Qwen3-Coder-30B-A3B-Instruct")
        self.temperature = config.get("temperature", 0.7)
        self.model = None
        self.tokenizer = None
        self._load()
    
    def _load(self):
        print(f"Loading Coder model: {self.model_name} on {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto" if self.device == "cuda:0" else None,
            trust_remote_code=True,
            attn_implementation="eager",
            torch_dtype=torch.float16 if self.device.startswith("cuda") else torch.float32
        )
        if self.device == "cpu":
            self.model = self.model.to("cpu")
        print("Coder model loaded successfully")
    
    def generate(self, prompt: str, context: str = "") -> str:
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=self.temperature,
            do_sample=True,
            top_p=0.95
        )
        response = self.tokenizer.decode(generated_ids[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        return response
    
    def chat(self, messages: list) -> str:
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=self.temperature,
            do_sample=True,
            top_p=0.95
        )
        response = self.tokenizer.decode(generated_ids[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        return response
    
    def explain_code(self, code: str) -> str:
        return self.generate(f"Explain this code:\n\n```python\n{code}\n```")
    
    def debug_code(self, code: str, error: str = "") -> str:
        prompt = f"Debug this code"
        if error:
            prompt += f". Error: {error}"
        prompt += f":\n\n```python\n{code}\n```"
        return self.generate(prompt)


class Qwen2Audio:
    """Qwen2-Audio-7B-Instruct для работы с аудио"""
    
    def __init__(self, config: dict):
        self.config = config
        self.device = config.get("device", "cuda:0")
        self.model_name = config.get("name", "Qwen/Qwen2-Audio-7B-Instruct")
        self.model = None
        self.processor = None
        self._load()
    
    def _load(self):
        print(f"Loading Audio model: {self.model_name} on {self.device}")
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map=self.device,
            trust_remote_code=True,
            attn_implementation="eager",
            torch_dtype=torch.float16 if self.device.startswith("cuda") else torch.float32
        )
        print("Audio model loaded successfully")
    
    def transcribe(self, audio_path: str) -> str:
        audio, sampling_rate = sf.read(audio_path)
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
        audio = (audio * 32768).astype(np.int16)
        
        messages = [
            {"role": "user", "content": [
                {"type": "audio", "audio_url": audio_path},
                {"type": "text", "text": "Transcribe this audio"}
            ]}
        ]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=text, audios=[audio], sampling_rate=sampling_rate, return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(**inputs, max_new_tokens=512)
        response = self.processor.decode(generated_ids[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        return response
    
    def analyze_audio(self, audio_path: str, task: str = "transcribe") -> str:
        if task == "transcribe":
            return self.transcribe(audio_path)
        elif task == "intent":
            transcription = self.transcribe(audio_path)
            return self._analyze_intent(transcription)
        elif task == "summarize":
            transcription = self.transcribe(audio_path)
            return self._summarize(transcription)
        return ""
    
    def _analyze_intent(self, text: str) -> str:
        prompt = f"Analyze the intent of this voice command: '{text}'. What action should be taken?"
        return prompt  # Requires coder model for actual analysis
    
    def _summarize(self, text: str) -> str:
        prompt = f"Summarize this transcription: '{text}'"
        return prompt  # Requires coder model for actual analysis
