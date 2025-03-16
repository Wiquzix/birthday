const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const port = process.env.PORT || 8080;

// Определяем URL бэкенда из переменной окружения или используем значение по умолчанию
const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';

// Настраиваем прокси для API запросов
app.use('/api', createProxyMiddleware({
  target: backendUrl,
  changeOrigin: true,
  pathRewrite: {
    '^/api': '/api' // Не изменяем путь
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`Proxying request to: ${backendUrl}${proxyReq.path}`);
  },
  onError: (err, req, res) => {
    console.error('Proxy error:', err);
    res.status(500).send('Proxy error');
  }
}));

// Статические файлы из директории dist
app.use(express.static(path.join(__dirname, 'dist')));

// Все остальные запросы направляем на index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

// Запускаем сервер
app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
  console.log(`Backend URL: ${backendUrl}`);
}); 