import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update, Document
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import PyPDF2
from docx import Document as DocxDocument

# === Настройки ===
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)
MEMORY_FILE = "memory.json"

# === Память ===
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_memory = load_memory()

# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Отправь мне текст или файл (PDF, TXT, DOCX) — я его запомню. "
        "Потом можешь спрашивать что угодно про его содержимое.\n\n"
        "Команды:\n"
        "📘 /info — показать, что я помню\n"
        "🧹 /reset — очистить память"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_memory[user_id] = []
    save_memory(user_memory)
    await update.message.reply_text("🧹 Память очищена!")

# 🆕 === Новая команда /info ===
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id not in user_memory or len(user_memory[user_id]) == 0:
        await update.message.reply_text("🕳 Я пока ничего не помню. Пришли файл или сообщение.")
        return

    system_msgs = [m for m in user_memory[user_id] if m["role"] == "system"]
    last_system = system_msgs[-1]["content"] if system_msgs else ""
    text_length = len(last_system)

    await update.message.reply_text(
        f"🧠 В памяти сейчас:\n"
        f"- Сообщений: {len(user_memory[user_id])}\n"
        f"- Размер контекста: {text_length} символов\n\n"
        f"📄 Я храню краткое содержимое последнего загруженного файла.\n"
        f"Чтобы очистить память, используй /reset."
    )

# === Чтение файлов ===
def read_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    elif ext == ".docx":
        doc = DocxDocument(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    else:
        text = "❌ Формат файла не поддерживается."

    return text.strip()

# === Обработка файлов ===
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    doc: Document = update.message.document

    file = await doc.get_file()
    file_path = f"temp_{user_id}_{doc.file_name}"
    await file.download_to_drive(file_path)

    try:
        content = read_file(file_path)
        if not content:
            await update.message.reply_text("Файл пуст или не читается 😢")
            return

        # Запоминаем содержимое файла как контекст
        user_memory[user_id] = [{"role": "system", "content": f"Вот содержимое загруженного файла:\n\n{content[:8000]}"}]
        save_memory(user_memory)

        await update.message.reply_text(
            f"📘 Я прочитал и запомнил файл: {doc.file_name}\n"
            f"Теперь можешь задавать вопросы по его содержимому!"
        )

    except Exception as e:
        await update.message.reply_text("⚠️ Ошибка при обработке файла.")
        print(f"File read error: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# === Обработка текстовых сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append({"role": "user", "content": text})

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=user_memory[user_id],
        )

        reply = completion.choices[0].message.content
        await update.message.reply_text(reply)

        user_memory[user_id].append({"role": "assistant", "content": reply})
        save_memory(user_memory)

    except Exception as e:
        await update.message.reply_text("⚠️ Ошибка при обращении к OpenAI API.")
        print(f"OpenAI error: {e}")

# === Основной запуск ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("info", info))  # 🆕 добавили сюда
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот с памятью и командой /info запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
