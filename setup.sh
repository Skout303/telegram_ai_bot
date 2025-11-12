#!/bin/bash
echo "🚀 Установка Telegram AI бота начинается..."
sleep 1

# === Обновление системы
sudo apt update && sudo apt upgrade -y

# === Установка зависимостей
sudo apt install -y python3 python3-pip git

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

# === Создаём systemd unit для автозапуска
SERVICE_FILE="/etc/systemd/system/telegram_bot.service"

echo "🛠️ Настраиваем автозапуск через systemd..."
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/bot.py
Restart=always
EnvironmentFile=$(pwd)/.env

[Install]
WantedBy=multi-user.target
EOF

# === Перезапуск systemd и включение автозапуска
sudo systemctl daemon-reload
sudo systemctl enable telegram_bot
sudo systemctl start telegram_bot

echo ""
echo "✅ Бот успешно установлен и запущен как systemd-сервис!"
echo "📡 Проверить статус: sudo systemctl status telegram_bot"
echo "🔁 Перезапустить: sudo systemctl restart telegram_bot"
echo "🛑 Остановить: sudo systemctl stop telegram_bot"
echo ""
