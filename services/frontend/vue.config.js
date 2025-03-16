module.exports = {
  devServer: {
    allowedHosts: 'all',
    hot: false,
    liveReload: false,
    webSocketServer: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'
        }
      }
    }
  }
} 