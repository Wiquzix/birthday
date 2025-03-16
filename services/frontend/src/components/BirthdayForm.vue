<!-- 
  Компонент BirthdayForm отображает форму для ввода даты рождения.
  После ввода даты и нажатия кнопки "Продолжить" компонент отправляет событие submit с выбранной датой.
-->
<template>
  <div class="birthday-form">
    <h2>Введите вашу дату рождения</h2>
    <!-- Поле ввода даты с ограничением на будущие даты -->
    <input 
      type="date" 
      v-model="birthday"
      class="date-input"
      :max="today"
    >
    <!-- Кнопка отправки формы, активна только если дата выбрана -->
    <button 
      @click="submitForm" 
      class="telegram-button"
      :disabled="!birthday"
    >
      Продолжить
    </button>
  </div>
</template>

<script>
export default {
  name: 'BirthdayForm',
  data() {
    return {
      // Выбранная дата рождения
      birthday: '',
      // Текущая дата для ограничения выбора будущих дат
      today: new Date().toISOString().split('T')[0]
    }
  },
  computed: {
    /**
     * Проверяет валидность выбранной даты
     * Дата считается валидной, если она выбрана и не в будущем
     * @returns {boolean} - Результат проверки
     */
    isValidDate() {
      return this.birthday && new Date(this.birthday) < new Date();
    }
  },
  methods: {
    /**
     * Обрабатывает отправку формы
     * Если дата валидна, отправляет событие submit с выбранной датой
     */
    submitForm() {
      if (this.isValidDate) {
        this.$emit('submit', this.birthday);
      }
    }
  }
}
</script>

<style scoped>
/* Контейнер формы */
.birthday-form {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background-color: var(--tg-theme-secondary-bg-color, rgba(255, 255, 255, 0.08));
  border-radius: 12px;
}

/* Заголовок формы */
h2 {
  color: var(--tg-theme-text-color, #000000);
  text-align: center;
  margin-bottom: 10px;
}

/* Поле ввода даты */
.date-input {
  padding: 10px;
  font-size: 16px;
  border: 1px solid var(--tg-theme-hint-color, #999);
  border-radius: 8px;
  width: 200px;
  background-color: var(--tg-theme-bg-color, #ffffff);
  color: var(--tg-theme-text-color, #000000);
}

/* Кнопка в стиле Telegram */
.telegram-button {
  background-color: var(--tg-theme-button-color, #3390ec);
  color: var(--tg-theme-button-text-color, #ffffff);
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  width: 100%;
  max-width: 200px;
}

/* Стиль для неактивной кнопки */
.telegram-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style> 