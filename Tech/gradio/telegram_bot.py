import os
import requests
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from dotenv import load_dotenv

load_dotenv()

PASSPORT_PHOTO, PERSON_PHOTO = range(2)

class PassportBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.api_passport = os.getenv("PASSPORT_API_URL")
        self.api_verify = os.getenv("VERIFY_API_URL")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text(
            "🛂 <b>АэроСтраж AI</b>\n\n"
            "Для проверки необходимо:\n"
            "1. Отправить фото страницы паспорта\n"
            "2. Отправить селфи для верификации\n"
            "3. Получить результат проверки\n\n"
            "Начнем с фото паспорта 📄",
            parse_mode="HTML"
        )
        return PASSPORT_PHOTO

    async def process_passport_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.message.from_user
        photo_file = await update.message.photo[-1].get_file()
        
        temp_path = f"temp_{user.id}_passport.jpg"
        await photo_file.download_to_drive(temp_path)
        
        try:
            with open(temp_path, "rb") as f:
                response = requests.post(self.api_passport, files={"file": f})
            passport_data = response.json()
            
            context.user_data["passport"] = passport_data
            context.user_data["passport_path"] = temp_path
            
            await update.message.reply_text(
                "✅ Паспорт успешно распознан!\n"
                "Теперь отправьте ваше селфи для верификации 📸",
                parse_mode="HTML"
            )
            return PERSON_PHOTO
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка обработки: {str(e)}")
            os.remove(temp_path)
            return ConversationHandler.END

    async def process_person_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.message.from_user
        photo_file = await update.message.photo[-1].get_file()
        
        temp_path = f"temp_{user.id}_person.jpg"
        await photo_file.download_to_drive(temp_path)
        
        try:
            passport_path = context.user_data.get("passport_path")
            
            with open(passport_path, "rb") as f1, open(temp_path, "rb") as f2:
                response = requests.post(
                    self.api_verify,
                    files={"file1": f1, "file2": f2}
                )
            verify_data = response.json()
            
            result = self.format_results(
                context.user_data["passport"], 
                verify_data
            )
            
            await update.message.reply_text(result, parse_mode="HTML")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка верификации: {str(e)}")
        
        # Cleanup
        for path in [temp_path, passport_path]:
            if os.path.exists(path):
                os.remove(path)
                
        return ConversationHandler.END

    def format_results(self, passport_data: dict, verify_data: dict) -> str:
        ocr = passport_data.get("OCR", {})
        verified = verify_data.get("verified", False)
        similarity = round(verify_data.get("distance", 0)*100, 2)
        
        return (
            "📋 <b>Результаты проверки:</b>\n\n"
            "🛂 <b>Данные паспорта:</b>\n"
            f"👤 Фамилия: <b>{ocr.get('Last_name_ru', 'N/A')}</b>\n"
            f"📛 Имя: <b>{ocr.get('First_name_ru', 'N/A')}</b>\n"
            f"🔖 Отчество: <b>{ocr.get('Middle_name_ru', 'N/A')}</b>\n"
            f"🎂 Дата рождения: <b>{ocr.get('Birth_date', 'N/A')}</b>\n"
            f"🔢 Серия/номер: <b>{ocr.get('Licence_number', 'N/A')}</b>\n\n"
            "🔍 <b>Верификация:</b>\n"
            f"{'✅ Личность подтверждена' if verified else '❌ Личности не совпадают'}\n"
            f"📊 Сходство: <b>{similarity}%</b>"
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("🚫 Операция отменена")
        return ConversationHandler.END

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"⚠️ Ошибка: {context.error}")

    def run(self):
        app = Application.builder().token(self.token).build()
        
        app.add_error_handler(self.error_handler)
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                PASSPORT_PHOTO: [
                    MessageHandler(filters.PHOTO, self.process_passport_photo)
                ],
                PERSON_PHOTO: [
                    MessageHandler(filters.PHOTO, self.process_person_photo)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        app.add_handler(conv_handler)
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    bot = PassportBot()
    bot.run()
