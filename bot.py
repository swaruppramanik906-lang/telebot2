import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN   = os.environ.get("BOT_TOKEN",   "8770256514:AAFboeG9vVOS987Nz9zXIZhwtsiVPySRC5U")
ADMIN_ID    = int(os.environ.get("ADMIN_ID", "6901201338"))
QR_CODE_URL = os.environ.get("QR_CODE_URL", "https://i.ibb.co/TMZ4tpf8/6337116742676582273.jpg")

logging.basicConfig(level=logging.INFO)

COURSES = {
    "pw":        {"name": "⚡ Physics Wallah (PW)",  "desc": "📘 Physics Wallah\n\n✅ JEE/NEET Full Syllabus\n✅ 500+ HD Videos\n✅ PDF Notes & DPP\n✅ Live Doubt Sessions\n"},
    "unacademy": {"name": "🎓 Unacademy",            "desc": "📗 Unacademy\n\n✅ UPSC/SSC/JEE/NEET\n✅ Live + Recorded\n✅ Mock Tests\n✅ 24x7 Support\n"},
    "kgs":       {"name": "📖 KGS (Khan Sir GS)",    "desc": "📙 KGS Course\n\n✅ SSC/Railways\n✅ GS Full Syllabus\n✅ Reasoning Tricks\n✅ Hindi Medium\n"},
    "target":    {"name": "🎯 Target IAS / PCS",     "desc": "📕 Target IAS/PCS\n\n✅ UPSC Prelims+Mains\n✅ State PCS Material\n✅ Answer Writing\n✅ Previous Papers\n"},
    "other":     {"name": "🌟 Other Courses",         "desc": "📓 Other Courses\n\n✅ Coding & Marketing\n✅ Stock Market\n✅ Spoken English\n✅ Personality Dev\n"},
}

# ── Global state dicts ──
AWAITING_FEEDBACK: dict[int, bool] = {}
AWAITING_PHONE:    dict[int, str]  = {}  # user_id -> course_name (waiting for phone)

# ──────────────────────────────────────────
# Keyboards
# ──────────────────────────────────────────

def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(COURSES["pw"]["name"],        callback_data="course_pw")],
        [InlineKeyboardButton(COURSES["unacademy"]["name"], callback_data="course_unacademy")],
        [InlineKeyboardButton(COURSES["kgs"]["name"],       callback_data="course_kgs")],
        [InlineKeyboardButton(COURSES["target"]["name"],    callback_data="course_target")],
        [InlineKeyboardButton(COURSES["other"]["name"],     callback_data="course_other")],
    ])

def phone_keyboard():
    """Show Telegram's native Share Phone Number button."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Apna Number Share Karo", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def post_delivery_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("😊 Thanks! Maza Aa Gaya!",     callback_data="thanks")],
        [InlineKeyboardButton("💬 Feedback / Comment Likhna", callback_data="askfeedback")],
        [InlineKeyboardButton("❌ Course Nahi Mila Mujhe",    callback_data="notreceived")],
    ])

# ──────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Paid Course Bot mein swagat hai!\n\n"
        "Apna Course chunein 👇\n\n"
        "Sirf Rs.49 mein Access paayein!\n"
        "Payment ke baad Done button dabayein ✅",
        reply_markup=home_keyboard(),
    )

async def course_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("course_", "")
    course = COURSES.get(key)
    if not course:
        return
    ctx.user_data["selected_course"] = key
    caption = (
        f"{course['desc']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Payment Details:\n\n"
        "Amount: Rs.49 only\n\n"
        "Steps:\n"
        "1. QR Scan karo ya UPI ID use karo\n"
        "2. Rs.49 pay karo\n"
        "3. Done button dabao\n"
        "4. Admin Course Link bhejega\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await query.message.reply_photo(
        photo=QR_CODE_URL,
        caption=caption,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Payment Ho Gayi — Done!", callback_data=f"done_{key}")],
            [InlineKeyboardButton("⬅️ Doosra Course Chunein",  callback_data="back_home")],
        ]),
    )

async def done_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("done_", "")
    course_name = COURSES.get(key, {}).get("name", key)
    user = query.from_user

    # Save course name — needed when phone arrives
    AWAITING_PHONE[user.id] = course_name

    # Ask for phone number
    await query.message.reply_text(
        "✅ Payment confirm karne ke liye\n"
        "apna Phone Number share karo 👇\n\n"
        "Neeche wala button dabao:",
        reply_markup=phone_keyboard(),
    )

async def receive_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Triggered when user shares their contact/phone number."""
    user = update.effective_user
    contact = update.message.contact
    phone = contact.phone_number
    course_name = AWAITING_PHONE.pop(user.id, "Unknown Course")
    uname = f"@{user.username}" if user.username else "(username nahi hai)"

    # Remove the phone share keyboard
    await update.message.reply_text(
        "✅ Phone Number Mil Gaya!\n\n"
        f"Course: {course_name}\n\n"
        "Admin verify kar raha hai...\n"
        "5-15 min mein Course Link aayega! 🎉",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Notify admin with full details including phone
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            "🔔 Naya Payment Request!\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Name    : {user.full_name}\n"
            f"User ID : {user.id}\n"
            f"Username: {uname}\n"
            f"Phone   : {phone}\n"
            f"Course  : {course_name}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Link bhejne ke liye:\n/send {user.id}\n\n"
            f"Reject karne ke liye:\n/reject {user.id}"
        )
        logging.info(f"[PHONE] Admin notified for user {user.id}, phone={phone}")
    except Exception as e:
        logging.warning(f"Admin phone alert failed: {e}")

