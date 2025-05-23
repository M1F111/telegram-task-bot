import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAudio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = '7790911787:AAH5jo6iNqb6bXo2cfklLqSKfaLIEOQVxqo'
DATA_FILE = 'data.json'

FOLDERS = ['work', 'home', 'music']

# ====== ХРАНИЛИЩЕ ======
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟥 Work", callback_data='folder_work')],
        [InlineKeyboardButton("🟩 Home", callback_data='folder_home')],
        [InlineKeyboardButton("🟦 Music", callback_data='folder_music')]
    ]
    await update.message.reply_text("Привет! Выберите папку:", reply_markup=InlineKeyboardMarkup(keyboard))

# ====== Коллбэки по кнопкам ======
async def folder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    folder = query.data.replace('folder_', '')
    context.user_data['current_folder'] = folder
    await query.message.reply_text(f"Папка {folder.upper()} активна. Теперь отправьте задачу, ссылку или трек.")

# ====== Обработка сообщений ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    folder = context.user_data.get('current_folder')
    if not folder:
        return await update.message.reply_text("Сначала нажмите /start и выберите папку.")

    data = load_data()
    if user_id not in data:
        data[user_id] = {f: [] for f in FOLDERS}

    # Work: текстовая задача
    if folder == 'work':
        data[user_id][folder].append({"text": update.message.text, "done": False})
        await update.message.reply_text("📝 Задача добавлена")

    # Home: важное (сохраняем текст / фото / ссылку)
    elif folder == 'home':
        entry = {"text": update.message.text or '', "photo": None}
        if update.message.photo:
            entry["photo"] = update.message.photo[-1].file_id
        data[user_id][folder].append(entry)
        await update.message.reply_text("✅ Сохранено в важное")

    # Music: аудио
    elif folder == 'music':
        if update.message.audio:
            file_id = update.message.audio.file_id
            data[user_id][folder].append(file_id)
            await update.message.reply_text("🎵 Трек добавлен в плейлист")
        else:
            await update.message.reply_text("Пришлите именно аудио-файл")

    save_data(data)

# ====== Команда /music для воспроизведения ======
async def play_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    music = data.get(user_id, {}).get('music', [])
    if not music:
        await update.message.reply_text("Плейлист пуст.")
        return
    await update.message.reply_text("🎧 Ваш плейлист:")
    for track_id in music:
        await update.message.reply_audio(track_id)

# ====== ЗАПУСК ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", play_music))
    app.add_handler(CallbackQueryHandler(folder_callback))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.AUDIO, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
