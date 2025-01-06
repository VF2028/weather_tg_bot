import os
import requests
import requests_cache
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import plotly.graph_objects as go

# Настройка логирования
logging.basicConfig(level=logging.INFO, filename='bot.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


#BOT_TOKEN = os.getenv("BOT_TOKEN")
#YANDEX_API_KEY = os.getenv("YANDEX_API_KEY") 

BOT_TOKEN = ""
YANDEX_API_KEY = "3a844ca2-91ee-405b-9170-6309f2afa83d"

BASE_URL = "https://api.open-meteo.com/v1/forecast"
YANDEX_GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"

# Создание кэшированной сессии для запросов
session = requests_cache.CachedSession('weather_cache', expire_after=3600)  # Кэш на 1 час

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


def plot_weather_data(forecast, city):
    dates = [day['date'] for day in forecast]
    max_temps = [day['max_temperature'] for day in forecast]
    min_temps = [day['min_temperature'] for day in forecast]

    fig = go.Figure()

    # Добавление линии максимальной температуры
    fig.add_trace(go.Scatter(x=dates, y=max_temps, mode='lines+markers', name='Максимальная температура (°C)', line=dict(color='red')))
    
    # Добавление линии минимальной температуры
    fig.add_trace(go.Scatter(x=dates, y=min_temps, mode='lines+markers', name='Минимальная температура (°C)', line=dict(color='blue')))

    # Добавление области между максимальной и минимальной температурой
    fig.add_trace(go.Scatter(x=dates, y=max_temps, mode='lines', showlegend=False, line=dict(width=0), fill='tonexty', fillcolor='rgba(255, 0, 0, 0.2)'))
    
    fig.update_layout(title=f'Прогноз температуры в {city.capitalize()}',
                      xaxis_title='Дата',
                      yaxis_title='Температура (°C)',
                      xaxis_tickangle=-45)

    # Сохранение графика в файл
    file_path = f'{city}_weather_plot.png'
    fig.write_image(file_path)

    return file_path

class WeatherStates(StatesGroup):
    days = State()
    start_city = State()
    end_city = State()
    intermediate_cities = State()
    

# Функции для получения данных о погоде и координатах
def get_coordinates(city_name):
    try:
        params = {
            "apikey": YANDEX_API_KEY,
            "geocode": city_name,
            "format": "json",
        }
        response = session.get(YANDEX_GEOCODER_URL, params=params)
        response.raise_for_status()

        data = response.json()
        geo_object = (
            data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [{}])[0]
            .get("GeoObject", {})
        )

        if not geo_object:
            return None

        coordinates = geo_object.get("Point", {}).get("pos", "")
        if not coordinates:
            return None

        lon, lat = map(float, coordinates.split(" "))
        return lat, lon
    except requests.RequestException as e:
        logging.error(f"Ошибка подключения к Яндекс API: {str(e)}")
        raise ValueError(f"Ошибка подключения к Яндекс API: {str(e)}")
    except Exception as e:
        logging.error(f"Ошибка при обработке города '{city_name}': {str(e)}")
        raise ValueError(f"Ошибка при обработке города '{city_name}': {str(e)}")

def get_weather_data(latitude, longitude, days=1):
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "timezone": "auto",
            "forecast_days": days,
        }
        response = session.get(BASE_URL, params=params)  # Используем кэшированную сессию
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Ошибка подключения к Open Meteo API: {e}")
        raise Exception(f"Ошибка подключения к Open Meteo API: {e}")

    data = response.json()
    if not data:
        raise Exception("Данные API недоступны или некорректны.")

    return data

def parse_weather_data(raw_data):
    daily_data = raw_data.get("daily", {})
    days = len(daily_data.get("temperature_2m_max", []))

    forecast = []
    for i in range(days):
        forecast.append({
            "date": daily_data.get("time", [])[i],
            "max_temperature": daily_data.get("temperature_2m_max", [None])[i],
            "min_temperature": daily_data.get("temperature_2m_min", [None])[i],
            "precipitation_sum": daily_data.get("precipitation_sum", [None])[i],
            "wind_speed_max": daily_data.get("windspeed_10m_max", [None])[i],
        })
    return forecast
'''
Один из вариантов при обработке выбора количества дней
# Создание inline кнопок для выбора дней прогноза
def create_days_buttons():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text="1 день", callback_data="1"))
    keyboard.add(types.InlineKeyboardButton(text="3 дня", callback_data="3"))
    keyboard.add(types.InlineKeyboardButton(text="5 дней", callback_data="5"))
    keyboard.add(types.InlineKeyboardButton(text="7 дней", callback_data="7"))
    return keyboard.as_markup()
'''
# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    logging.info(f"User {message.from_user.id} started the bot.")
    await message.answer(
        "Привет! Я помогу тебе узнать прогноз погоды по маршруту.\n"
        "Вот как ты можешь использовать меня:\n\n"
        "/weather - Получить прогноз погоды для маршрута\n"
        "Просто введи начальный город, конечный и промежуточные города, и я покажу тебе прогноз погоды.\n\n"
        "Попробуй команду /help, чтобы получить список доступных команд."
    )

# Обработчик команды /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "Доступные команды:\n\n"
        "/start - Приветственное сообщение и описание функционала\n"
        "/help - Справка по командам\n"
        "/weather - Запуск прогнозирования погоды для маршрута\n\n"
        "Для использования команды /weather введите начальный город, конечный и промежуточные города. "
        "Я покажу тебе прогноз погоды на выбранный период."
    )

