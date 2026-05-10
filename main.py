import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def main():
    print("=== Этап 1: Базовый цикл ===")
    
    # 1. Инициализация модели и токенизатора
    model_name = "distilgpt2"
    print(f"Загрузка модели: {model_name}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    
    # Устанавливаем режим оценки
    model.eval()
    
    # Начальный промпт
    input_text = "Hello, I am an AI assistant."
    print(f"Входной текст: {input_text}")
    
    inputs = tokenizer.encode(input_text, return_tensors="pt")
    
    # 2. Простой цикл генерации
    print("\nГенерация продолжения текста...")
    with torch.no_grad():
        outputs = model.generate(
            inputs, 
            max_new_tokens=50, 
            do_sample=True, 
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Результат:\n{generated_text}")
    
    print("\n=== Этап 1 завершен ===")
    print("Далее будет добавлен чат-бот интерфейс.")

if __name__ == "__main__":
    main()
