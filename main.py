import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def main():
    print("=== Этап 2: Чат-бот с историей диалога ===")

    # 1. Инициализация модели и токенизатора
    model_name = "distilgpt2"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Загрузка модели: {model_name}... (Устройство: {device})")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    # Устанавливаем pad_token, так как у distilgpt2 его нет по умолчанию
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    model.eval()

    # Системный промпт (инструкция для бота)
    system_prompt = "You are a helpful AI assistant."
    
    # История диалога
    conversation_history = f"{system_prompt}\n"

    print("\nЧат-бот запущен! (Введите 'quit' для выхода)")
    print("-" * 40)

    while True:
        # 2. Получаем ввод от пользователя
        try:
            user_input = input("\nВы: ")
        except (EOFError, KeyboardInterrupt):
            print("\nБот: До свидания!")
            break
            
        if user_input.lower() in ["quit", "exit", "выход"]:
            print("Бот: До свидания!")
            break

        # 3. Формируем полный контекст диалога
        # Добавляем реплику пользователя в историю
        conversation_history += f"User: {user_input}\nBot: "

        # 4. Токенизация входных данных
        inputs = tokenizer.encode(conversation_history, return_tensors="pt").to(device)

        # Ограничение длины входа, чтобы не переполнить память
        max_input_length = 512
        if inputs.shape[1] > max_input_length:
            # Если история слишком длинная, обрезаем начало
            inputs = inputs[:, -max_input_length:]
            conversation_history = tokenizer.decode(inputs[0], skip_special_tokens=True)

        # 5. Генерация ответа
        print("Бот: ", end="", flush=True)
        
        with torch.no_grad():
            output = model.generate(
                inputs,
                max_new_tokens=100,          # Сколько новых токенов генерировать
                temperature=0.7,             # Креативность
                top_p=0.9,                   # Разнообразие выбора
                do_sample=True,              # Использовать семплирование
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=2,      # Избегать повторений фраз
            )

        # 6. Декодирование и вывод
        full_response = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Выделяем только ответ бота (убираем историю из вывода)
        bot_reply = full_response.split("Bot: ")[-1].strip()
        
        # Очищаем ответ от возможных обрывков следующих реплик
        if "User:" in bot_reply:
            bot_reply = bot_reply.split("User:")[0].strip()

        print(bot_reply)

        # 7. Обновляем историю диалога полным ответом
        conversation_history += bot_reply + "\n"

if __name__ == "__main__":
    main()
