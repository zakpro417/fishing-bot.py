
import logging
import random
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from geopy.geocoders import Nominatim
from apscheduler.schedulers.background import BackgroundScheduler

# Токен Telegram-бота
TOKEN = "7745591280:AAFa-YcDPqGzyYXdglVHJNE1bIj1rV1C6GE"

# Настройка логирования
logging.basicConfig(
    filename="fishing_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Данные о рыбе
FISH_TYPES = {
    "Карась 🐠": {
        "temp_opt": (15, 20),
        "pressure_opt": (1000, 1015),
        "wind_max": 4,
        "cloud_max": 60,
    },
    "Короп 🐟": {
        "temp_opt": (15, 25),
        "pressure_opt": (1000, 1020),
        "wind_max": 5,
        "cloud_max": 70,
    },
}

# Функция для получения текущего сезона
def get_season():
    month = datetime.now().month
    if 3 <= month <= 5:
        return "весна 🌸"
    elif 6 <= month <= 8:
        return "літо ☀️"
    elif 9 <= month <= 11:
        return "осінь 🍂"
    else:
        return "зима ❄️"

# Прогноз клева
def predict_bite_chance(fish, weather_data):
    fish_data = FISH_TYPES.get(fish)
    if not fish_data:
        return "Информация о рыбе отсутствует."

    temp = weather_data.get("temp", 0)
    pressure = weather_data.get("pressure", 0)
    wind_speed = weather_data.get("wind_speed", 0)
    clouds = weather_data.get("clouds", 0)

    temp_score = 1.0 - abs(temp - sum(fish_data["temp_opt"]) / 2) / (
        fish_data["temp_opt"][1] - fish_data["temp_opt"][0]
    )
    pressure_score = (
        1.0
        if fish_data["pressure_opt"][0] <= pressure <= fish_data["pressure_opt"][1]
        else 0.5
    )
    wind_score = 1.0 if wind_speed <= fish_data["wind_max"] else 0.3
    cloud_score = 1.0 if clouds <= fish_data["cloud_max"] else 0.5

    overall_score = (temp_score + pressure_score + wind_score + cloud_score) / 4
    return f"Вероятность клева для {fish}: {overall_score * 100:.1f}%"

# Получение геолокации пользователя
def get_user_location(lat, lon):
    geolocator = Nominatim(user_agent="fishing_bot")
    location = geolocator.reverse((lat, lon))
    return location.address

# Ежедневные уведомления
def send_daily_update(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.context
    weather_data = {"temp": 18, "pressure": 1010, "wind_speed": 3, "clouds": 50}
    bite_chance = predict_bite_chance("Карась 🐠", weather_data)
    context.bot.send_message(
        chat_id=chat_id,
        text=f"Сегодняшняя погода: {weather_data}\n{bite_chance}",
    )

def schedule_daily_updates(application, chat_id):
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_update, "cron", hour=8, context=chat_id)
    scheduler.start()

# Генерация отчета о рыбалке
def generate_fishing_report(user_id, fish_caught, bait_used):
    report = f"Отчет о рыбалке для пользователя {user_id}:\n"
    report += f"Поймано рыбы: {fish_caught}\n"
    report += f"Использованная прикормка: {bait_used}\n"
    return report

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Выбрать рыбу", callback_data="choose_fish")],
        [InlineKeyboardButton("Прогноз клева", callback_data="bite_forecast")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

# Обработчик выбора рыбы
async def choose_fish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fish_list = "\n".join(FISH_TYPES.keys())
    await query.edit_message_text(text=f"Выберите рыбу:\n{fish_list}")

# Обработчик прогноза клева
async def bite_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    weather_data = {"temp": 18, "pressure": 1010, "wind_speed": 3, "clouds": 50}
    bite_chance = predict_bite_chance("Карась 🐠", weather_data)
    await query.edit_message_text(text=bite_chance)

# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(choose_fish, pattern="choose_fish"))
    application.add_handler(CallbackQueryHandler(bite_forecast, pattern="bite_forecast"))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()