# Обработчик команды /weather
@dp.message(Command("weather"))
async def weather_command(message: types.Message, state: FSMContext):
    await message.answer("Введите количество дней для прогноза:")
    await state.set_state(WeatherStates.days)

# Обработчик для выбора количества дней
@dp.message(WeatherStates.days)
async def process_days_selection(message: types.Message, state: FSMContext):
    days_input = message.text.strip()
    
    try:
        days = int(days_input)  # Преобразование в целое число
        if days <= 0:
            raise ValueError("Количество дней должно быть положительным числом.")

        # Сохраняем количество дней в состоянии
        await state.update_data(days=days)

        # Запрашиваем начальный город
        await message.answer("Введите начальный город:")
        await state.set_state(WeatherStates.start_city)

    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}. Попробуйте снова.")

# Обработчик начального города
@dp.message(WeatherStates.start_city)
async def process_start_city(message: types.Message, state: FSMContext):
    city_name = message.text.strip().lower()
    try:
        coordinates = get_coordinates(city_name)
        if coordinates is None:
            await message.answer(f"Город '{city_name.capitalize()}' не найден. Пожалуйста, попробуйте снова.")
            return

        await state.update_data(start_city=city_name)
        await message.answer("Введите конечный город:")
        await state.set_state(WeatherStates.end_city)
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}. Попробуйте снова.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}. Пожалуйста, попробуйте снова.")

# Обработчик конечного города
@dp.message(WeatherStates.end_city)
async def process_end_city(message: types.Message, state: FSMContext):
    data = await state.get_data()
    start_city = data["start_city"]
    end_city = message.text.strip().lower()

    if start_city == end_city:
        await message.answer("Ошибка: начальный и конечный города не должны совпадать! Введите другой конечный город:")
        return

    try:
        coordinates = get_coordinates(end_city)
        if coordinates is None:
            await message.answer(f"Город '{end_city.capitalize()}' не найден. Пожалуйста, попробуйте снова.")
            return

        await state.update_data(end_city=end_city)
        await message.answer("Введите промежуточные города через запятую (если их нет, напишите 'нет'):")
        await state.set_state(WeatherStates.intermediate_cities)
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}. Попробуйте снова.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}. Пожалуйста, попробуйте снова.")

# Обработчик промежуточных городов
@dp.message(WeatherStates.intermediate_cities)
async def process_intermediate_cities(message: types.Message, state: FSMContext):
    data = await state.get_data()
    start_city = data["start_city"]
    end_city = data["end_city"]
    intermediate_cities_input = message.text.strip().lower()

    if intermediate_cities_input == "нет":
        intermediate_cities = []
    else:
        intermediate_cities = [city.strip() for city in intermediate_cities_input.split(",") if city.strip()]

    if any(city in [start_city, end_city] for city in intermediate_cities):
        await message.answer("Ошибка: промежуточные города не должны совпадать с начальным или конечным городом. Попробуйте еще раз:")
        return

    route = f"{start_city.capitalize()} -> "
    if intermediate_cities:
        route += " -> ".join([city.capitalize() for city in intermediate_cities]) + " -> "
    route += f"{end_city.capitalize()}"

    # Получаем количество дней из состояния
    days = data.get('days', 1)

    # Получаем координаты и прогноз погоды для каждого города
    try:
        cities = [start_city] + intermediate_cities + [end_city]
        
        weather_report = ""
        
        for city in cities:
            try:
                lat, lon = get_coordinates(city)
                if lat is None or lon is None:
                    await message.answer(f"Город '{city.capitalize()}' не найден. Пропускаем его.")
                    continue
                
                weather_data = get_weather_data(lat, lon, days=days)
                forecast = parse_weather_data(weather_data)
                
                # Если больше 1 дня то рисуем графики
                if days > 1:
                    # Создание и отправка графика
                    plot_file = plot_weather_data(forecast, city)
                    await message.answer_photo(types.FSInputFile(plot_file), caption=f'**График погоды для {city.capitalize()}**', parse_mode="Markdown")

                weather_report += f"**Погода для города {city.capitalize()}:**\n"
                for day in forecast:
                    weather_report += (
                        f"**Дата:** {day['date']}\n"
                        f"**Макс. температура:** {day['max_temperature']}°C\n"
                        f"**Мин. температура:** {day['min_temperature']}°C\n"
                        f"**Осадки:** {day['precipitation_sum']} мм\n"
                        f"**Макс. скорость ветра:** {day['wind_speed_max']} м/с\n\n"
                    )
                    
            except Exception as e:
                logging.error(f"Ошибка при получении данных для города '{city.capitalize()}': {str(e)}")
                await message.answer(f"Ошибка при получении данных для города '{city.capitalize()}': {str(e)}")

        # Отправляем отчет о погоде пользователю
        if weather_report:
            await message.answer(f'Ваш маршрут: {route}\n\n{weather_report}', parse_mode="Markdown")
        else:
            await message.answer(f"Не удалось получить данные о погоде для маршрута.")

    except Exception as e:
        logging.error(f"Произошла ошибка при обработке маршрута: {str(e)}")
        await message.answer(f"Произошла ошибка при обработке маршрута: {str(e)}")

    await state.clear()

# Запуск бота
if __name__ == "__main__":
    async def main():
        await dp.start_polling(bot)

    asyncio.run(main())
