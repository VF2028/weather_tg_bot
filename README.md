# Telegram Weather Bot

## Описание

Этот проект представляет собой Telegram-бота, который предоставляет пользователям прогноз погоды для заданного маршрута. Бот позволяет вводить начальный и конечный города, а также промежуточные города, и возвращает прогноз погоды на несколько дней вперед.

### Основные функции

- **Прогноз погоды**: Получение данных о погоде с использованием API Open Meteo.
- **Геокодирование**: Определение координат городов с помощью Яндекс Геокодера.
- **Интерактивный интерфейс**: Удобное взаимодействие с пользователем через команды и кнопки.
- **Кэширование запросов**: Использование кэширования для повышения производительности и снижения нагрузки на API.
- **Логирование**: Запись событий и ошибок для упрощения отладки и мониторинга.

## Установка

1. Клонируйте репозиторий: https://github.com/VF2028/weather_tg_bot

2. Перейдите в директорию проекта: bot.py

3. Установите необходимые зависимости: pip install aiogram requests-cache python-dotenv


4. В файле `.env` в корневой директории проекта и добавьте ваши токены:
   BOT_TOKEN=ваш_токен_бота
   YANDEX_API_KEY=ваш_ключ_API_Яндекса


## Использование

Запустите бота с помощью следующей команды: python bot.py


После запуска бота вы можете начать взаимодействовать с ним в Telegram (@vaf_project_bot), используя команды `/start`, `/help` и `/weather`.

## Команды

- `/start` - Приветственное сообщение и описание функционала.
- `/help` - Справка по командам.
- `/weather` - Запуск прогнозирования погоды для маршрута.

## Вклад

Если вы хотите внести свой вклад в проект, пожалуйста, создайте новый issue или отправьте pull request.

## Лицензия

Этот проект лицензирован под MIT License - смотрите файл [LICENSE](LICENSE) для подробностей.





   


   
