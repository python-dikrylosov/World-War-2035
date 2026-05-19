"""
Скрипт для публикации Qwen Multimodal Assistant на Hugging Face Hub.

Использование:
    python push_to_hub.py --repo-id your-username/qwen-multimodal-assistant

Требования:
    pip install huggingface_hub
    huggingface-cli login  (или установи переменную окружения HF_TOKEN)
"""

import argparse
from huggingface_hub import HfApi, create_repo
from pathlib import Path
import os

def main():
    parser = argparse.ArgumentParser(description="Push Qwen Multimodal Assistant to HF Hub")
    parser.add_argument("--repo-id", type=str, required=True, help="Repo ID: username/repo-name")
    parser.add_argument("--token", type=str, default=None, help="HF Token (or set HF_TOKEN env var)")
    parser.add_argument("--private", action="store_true", help="Make repo private")
    
    args = parser.parse_args()
    
    api = HfApi()
    
    # Проверка токена
    token = args.token or os.getenv("HF_TOKEN")
    if not token:
        print("❌ Ошибка: Токен не найден. Запустите 'huggingface-cli login' или задайте HF_TOKEN")
        return

    print(f"🚀 Подготовка к загрузке в {args.repo_id}...")
    
    # Создаем репозиторий
    try:
        create_repo(repo_id=args.repo_id, token=token, private=args.private, exist_ok=True, repo_type="model")
        print(f"✅ Репозиторий создан/найден: https://huggingface.co/{args.repo_id}")
    except Exception as e:
        print(f"❌ Ошибка создания репозитория: {e}")
        return

    # Список файлов для загрузки (исключаем модели, кэш, temp)
    root_dir = Path(__file__).parent
    ignore_patterns = [
        "models/*", 
        "data/knowledge.json", 
        "__pycache__/", 
        "*.pyc", 
        ".venv/", 
        "venv/", 
        "temp_*.png", 
        "lab_*.png",
        ".git",
        "push_to_hub.py"
    ]
    
    print("📦 Загрузка файлов...")
    
    try:
        api.upload_folder(
            folder_path=str(root_dir),
            repo_id=args.repo_id,
            repo_type="model",
            token=token,
            ignore_patterns=ignore_patterns,
            commit_message="Upload Qwen Multimodal Assistant project"
        )
        print(f"✅ Успешно загружено!")
        print(f"🔗 Ссылка: https://huggingface.co/{args.repo_id}")
        print("\n📝 Инструкция для пользователей:")
        print(f"   git lfs install")
        print(f"   git clone https://huggingface.co/{args.repo_id}")
        print(f"   cd {args.repo_id.split('/')[-1]}")
        print(f"   pip install -r requirements.txt")
        print(f"   # Скачайте модели вручную в папку models/")
        print(f"   python app.py")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")

if __name__ == "__main__":
    main()
