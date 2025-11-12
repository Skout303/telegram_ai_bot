#!/bin/bash
echo "🚀 Установка Telegram AI бота начинается..."
sleep 1

# === Обновление системы
sudo apt update && sudo apt upgrade -y

# === Установка зависимостей
sudo apt install -y python3 python3-pip git screen

# === Проверка версий
echo "🐍 Python: $(python3 --version)"
echo "📦 Pip: $(pip --version)"
echo "🔧 Git: $(git --version)"

# === Клонирование репозитория
if [ ! -d "telegram_ai_bot" ]; then
  git clone https://github.com/Skout303/telegram_ai_bot.git
fi
cd telegram_ai_bot || exit

# === Создание .env
echo "🔐 Создание .env файла..."
read -p "Введите TELEGRAM_TOKEN: " TELEGRAM_TOKEN
read -p "Введите OPENAI_API_KEY: " OPENAI_API_KEY

cat > .env <<EOL
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
OPENAI_API_KEY=$OPENAI_API_KEY
EOL

# === Установка Python-зависимостей
echo "📦 Устанавливаем зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# === Запуск бота в screen (чтобы не останавливался)
echo "🟢 Запускаем бота в фоновом режиме..."
screen -dmS telegram_bot python3 bot.py

echo ""
echo "✅ Бот успешно установлен и запущен!"
echo "📡 Проверить запущенные процессы: screen -ls"
echo "👉 Вернуться к экрану: screen -r telegram_bot"
echo "❌ Выйти из него (не останавливая): Ctrl + A, затем D"
echo ""