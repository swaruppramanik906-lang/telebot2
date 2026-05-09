import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

def post_delivery_keyboard(user_id: int):
    """Keyboard shown after admin sends course link."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ 5 Star",  callback_data=f"rate_5_{user_id}"),
            InlineKeyboardButton("⭐ 4 Star",  callback_data=f"rate_4_{user_id}"),
            InlineKeyboardButton("⭐ 3 Star",  callback_data=f"rate_3_{user_id}"),
        ],
        [InlineKeyboardButton("😊 Thanks! Maza Aa Gaya!",    callback_data=f"thanks_{user_id}")],
        [InlineKeyboardButton("❌ Course Nahi Mila Mujhe",   callback_data=f"notreceived_{user_id}")],
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
    uname = f"@{user.username}" if user.username else "(username nahi hai)"
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            "🔔 Naya Payment Request!\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Name    : {user.full_name}\n"
            f"User ID : {user.id}\n"
            f"Username: {uname}\n"
            f"Course  : {course_name}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Link bhejne ke liye:\n/send {user.id}\n\n"
            f"Reject karne ke liye:\n/reject {user.id}"
        )
    except Exception as e:
        logging.warning(f"Admin alert failed: {e}")
    await query.message.reply_text(
        "✅ Request Receive Ho Gayi!\n\n"
        f"Course: {course_name}\n\n"
        "Admin verify kar raha hai...\n"
        "5-15 min mein Course Link aayega!"
    )

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
        # Send course link to user WITH post-delivery keyboard
        await ctx.bot.send_message(
            int(target_id),
            "🎉 Payment Verified! Course Access Mila!\n\n"
            + update.message.text +
            "\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Happy Learning! ✅\n\n"
            "Kya aapko course mila? Feedback do 👇",
            reply_markup=post_delivery_keyboard(int(target_id)),
        )
        await update.message.reply_text(f"✅ User {target_id} ko link bhej diya!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    ctx.user_data["admin_sending"] = False
    ctx.bot_data.pop("pending_send", None)

# ──────────────────────────────────────────
# NEW: Rating Handler
# ──────────────────────────────────────────

async def handle_rating(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")   # rate_5_userid
    stars = int(parts[1])
    user = query.from_user
    uname = f"@{user.username}" if user.username else "(username nahi hai)"

    star_emoji = "⭐" * stars
    await query.message.edit_reply_markup(reply_markup=None)  # Remove keyboard
    await query.message.reply_text(
        f"Shukriya! {star_emoji} Rating ke liye!\n\n"
        "Aapka feedback humein behtar banata hai! 💪\n"
        "Koi bhi problem ho toh /start karo."
    )

    # Notify admin about rating
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"⭐ Naya Rating Mila!\n"
            f"User  : {user.full_name} ({uname})\n"
            f"ID    : {user.id}\n"
            f"Rating: {star_emoji} ({stars}/5)"
        )
    except Exception as e:
        logging.warning(f"Rating admin alert failed: {e}")

# ──────────────────────────────────────────
# NEW: Thanks Handler
# ──────────────────────────────────────────

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

    # Notify admin
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"😊 Thanks Message Mila!\n"
            f"User  : {user.full_name} ({uname})\n"
            f"ID    : {user.id}\n"
            f"Status: Khush hai ✅"
        )
    except Exception as e:
        logging.warning(f"Thanks admin alert failed: {e}")

# ──────────────────────────────────────────
# NEW: Course Not Received Handler
# ──────────────────────────────────────────

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

    # Alert admin urgently
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"🚨 Course Nahi Mila — Complaint!\n"
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
# NEW: Text Feedback Handler (after rating)
# ──────────────────────────────────────────

async def handle_text_feedback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Collect written feedback from users (when not admin)."""
    if update.effective_user.id == ADMIN_ID:
        return  # Let admin_forward handle admin messages
    user = update.effective_user
    uname = f"@{user.username}" if user.username else "(username nahi hai)"
    feedback_text = update.message.text

    await update.message.reply_text(
        "✅ Aapka feedback mil gaya! Shukriya 🙏\n"
        "Hum isko improve karne mein use karenge."
    )

    # Forward feedback to admin
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"💬 User Feedback Aaya!\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Name    : {user.full_name}\n"
            f"Username: {uname}\n"
            f"User ID : {user.id}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Feedback:\n{feedback_text}"
        )
    except Exception as e:
        logging.warning(f"Feedback admin alert failed: {e}")

async def reject_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.args:
        return
    user_id = int(ctx.args[0])
    try:
        await ctx.bot.send_message(
            user_id,
            "❌ Payment Verify Nahi Huyi!\nDobara /start karke try karein."
        )
    except:
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
    app.add_handler(CallbackQueryHandler(course_selected,    pattern="^course_"))
    app.add_handler(CallbackQueryHandler(done_payment,       pattern="^done_"))
    app.add_handler(CallbackQueryHandler(back_home,          pattern="^back_home$"))

    # NEW: Post-delivery feedback callbacks
    app.add_handler(CallbackQueryHandler(handle_rating,      pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(handle_thanks,      pattern="^thanks_"))
    app.add_handler(CallbackQueryHandler(handle_not_received, pattern="^notreceived_"))

    # Admin forward (must stay BEFORE user text handler)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID),
        admin_forward
    ))

    # NEW: User text feedback (non-admin users)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.User(ADMIN_ID),
        handle_text_feedback
    ))

    print("Bot chal raha hai...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
