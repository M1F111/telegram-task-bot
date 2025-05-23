import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==== НАСТРОЙКИ ====
TOKEN = '7790911787:AAH5jo6iNqb6bXo2cfklLqSKfaLIEOQVxqo'
ALLOWED_USERS = [821886191]  # замените на свои user_id
DATA_FILE = 'data.json'
FOLDERS = ['work', 'home', 'music']

# ==== ХРАНИЛИЩЕ ====
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {folder: [] for folder in FOLDERS}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

data = load_data()

# ==== ОБРАБОТЧИК ====
async def handle_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ Access denied.")
        return

    folder = update.message.text.replace('/', '').lower()
    if folder not in FOLDERS:
        await update.message.reply_text("❓ Unknown folder.")
        return

    if not context.args:
        tasks = data.get(folder, [])
        if tasks:
            task_lines = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
            message = f"📁 {folder.capitalize()}:\n{task_lines}"
        else:
            message = "No tasks."
        await update.message.reply_text(message)
    else:
        task = " ".join(context.args)
        data[folder].append(task)
        save_data(data)
        await update.message.reply_text(f"✅ Added to {folder}: {task}")

# ==== СТАРТ ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Use /work /home /music + your task.")

# ==== ЗАПУСК ====
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    for f in FOLDERS:
        app.add_handler(CommandHandler(f, handle_folder))
    app.run_polling()

if __name__ == "__main__":
    main()
