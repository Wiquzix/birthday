<!-- 
  Компонент UserInfo отображает информацию о пользователе и обратный отсчет до дня рождения.
  Поддерживает два режима:
  1. Обычный режим - показывает информацию о текущем пользователе
  2. Режим шаринга - показывает информацию о пользователе, который поделился данными
-->
<template>
  <div class="user-info">
    <!-- Сообщение об ошибке, если данные пользователя недоступны -->
    <div v-if="!isValidUserInfo && !sharedData" class="error-message">
      Ошибка: данные пользователя недоступны
    </div>
    
    <!-- Основной блок с информацией о пользователе -->
    <div v-else class="user-details" :class="{ 'shared-info': sharedData }">
      <h2>{{ sharedData ? 'Информация от пользователя' : 'Информация о пользователе' }}</h2>
      
      <!-- Информация о пользователе -->
      <div class="info-item">
        <span class="label">Имя:</span>
        <span class="value">{{ displayUserInfo.first_name }}</span>
      </div>
      <div class="info-item" v-if="displayUserInfo.last_name">
        <span class="label">Фамилия:</span>
        <span class="value">{{ displayUserInfo.last_name }}</span>
      </div>
      <div class="info-item" v-if="displayUserInfo.username">
        <span class="label">Username:</span>
        <span class="value">@{{ displayUserInfo.username }}</span>
      </div>
      
      <!-- Обратный отсчет до дня рождения -->
      <div class="birthday-countdown">
        <h3>До дня рождения осталось:</h3>
        <div class="countdown-values">
          <div class="countdown-item">
            <span class="count">{{ timeLeft.days }}</span>
            <span class="unit">дней</span>
          </div>
          <div class="countdown-item">
            <span class="count">{{ timeLeft.hours }}</span>
            <span class="unit">часов</span>
          </div>
          <div class="countdown-item">
            <span class="count">{{ timeLeft.minutes }}</span>
            <span class="unit">минут</span>
          </div>
        </div>
      </div>
      
      <!-- Индикатор отправки -->
      <div v-if="isSharing" class="sending-indicator">
        <div class="spinner"></div>
        <span>{{ sendingStatus }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserInfo',
  props: {
    // Информация о пользователе из Telegram WebApp
    userInfo: {
      type: Object,
      required: true
    },
    // Дата рождения пользователя
    birthday: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      // Оставшееся время до дня рождения
      timeLeft: {
        days: 0,
        hours: 0,
        minutes: 0
      },
      // Таймер для обновления обратного отсчета
      timer: null,
      // Флаг, указывающий, что идет процесс отправки данных
      isSharing: false,
      // Данные, полученные при шаринге (если есть)
      sharedData: null
    }
  },
  computed: {
    // Проверка валидности данных пользователя
    isValidUserInfo() {
      return this.userInfo && typeof this.userInfo === 'object' && 'first_name' in this.userInfo;
    },
    // Определение даты рождения в зависимости от режима (обычный или шаринг)
    currentBirthday() {
      return this.sharedData ? this.sharedData.share.birthday : this.birthday;
    },
    // Определение информации о пользователе в зависимости от режима
    displayUserInfo() {
      return this.sharedData ? this.sharedData.user : this.userInfo;
    }
  },
  methods: {
    /**
     * Рассчитывает оставшееся время до дня рождения
     * Устанавливает дни, часы и минуты в объект timeLeft
     */
    calculateTimeLeft() {
      try {
        const now = new Date()
        const birthDate = new Date(this.currentBirthday)
        
        // Создаем дату следующего дня рождения в текущем году
        const nextBirthday = new Date(now.getFullYear(), birthDate.getMonth(), birthDate.getDate())
        
        // Если день рождения в этом году уже прошел, берем следующий год
        if (nextBirthday < now) {
          nextBirthday.setFullYear(now.getFullYear() + 1)
        }
        
        // Рассчитываем разницу во времени
        const diff = nextBirthday - now
        
        // Обновляем данные для отображения
        this.timeLeft = {
          days: Math.floor(diff / (1000 * 60 * 60 * 24)),
          hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
          minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
        }
      } catch (error) {
        // В случае ошибки устанавливаем нули
        this.timeLeft = { days: 0, hours: 0, minutes: 0 };
      }
    },
    
    /**
     * Загружает данные по идентификатору шаринга
     * @param {string} shareId - Идентификатор шаринга
     */
    async loadSharedData(shareId) {
      try {
        // Получаем базовый URL для API
        const apiUrl = window.location.origin + '/api';
        console.log('URL API для загрузки данных:', apiUrl);
        
        const response = await fetch(`${apiUrl}/share/${shareId}`);
        if (!response.ok) {
          throw new Error('Не удалось загрузить данные');
        }
        this.sharedData = await response.json();
      } catch (error) {
        console.error('Error loading shared data:', error);
        this.sharedData = null;
      }
    },
    
    /**
     * Отправляет данные пользователя на сервер для шаринга
     * Использует Telegram WebApp API для отображения прогресса и уведомлений
     */
    async shareInfo() {
      // Проверяем доступность Telegram WebApp
      if (!window.Telegram?.WebApp) {
        return;
      }

      const tg = window.Telegram.WebApp;
      this.isSharing = true;

      try {
        // Показываем индикатор прогресса на кнопке
        tg.MainButton.showProgress();
        tg.MainButton.setText('Отправка...');

        // Генерируем уникальный идентификатор для шаринга
        const shareId = Math.random().toString(36).substring(2, 15);
        const chatId = tg.initDataUnsafe?.user?.id;

        if (!chatId) {
          throw new Error('Не удалось получить ID пользователя');
        }

        // Подготавливаем данные для отправки
        const shareData = {
          shareId: shareId,
          data: {
            birthday: this.birthday
          },
          chatId: chatId,
          userInfo: tg.initDataUnsafe.user
        };
        
        // Получаем базовый URL для API
        const apiUrl = window.location.origin + '/api';

        // Отправляем запрос на сервер
        const response = await fetch(`${apiUrl}/share`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(shareData)
        }).catch(error => {
          console.error('Ошибка fetch:', error);
          throw new Error(`Ошибка сети: ${error.message}`);
        });

        // Проверяем успешность запроса
        if (!response.ok) {
          const errorText = await response.text();
          console.error('Ошибка ответа:', response.status, errorText);
          throw new Error(`Ошибка сервера (${response.status}): ${errorText}`);
        }

        const responseData = await response.json();

        // Скрываем индикатор прогресса
        tg.MainButton.hideProgress();
        
        // Показываем уведомление об успехе
        tg.showPopup({
          title: 'Успех',
          message: 'Ссылка отправлена в чат.',
          buttons: [{type: 'close'}]
        });

        // Закрываем приложение после успешной отправки
        setTimeout(() => {
          tg.close();
        }, 1000);

      } catch (error) {
        // Обработка ошибки
        console.error('Ошибка при отправке данных:', error);
        tg.MainButton.hideProgress();
        tg.MainButton.setText('Поделиться');
        
        // Показываем уведомление об ошибке
        tg.showPopup({
          title: 'Ошибка',
          message: error.message || 'Не удалось отправить данные',
          buttons: [{type: 'close'}]
        });
      } finally {
        this.isSharing = false;
      }
    }
  },
  async mounted() {
    // Инициализация таймера для обратного отсчета
    this.calculateTimeLeft();
    this.timer = setInterval(this.calculateTimeLeft, 60000);
    
    // Настраиваем кнопку "Поделиться" только если не в режиме шаринга
    if (!this.sharedData && window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp;
      tg.MainButton.setText('Поделиться');
      tg.MainButton.show();
      tg.MainButton.onClick(() => this.shareInfo());
    }
  },
  beforeDestroy() {
    // Очищаем таймер при уничтожении компонента
    if (this.timer) {
      clearInterval(this.timer);
    }
    
    // Скрываем кнопку при уничтожении компонента
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.MainButton.hide();
    }
  }
}
</script>

