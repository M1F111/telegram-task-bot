import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = '7790911787:AAH5jo6iNqb6bXo2cfklLqSKfaLIEOQVxqo'
DATA_FILE = 'data.json'
FOLDERS = ['work', 'home', 'music']

# ========== ХРАНИЛИЩЕ ==========
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ========== /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟥 Work", callback_data='open_work')],
        [InlineKeyboardButton("🟩 Home", callback_data='open_home')],
        [InlineKeyboardButton("🟦 Music", callback_data='open_music')]
    ]
    await update.effective_message.reply_text("Привет! Выберите папку:", reply_markup=InlineKeyboardMarkup(keyboard))

# ========== ОБРАБОТКА КНОПОК ==========
async def folder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == 'open_work':
        keyboard = [
            [InlineKeyboardButton("📌 Задачи", callback_data='work_active')],
            [InlineKeyboardButton("📂 Все", callback_data='work_all')],
            [InlineKeyboardButton("⬅️ Выйти", callback_data='back')]
        ]
        await query.edit_message_text("📁 Папка WORK:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'open_home':
        keyboard = [
            [InlineKeyboardButton("📌 Задачи", callback_data='home_active')],
            [InlineKeyboardButton("⭐ Избранное", callback_data='home_done')],
            [InlineKeyboardButton("🎵 Музыка", callback_data='home_music')],
            [InlineKeyboardButton("⬅️ Выйти", callback_data='back')]
        ]
        await query.edit_message_text("📁 Папка HOME:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == 'open_music' or action == 'home_music':
        await query.edit_message_text("Папка MUSIC активна. Отправьте аудио.")
        context.user_data['current_folder'] = 'music'

    elif action == 'back':
        await start(update, context)

    elif action == 'work_active':
        await show_tasks(update, context, folder='work', active_only=True)

    elif action == 'work_all':
        await show_tasks(update, context, folder='work', active_only=False)

    elif action == 'home_active':
        await show_tasks(update, context, folder='home', active_only=True)

    elif action == 'home_done':
        await show_tasks(update, context, folder='home', active_only=False, done_only=True)

# ========== ПОКАЗ СПИСКА ==========
async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE, folder, active_only=False, done_only=False):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_data()
    items = data.get(user_id, {}).get(folder, [])

    result = []
    for i, item in enumerate(items):
        if folder == 'music':
            continue
        if done_only and not item.get('done'): continue
        if active_only and item.get('done'): continue
        result.append((i, item))

    if not result:
        await query.edit_message_text("Список пуст.")
        return

    for i, item in result:
        text = item.get('text', '')
        status = '✅' if item.get('done') else '❌'
        label = f"{status} {text}"
        if folder == 'work':
            buttons = [InlineKeyboardButton("✅ Завершить", callback_data=f'delete_{folder}_{i}')]
        else:
            buttons = [InlineKeyboardButton("↩️" if item['done'] else "✅", callback_data=f'toggle_{folder}_{i}')]
        await query.message.reply_text(label, reply_markup=InlineKeyboardMarkup([buttons]))

# ========== СООБЩЕНИЯ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    folder = context.user_data.get('current_folder')
    if not folder:
        return await update.message.reply_text("Выберите папку через /start")

    data = load_data()
    if user_id not in data:
        data[user_id] = {f: [] for f in FOLDERS}

    if folder == 'music':
        if update.message.audio:
            data[user_id][folder].append(update.message.audio.file_id)
            await update.message.reply_text("🎵 Трек добавлен")
        else:
            await update.message.reply_text("Отправьте аудио")
    else:
        item = {"text": update.message.text, "done": False}
        if update.message.photo:
            item["photo"] = update.message.photo[-1].file_id
        data[user_id][folder].append(item)
        await update.message.reply_text("✅ Добавлено")

    save_data(data)

# ========== КНОПКИ: toggle/remove ==========
async def toggle_or_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = load_data()

    parts = query.data.split('_')
    action, folder, index = parts[0], parts[1], int(parts[2])
    items = data.get(user_id, {}).get(folder, [])

    if not (0 <= index < len(items)):
        return await query.edit_message_text("❌ Не найдено")

    if action == 'toggle':
        items[index]['done'] = not items[index]['done']
        save_data(data)
        await query.edit_message_text(f"{'✅' if items[index]['done'] else '❌'} {items[index]['text']}")

    elif action == 'delete':
        deleted = items.pop(index)
        save_data(data)
        await query.edit_message_text(f"❌ {deleted['text']} (удалено)")

# ========== СТАРТ ==========
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(folder_callback, pattern="^(open_|home_|work_|back|tasks)$"))
    app.add_handler(CallbackQueryHandler(toggle_or_delete, pattern="^(toggle|delete)_"))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.AUDIO, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