async def send_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /send USER_ID")
        return
    ctx.bot_data["pending_send"] = ctx.args[0]
    ctx.user_data["admin_sending"] = True
    await update.message.reply_text(
        f"User {ctx.args[0]} ko bhejne ke liye\nAb Course Link type karo 👇"
    )

async def admin_forward(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.user_data.get("admin_sending"):
        return
    target_id = ctx.bot_data.get("pending_send")
    if not target_id:
        return
    try:
        await ctx.bot.send_message(
            int(target_id),
            "🎉 Payment Verified! Course Access Mila!\n\n"
            + update.message.text +
            "\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Happy Learning! ✅\n\n"
            "Kya aapko course mila? Feedback do 👇",
            reply_markup=post_delivery_keyboard(),
        )
        await update.message.reply_text(f"✅ User {target_id} ko link bhej diya!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    ctx.user_data["admin_sending"] = False
    ctx.bot_data.pop("pending_send", None)

# ──────────────────────────────────────────
# Post-delivery callbacks
# ──────────────────────────────────────────

async def ask_feedback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    AWAITING_FEEDBACK[user_id] = True
    logging.info(f"[FEEDBACK] awaiting_feedback set for user_id={user_id}")
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.reply_text(
        "✍️ Apna feedback ya comment neeche type karo:\n\n"
        "(Course kaisa laga? Koi problem? Koi suggestion?)"
    )

async def handle_thanks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uname = f"@{user.username}" if user.username else "(username nahi hai)"
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.reply_text(
        "🙏 Shukriya! Aapka Dhanyawad!\n\n"
        "Khub padho, khub seekho! 📚\n"
        "Agar aur koi course chahiye toh /start karo.\n\n"
        "Apne doston ko bhi batao! 😊"
    )
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            "😊 Thanks Message Mila!\n"
            f"User  : {user.full_name} ({uname})\n"
            f"ID    : {user.id}\n"
            "Status: Khush hai ✅"
        )
    except Exception as e:
        logging.warning(f"Thanks admin alert failed: {e}")

async def handle_not_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uname = f"@{user.username}" if user.username else "(username nahi hai)"
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.reply_text(
        "😟 Oops! Sharmindagi ke liye maafi!\n\n"
        "Aapki complaint admin ko bhej di gayi hai.\n"
        "15 minute mein aapko course link milega.\n\n"
        "Agar tab bhi nahi mila toh /start karke dobara try karo."
    )
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            "🚨 Course Nahi Mila — Complaint!\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Name    : {user.full_name}\n"
            f"Username: {uname}\n"
            f"User ID : {user.id}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Turant link bhejo:\n/send {user.id}"
        )
    except Exception as e:
        logging.warning(f"Not-received admin alert failed: {e}")

# ──────────────────────────────────────────
# User text handler (feedback mode)
# ──────────────────────────────────────────

async def handle_user_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    uname = f"@{user.username}" if user.username else "(username nahi hai)"
    logging.info(f"[TEXT] from user_id={user_id}, awaiting_feedback={AWAITING_FEEDBACK.get(user_id)}")

    if AWAITING_FEEDBACK.get(user_id):
        feedback_text = update.message.text
        AWAITING_FEEDBACK[user_id] = False
        await update.message.reply_text(
            "✅ Aapka feedback mil gaya! Bahut shukriya 🙏\n\n"
            "Hum isko improve karne mein zaroor use karenge.\n"
            "Koi aur course chahiye toh /start karo! 📚"
        )
        try:
            await ctx.bot.send_message(
                ADMIN_ID,
                "💬 User Feedback Aaya!\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"Name    : {user.full_name}\n"
                f"Username: {uname}\n"
                f"User ID : {user_id}\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"Feedback:\n{feedback_text}"
            )
            logging.info(f"[FEEDBACK] Sent to admin from user_id={user_id}")
        except Exception as e:
            logging.warning(f"Feedback admin send failed: {e}")
    else:
        await update.message.reply_text(
            "Koi bhi course lene ke liye /start karo 😊"
        )

async def reject_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.args:
        return
    user_id = int(ctx.args[0])
    try:
        await ctx.bot.send_message(
            user_id,
            "❌ Payment Verify Nahi Huyi!\nDobara /start karke try karein.",
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception:
        pass
    await update.message.reply_text(f"User {user_id} reject kiya.")

async def back_home(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Course Chunein:", reply_markup=home_keyboard())

# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("send",   send_cmd))
    app.add_handler(CommandHandler("reject", reject_cmd))

    # Course flow
    app.add_handler(CallbackQueryHandler(course_selected,     pattern="^course_"))
    app.add_handler(CallbackQueryHandler(done_payment,        pattern="^done_"))
    app.add_handler(CallbackQueryHandler(back_home,           pattern="^back_home$"))

    # Post-delivery feedback buttons
    app.add_handler(CallbackQueryHandler(ask_feedback,        pattern="^askfeedback$"))
    app.add_handler(CallbackQueryHandler(handle_thanks,       pattern="^thanks$"))
    app.add_handler(CallbackQueryHandler(handle_not_received, pattern="^notreceived$"))

    # ✅ Phone number (contact) handler — fires when user shares contact
    app.add_handler(MessageHandler(filters.CONTACT, receive_phone))

    # Admin text (course link sending) — MUST be before user text handler
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID),
        admin_forward
    ))

    # User text (feedback or default reply)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.User(ADMIN_ID),
        handle_user_text
    ))

    print("Bot chal raha hai...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
