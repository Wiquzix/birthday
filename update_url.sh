#!/bin/bash

# Функция для обновления .env файла
update_env_file() {
    local env_file=$1
    local tunnel_url=$2
    
    # Проверяем существование файла
    if [ ! -f "$env_file" ]; then
        echo "Предупреждение: Файл $env_file не найден"
        return
    fi
    
    # Создаем временный файл
    touch "${env_file}.tmp"
    
    # Копируем содержимое .env, заменяя или добавляя EXTERNAL_URL
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ $line == EXTERNAL_URL=* ]]; then
            echo "EXTERNAL_URL=$tunnel_url" >> "${env_file}.tmp"
        else
            echo "$line" >> "${env_file}.tmp"
        fi
    done < "$env_file"
    
    # Проверяем, был ли добавлен EXTERNAL_URL
    if ! grep -q "^EXTERNAL_URL=" "${env_file}.tmp"; then
        echo "EXTERNAL_URL=$tunnel_url" >> "${env_file}.tmp"
    fi
    
    # Заменяем оригинальный файл
    mv "${env_file}.tmp" "$env_file"
    echo "URL обновлен в файле $env_file: $tunnel_url"
}

# Функция для отправки сообщения в BotFather
update_botfather() {
    local tunnel_url=$1
    
    echo "============================================="
    echo "Инструкции для обновления URL в BotFather:"
    echo "1. Откройте @BotFather в Telegram"
    echo "2. Отправьте команду /editapp"
    echo "3. Отправьте ссылку: https://t.me/WiquzixBot/wiquzix"
    echo "4. Нажимайте /skip для пропуска изменения:"
    echo "   - заголовка"
    echo "   - описания"
    echo "   - фото"
    echo "   - GIF"
    echo "5. Когда BotFather попросит новый URL, отправьте:"
    echo "$tunnel_url"
    echo "============================================="
    
    # Копируем URL в буфер обмена, если возможно
    if command -v pbcopy > /dev/null; then
        echo -n "$tunnel_url" | pbcopy
        echo "URL скопирован в буфер обмена!"
    fi
    
    # Спрашиваем пользователя, хочет ли он обновить URL в BotFather
    read -p "Хотите обновить URL в BotFather? (y/n): " update_botfather_choice
    if [[ $update_botfather_choice == "y" ]]; then
        echo "Нажмите Enter, когда закончите обновление URL в BotFather..."
        read -r
    fi
}

# Функция для перезапуска контейнеров
restart_containers() {
    local tunnel_url=$1
    
    # Спрашиваем пользователя, хочет ли он перезапустить контейнеры
    read -p "Хотите перезапустить контейнеры? (y/n): " restart_choice
    if [[ $restart_choice == "y" ]]; then
        echo "Перезапуск контейнеров..."
        docker-compose down
        docker-compose up -d
        echo "Контейнеры перезапущены с новым URL: $tunnel_url"
    else
        echo "Не забудьте перезапустить контейнеры вручную для применения нового URL."
    fi
}

# Очищаем старый лог
rm -f /tmp/cloudflared_output.log
touch /tmp/cloudflared_output.log

echo "Запуск Cloudflare туннеля..."
echo "Для остановки туннеля нажмите Ctrl+C"

# Запускаем cloudflared и обрабатываем вывод
cloudflared tunnel --url http://localhost:8080 2>&1 | while IFS= read -r line; do
    echo "$line"
    if [[ $line == *"Your quick Tunnel has been created"* ]]; then
        # Читаем следующую строку, которая содержит URL
        read -r url_line
        echo "$url_line"
        
        # Извлекаем URL из строки
        TUNNEL_URL=$(echo "$url_line" | grep -o 'https://[^[:space:]]*\.trycloudflare\.com')
        
        if [ -n "$TUNNEL_URL" ]; then
            echo "Найден URL: $TUNNEL_URL"
            
            # Обновляем .env файлы
            update_env_file ".env" "$TUNNEL_URL"
            update_env_file "services/backend/.env" "$TUNNEL_URL"
            update_env_file "services/bot/.env" "$TUNNEL_URL"
            
            # Обновляем URL в BotFather
            update_botfather "$TUNNEL_URL"
            
            # Перезапускаем контейнеры
            restart_containers "$TUNNEL_URL"
            
            echo "Туннель активен. Для остановки нажмите Ctrl+C"
        fi
    fi
done 