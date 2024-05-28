import os
import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from random import sample
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükleyin
load_dotenv()

# Ortam değişkenini okuyun
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not found")

# Veritabanı bağlantısı
conn = sqlite3.connect('messages.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        user_id INTEGER,
        username TEXT,
        date TEXT
    )
''')
conn.commit()

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Çekiliş botuna hoş geldiniz!')

def track_messages(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO messages (user_id, username, date) VALUES (?, ?, ?)', (user.id, user.username, date))
    conn.commit()

def draw_lottery(update: Update, context: CallbackContext) -> None:
    winners_count = int(context.args[0]) if context.args else 1
    one_week_ago = datetime.now() - timedelta(days=7)
    c.execute('''
        SELECT user_id, username, COUNT(*) as msg_count
        FROM messages
        WHERE date >= ?
        GROUP BY user_id
        HAVING msg_count >= 250
    ''', (one_week_ago.strftime('%Y-%m-%d %H:%M:%S'),))
    eligible_users = c.fetchall()
    if not eligible_users:
        update.message.reply_text('Yeterli mesaj atan kullanıcı bulunamadı.')
        return
    winners = sample(eligible_users, min(winners_count, len(eligible_users)))
    winners_text = '\n'.join([f'{winner[1]} ({winner[0]})' for winner in winners])
    update.message.reply_text(f'Kazananlar:\n{winners_text}')

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_messages))
    dispatcher.add_handler(CommandHandler("draw", draw_lottery))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
