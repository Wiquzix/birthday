FROM node:16-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Сначала собираем приложение
RUN npm run build

EXPOSE 8080

# Запускаем только server.js
CMD ["node", "server.js"] 