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
        [InlineKeyboardButton("🟥 Work", callback_data='open_work')],
        [InlineKeyboardButton("🟩 Home", callback_data='open_home')],
        [InlineKeyboardButton("🟦 Music", callback_data='open_music')]
    ]
    await update.message.reply_text("Привет! Выберите папку:", reply_markup=InlineKeyboardMarkup(keyboard))

# ====== Кнопки-папки и вложенные ======
async def folder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == 'open_work':
        keyboard = [
            [InlineKeyboardButton("📌 Задачи", callback_data='work_tasks')],
            [InlineKeyboardButton("📂 Все", callback_data='tasks')],
            [InlineKeyboardButton("⬅️ Выйти", callback_data='back_home')]
        ]
        await query.edit_message_text("📁 Папка WORK:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'open_home':
        keyboard = [
            [InlineKeyboardButton("📌 Задачи", callback_data='home_tasks')],
            [InlineKeyboardButton("⭐ Избранное", callback_data='home_fav')],
            [InlineKeyboardButton("🎵 Музыка", callback_data='home_music')],
            [InlineKeyboardButton("⬅️ Выйти", callback_data='back_home')]
        ]
        await query.edit_message_text("📁 Папка HOME:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'open_music':
        await play_music(update, context)

    elif action == 'back_home':
        await start(update, context)

    elif action == 'tasks':
        await list_tasks(query, context)

    elif action == 'home_tasks':
        context.user_data['current_folder'] = 'home'
        await query.edit_message_text("Папка HOME активна. Отправьте задачу, фото или текст.")

    elif action == 'home_fav':
        await list_home(query, context)

    elif action == 'home_music':
        context.user_data['current_folder'] = 'music'
        await query.edit_message_text("Папка МУЗЫКА активна. Отправьте трек.")

    elif action == 'work_tasks':
        context.user_data['current_folder'] = 'work'
        await query.edit_message_text("Папка WORK активна. Отправьте задачу.")

# ====== Обработка сообщений ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    folder = context.user_data.get('current_folder')

    if not folder:
        return await update.message.reply_text("Сначала нажмите /start и выберите папку.")

    data = load_data()
    if user_id not in data:
        data[user_id] = {f: [] for f in FOLDERS}

    if folder == 'work':
        data[user_id][folder].append({"text": text, "done": False})
        await update.message.reply_text("📝 Задача добавлена")

    elif folder == 'home':
        entry = {"text": text or '', "photo": None, "done": False}
        if update.message.photo:
            entry["photo"] = update.message.photo[-1].file_id
        data[user_id][folder].append(entry)
        await update.message.reply_text("✅ Сохранено в важное")

    elif folder == 'music':
        if update.message.audio:
            file_id = update.message.audio.file_id
            data[user_id][folder].append(file_id)
            await update.message.reply_text("🎵 Трек добавлен в плейлист")
        else:
            await update.message.reply_text("Пришлите именно аудиофайл")

    save_data(data)

# ====== Показать задачи Work ======
async def list_tasks(query, context):
    user_id = str(query.from_user.id)
    data = load_data()
    tasks = data.get(user_id, {}).get('work', [])
    if not tasks:
        await query.edit_message_text("Список задач пуст.")
        return

    for i, task in enumerate(tasks):
        status = "✅" if task['done'] else "❌"
        text = f"{i+1}. {status} {task['text']}"
        buttons = [InlineKeyboardButton("✅ Завершить", callback_data=f"remove_work_{i}")]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup([buttons]))

# ====== Home отображение ======
async def list_home(query, context):
    user_id = str(query.from_user.id)
    data = load_data()
    items = data.get(user_id, {}).get('home', [])
    if not items:
        await query.edit_message_text("Папка Home пуста.")
        return

    for i, item in enumerate(items):
        status = "✅" if item.get('done') else "❌"
        text = item.get('text', '')
        msg = f"{i+1}. {status} {text}"
        buttons = [InlineKeyboardButton("✅" if not item.get('done') else "↩️", callback_data=f"toggle_home_{i}")]
        if item.get("photo"):
            await query.message.reply_photo(item["photo"], caption=msg, reply_markup=InlineKeyboardMarkup([buttons]))
        else:
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([buttons]))

# ====== Тогглы/Удаление ======
async def toggle_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_data()

    if 'toggle_home_' in query.data:
        folder = 'home'
        index = int(query.data.replace('toggle_home_', ''))
        items = data.get(user_id, {}).get(folder, [])
        if 0 <= index < len(items):
            items[index]['done'] = not items[index]['done']
            save_data(data)
            text = items[index].get('text', '')
            msg = f"{index+1}. {'✅' if items[index]['done'] else '❌'} {text}"
            if items[index].get('photo'):
                await query.edit_message_caption(caption=msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️" if items[index]['done'] else "✅", callback_data=query.data)]]))
            else:
                await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️" if items[index]['done'] else "✅", callback_data=query.data)]]))
            await query.answer("Статус обновлён")

    elif 'remove_work_' in query.data:
        folder = 'work'
        index = int(query.data.replace('remove_work_', ''))
        items = data.get(user_id, {}).get(folder, [])
        if 0 <= index < len(items):
            removed = items.pop(index)
            save_data(data)
            await query.edit_message_text(f"❎ {removed['text']} (удалено)")
            await query.answer("Удалено")

# ====== Музыка ======
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
    app.add_handler(CallbackQueryHandler(toggle_task, pattern="^(toggle_|remove_).*"))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.AUDIO, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
