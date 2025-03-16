<!-- 
  Главный компонент приложения, который управляет состоянием и отображением.
  Поддерживает два основных режима:
  1. Ввод даты рождения (BirthdayForm)
  2. Отображение информации о пользователе (UserInfo)
  
  Также поддерживает режим шаринга, когда пользователь открывает приложение по ссылке.
-->
<template>
  <div id="app" :style="{ backgroundColor: backgroundColor }">
    <!-- Индикатор загрузки -->
    <div v-if="loading" class="loading">
      Загрузка...
    </div>
    
    <!-- Сообщение об ошибке -->
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    
    <!-- Режим шаринга - показываем информацию о пользователе, который поделился данными -->
    <div v-else-if="sharedMode" class="shared-mode">
      <UserInfo :userInfo="userInfo" :birthday="birthday" />
    </div>
    
    <!-- Режим ввода даты рождения -->
    <div v-else-if="!birthdaySet">
      <BirthdayForm @submit="setBirthday" />
    </div>
    
    <!-- Обычный режим - показываем информацию о текущем пользователе -->
    <div v-else>
      <UserInfo :userInfo="userInfo" :birthday="birthday" />
    </div>
  </div>
</template>

<script>
import BirthdayForm from './components/BirthdayForm.vue'
import UserInfo from './components/UserInfo.vue'

export default {
  name: 'App',
  components: {
    BirthdayForm,
    UserInfo
  },
  data() {
    return {
      // Информация о пользователе
      userInfo: {},
      // Дата рождения пользователя
      birthday: '',
      // Флаг, указывающий, что дата рождения установлена
      birthdaySet: false,
      // Флаг загрузки
      loading: true,
      // Сообщение об ошибке
      error: null,
      // Флаг режима шаринга
      sharedMode: false,
      // Цвет фона из Telegram WebApp
      backgroundColor: '#ffffff',
      // Флаг доступности Telegram WebApp
      isValidWebApp: false,
      // Объект Telegram WebApp
      tg: null
    }
  },
  methods: {
    /**
     * Устанавливает дату рождения пользователя
     * @param {string} date - Дата рождения в формате YYYY-MM-DD
     */
    setBirthday(date) {
      this.birthday = date;
      this.birthdaySet = true;
    },
    
    /**
     * Проверяет наличие параметра share_id в URL или в start_param
     * Если параметр найден, загружает данные с сервера
     */
    async checkForSharedData() {
      // Проверяем наличие параметра share_id в URL или в startapp
      const tg = window.Telegram?.WebApp;
      let shareId = null;
      
      // Проверяем start_param из Telegram WebApp
      if (tg?.initDataUnsafe?.start_param) {
        const startParam = tg.initDataUnsafe.start_param;
        
        if (startParam.startsWith('share_')) {
          shareId = startParam.substring(6);
        }
      } else {
        // Проверяем URL параметры (для тестирования)
        const urlParams = new URLSearchParams(window.location.search);
        shareId = urlParams.get('share_id');
      }
      
      // Дополнительная проверка для startapp в URL
      if (!shareId && window.location.href.includes('startapp=')) {
        const match = window.location.href.match(/startapp=share_([^&]+)/);
        if (match && match[1]) {
          shareId = match[1];
        }
      }
      
      // Если найден shareId, загружаем данные
      if (shareId) {
        try {
          // Получаем базовый URL для API
          const apiUrl = window.location.origin + '/api';
          console.log('URL API для загрузки данных:', apiUrl);
          
          const response = await fetch(`${apiUrl}/share/${shareId}`);
          if (!response.ok) {
            throw new Error('Не удалось загрузить данные');
          }
          
          const data = await response.json();
          
          // Устанавливаем данные из шаринга
          this.userInfo = data.user;
          this.birthday = data.share.birthday;
          this.birthdaySet = true;
          this.sharedMode = true;
        } catch (error) {
          this.error = `Ошибка: ${error.message}`;
        }
      }
    }
  },
  async mounted() {
    try {
      // Инициализация Telegram WebApp
      const tg = window.Telegram?.WebApp;
      if (tg) {
        this.tg = tg;
        this.isValidWebApp = true;
        
        // Инициализация Telegram Web App
        tg.ready();
        tg.expand();
        
        // Используем цвет темы из Telegram
        this.backgroundColor = tg.backgroundColor || '#ffffff';
      }
      
      // Проверяем наличие данных из шаринга
      await this.checkForSharedData();
      
      // Если не в режиме шаринга, получаем данные пользователя из Telegram
      if (!this.sharedMode) {
        if (tg) {
          this.userInfo = tg.initDataUnsafe?.user || {};
        } else {
          // Для тестирования без Telegram
          this.userInfo = {
            first_name: 'Тестовый',
            last_name: 'Пользователь',
            username: 'test_user'
          };
        }
      }
      
      // Завершаем загрузку
      this.loading = false;
    } catch (error) {
      console.error('Ошибка при инициализации:', error);
      this.error = `Ошибка: ${error.message}`;
      this.loading = false;
    }
  }
}
</script>

<style>
/* Основной контейнер приложения */
#app {
  font-family: 'Roboto', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--tg-theme-text-color, #000000);
  background-color: var(--tg-theme-bg-color, #ffffff);
  min-height: 100vh;
  padding: 16px;
}

/* Индикатор загрузки и сообщение об ошибке */
.loading, .error {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  text-align: center;
  padding: 20px;
}

/* Сообщение об ошибке */
.error {
  color: var(--tg-theme-destructive-text-color, #ff3b30);
}

/* Контейнер для режима шаринга */
.shared-mode {
  padding: 10px;
}

/* Заголовки */
h2 {
  color: var(--tg-theme-text-color, #000000);
  text-align: center;
  margin-bottom: 20px;
}
</style>
  
  