<style scoped>
/* Основной контейнер */
.user-info {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Блок с информацией о пользователе */
.user-details {
  background-color: var(--tg-theme-secondary-bg-color, rgba(255, 255, 255, 0.08));
  padding: 20px;
  border-radius: 12px;
}

/* Стиль для режима шаринга */
.shared-info {
  border: 2px solid var(--tg-theme-button-color, #3390ec);
}

/* Сообщение об ошибке */
.error-message {
  color: var(--tg-theme-destructive-text-color, #ff3b30);
  text-align: center;
  padding: 20px;
  background-color: var(--tg-theme-secondary-bg-color, rgba(255, 255, 255, 0.08));
  border-radius: 8px;
  font-size: 14px;
  max-width: 100%;
}

/* Элемент информации о пользователе */
.info-item {
  margin: 10px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Метка поля */
.label {
  color: var(--tg-theme-hint-color, #999);
}

/* Значение поля */
.value {
  font-weight: bold;
}

/* Блок обратного отсчета */
.birthday-countdown {
  margin-top: 20px;
  text-align: center;
}

/* Контейнер для значений обратного отсчета */
.countdown-values {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
}

/* Элемент обратного отсчета */
.countdown-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Числовое значение обратного отсчета */
.count {
  font-size: 24px;
  font-weight: bold;
  color: var(--tg-theme-button-color, #3390ec);
}

/* Единица измерения обратного отсчета */
.unit {
  font-size: 12px;
  color: var(--tg-theme-hint-color, #999);
}

.telegram-button {
  background-color: var(--tg-theme-button-color, #2481cc);
  color: var(--tg-theme-button-text-color, #ffffff);
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  width: 100%;
  transition: all 0.3s ease;
}

.telegram-button:active {
  transform: scale(0.98);
  opacity: 0.9;
}

.telegram-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
</style> 