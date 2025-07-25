import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackContext
)

# --- BOT CONFIG ---
TOKEN = '8311398753:AAErEhUGNr6puyafh2-_BrfRbrmNFwB5620'  # <-- Replace this with your real token!

# --- STATE ---
queue = []  # List of user dicts: [{'id': id, 'name': 'Alice'}]
currently_charging = None  # User dict, or None

# --- BUTTONS ---
BUTTONS = [
    ["🔌 Charge my car", "👋 Leave charger"],
    ["📍 My place in line", "📜 Queue status"],
    ["❌ Cancel my request"]
]
MARKUP = ReplyKeyboardMarkup(BUTTONS, resize_keyboard=True)

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)

# --- HELPERS ---
def find_user(user_id):
    for u in queue:
        if u['id'] == user_id:
            return u
    return None

def get_username(user):
    return user.first_name or user.username or "User"

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the EV Charger Queue Bot!\nUse the buttons to join or leave the line.",
        reply_markup=MARKUP
    )

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    user = update.message.from_user
    user_id = user.id
    name = get_username(user)

    global queue, currently_charging

    if text == "🔌 Charge my car":
        if currently_charging and currently_charging['id'] == user_id:
            await update.message.reply_text("You're charging now! 🔌", reply_markup=MARKUP)
            return
        if find_user(user_id):
            place = queue.index(find_user(user_id)) + 1
            await update.message.reply_text(f"You're #{place} in line.", reply_markup=MARKUP)
            return
        if not currently_charging:
            currently_charging = {'id': user_id, 'name': name}
            await update.message.reply_text("It's your turn! Plug in! 🔌", reply_markup=MARKUP)
        else:
            queue.append({'id': user_id, 'name': name})
            await update.message.reply_text(f"Added to the line! You're #{len(queue)} in line.", reply_markup=MARKUP)

    elif text == "👋 Leave charger":
        if currently_charging and currently_charging['id'] == user_id:
            # Move up next in queue
            if queue:
                next_user = queue.pop(0)
                currently_charging = next_user
                await context.bot.send_message(
                    chat_id=next_user['id'],
                    text="Your turn! Plug in! 🔌"
                )
            else:
                currently_charging = None
            await update.message.reply_text("You've left the charger. Thank you! 👋", reply_markup=MARKUP)
        elif find_user(user_id):
            # Remove from queue
            queue = [u for u in queue if u['id'] != user_id]
            await update.message.reply_text("You weren't charging, but you have been removed from the queue. 👋", reply_markup=MARKUP)
        else:
            await update.message.reply_text("You weren't charging, and you are not in the queue. 👋", reply_markup=MARKUP)

    elif text == "📍 My place in line":
        if currently_charging and currently_charging['id'] == user_id:
            await update.message.reply_text("You're charging now! 🔌", reply_markup=MARKUP)
        elif find_user(user_id):
            place = queue.index(find_user(user_id)) + 1
            await update.message.reply_text(f"You're #{place} in line.", reply_markup=MARKUP)
        else:
            await update.message.reply_text("You are not in the queue.", reply_markup=MARKUP)

    elif text == "📜 Queue status":
        if currently_charging:
            names = [currently_charging['name']] + [u['name'] for u in queue]
            reply = "Now charging: " + currently_charging['name'] + "\nQueue:\n"
            if queue:
                reply += "\n".join([f"{i+1}. {u['name']}" for i, u in enumerate(queue)])
            else:
                reply += "No one waiting."
            await update.message.reply_text(reply, reply_markup=MARKUP)
        else:
            await update.message.reply_text("Queue is empty! 🔋", reply_markup=MARKUP)

    elif text == "❌ Cancel my request":
        if currently_charging and currently_charging['id'] == user_id:
            currently_charging = None
            await update.message.reply_text("You've left the charger. 👋", reply_markup=MARKUP)
            # Promote next in line
            if queue:
                next_user = queue.pop(0)
                currently_charging = next_user
                await context.bot.send_message(
                    chat_id=next_user['id'],
                    text="Your turn! Plug in! 🔌"
                )
        elif find_user(user_id):
            queue = [u for u in queue if u['id'] != user_id]
            await update.message.reply_text("Removed from the queue. 👋", reply_markup=MARKUP)
        else:
            await update.message.reply_text("You are not in the queue.", reply_markup=MARKUP)

    else:
        await update.message.reply_text("Please use the buttons. 😊", reply_markup=MARKUP)

# --- MAIN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    print("Bot is running!")
    app.run_polling()