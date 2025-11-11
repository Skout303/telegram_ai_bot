import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
import PyPDF2
from docx import Document as DocxDocument

import telegram

# Проверка версии python-telegram-bot
print(f"🚀 python-telegram-bot version: {telegram.__version__}")
import openai

# 🚀 Проверка версии python-telegram-bot
current_ptb_version = tuple(map(int, telegram.__version__.split(".")))
required_ptb_version = (20, 7)

print(f"🚀 python-telegram-bot version detected: {telegram.__version__}")

if current_ptb_version < required_ptb_version:
    print("⚠️ ВНИМАНИЕ: Установлена устаревшая версия python-telegram-bot!")
    print("⚠️ Очисти build cache на Render и перезапусти деплой.")
else:
    print("✅ Версия python-telegram-bot корректна и готова к запуску!")

# 🤖 Проверка версии OpenAI SDK
try:
    openai_version = openai.__version__
    required_openai_version = (1, 12, 0)
    current_openai_version = tuple(map(int, openai_version.split(".")))

    print(f"🧠 openai SDK version detected: {openai_version}")

    if current_openai_version < required_openai_version:
        print("⚠️ ВНИМАНИЕ: Установлена устаревшая версия OpenAI SDK!")
        print("⚠️ Очисти build cache и перезапусти деплой.")
    else:
        print("✅ Версия OpenAI SDK корректна!")
except Exception as e:
    print(f"❌ Ошибка при проверке версии OpenAI: {e}")

# === Настройки ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MEMORY_FILE = "user_memory.json"

client = OpenAI(api_key=OPENAI_API_KEY)

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
        "👋 Привет! Я умный бот.\n\n"
        "📄 Могу читать PDF и DOCX.\n"
        "🖼️ Улучшаю фото и рисую картинки.\n"
        "💬 Помню контекст разговора.\n\n"
        "Напиши /help, чтобы узнать больше!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 <b>Помощь по командам</b>\n\n"
        "🧠 <b>/start</b> — начать работу\n"
        "💬 Просто напиши сообщение — бот ответит с учётом контекста\n"
        "📄 Отправь PDF, DOCX или TXT — бот прочитает файл\n"
        "🖼️ Отправь фото — бот улучшит или стилизует изображение\n"
        "🎨 <b>/draw [описание]</b> — нарисовать по тексту\n"
        "🧽 <b>/reset</b> — очистить память бота\n"
        "ℹ️ <b>/info</b> — показать инфо о возможностях\n"
        "❓ <b>/help</b> — показать это меню"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Я бот, который умеет:\n"
        "- Понимать контекст диалога 🧠\n"
        "- Читать и пересказывать файлы 📄\n"
        "- Работать с фото 🖼️\n"
        "- Рисовать по тексту 🎨"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in user_memory:
        del user_memory[user_id]
        save_memory(user_memory)
    await update.message.reply_text("🧠 Память очищена. Начинаем заново!")

# === Работа с файлами ===
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = await update.message.document.get_file()
    file_name = update.message.document.file_name
    path = f"user_{update.message.from_user.id}_{file_name}"
    await doc.download_to_drive(path)

    text = ""
    if file_name.endswith(".pdf"):
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = " ".join(page.extract_text() for page in reader.pages)
    elif file_name.endswith(".docx"):
        document = DocxDocument(path)
        text = "\n".join(p.text for p in document.paragraphs)
    elif file_name.endswith(".txt"):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        await update.message.reply_text("⚠️ Поддерживаются только PDF, DOCX и TXT.")
        os.remove(path)
        return

    os.remove(path)

    await update.message.reply_text("📚 Файл получен. Обрабатываю...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Кратко перескажи этот текст:\n{text[:4000]}"}],
    )

    summary = response.choices[0].message.content
    await update.message.reply_text(f"🧾 Резюме:\n\n{summary}")

# === Работа с изображениями ===
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    path = f"user_photo_{update.message.from_user.id}.jpg"
    await file.download_to_drive(path)
    await update.message.reply_text("🖼️ Фото получено! Обрабатываю...")

    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt="улучши изображение и добавь художественный стиль"
        )
        image_url = result.data[0].url
        await update.message.reply_photo(photo=image_url, caption="✨ Готово!")
    except Exception as e:
        print("Image error:", e)
        await update.message.reply_text("⚠️ Ошибка при обработке изображения.")

# === Генерация изображений по описанию ===
async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎨 Напиши, что нарисовать: /draw кот в шляпе")
        return

    prompt = " ".join(context.args)
    await update.message.reply_text(f"🖌️ Рисую: {prompt}...")
    try:
        result = client.images.generate(model="gpt-image-1", prompt=prompt)
        image_url = result.data[0].url
        await update.message.reply_photo(photo=image_url, caption="🎨 Готово!")
    except Exception as e:
        print("Draw error:", e)
        await update.message.reply_text("⚠️ Не удалось создать изображение.")

# === Общение с памятью ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append({"role": "user", "content": text})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=user_memory[user_id]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
        user_memory[user_id].append({"role": "assistant", "content": answer})
        save_memory(user_memory)
    except Exception as e:
        print("Chat error:", e)
        await update.message.reply_text("⚠️ Ошибка при обращении к OpenAI.")

# === Запуск ===
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

def main():
    print("🚀 Бот запускается...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("draw", draw))

    # обработка файлов и фото
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен и слушает Telegram...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()