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

def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(COURSES["pw"]["name"],        callback_data="course_pw")],
        [InlineKeyboardButton(COURSES["unacademy"]["name"], callback_data="course_unacademy")],
        [InlineKeyboardButton(COURSES["kgs"]["name"],       callback_data="course_kgs")],
        [InlineKeyboardButton(COURSES["target"]["name"],    callback_data="course_target")],
        [InlineKeyboardButton(COURSES["other"]["name"],     callback_data="course_other")],
    ])

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
            "Naya Payment Request!\n"
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
        "Request Receive Ho Gayi!\n\n"
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
        await ctx.bot.send_message(
            int(target_id),
            "Payment Verified! Course Access Mila!\n\n"
            + update.message.text +
            "\n\nHappy Learning! ✅"
        )
        await update.message.reply_text(f"User {target_id} ko link bhej diya!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    ctx.user_data["admin_sending"] = False
    ctx.bot_data.pop("pending_send", None)

async def reject_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.args:
        return
    user_id = int(ctx.args[0])
    try:
        await ctx.bot.send_message(
            user_id,
            "Payment Verify Nahi Huyi!\nDobara /start karke try karein."
        )
    except:
        pass
    await update.message.reply_text(f"User {user_id} reject kiya.")

async def back_home(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Course Chunein:", reply_markup=home_keyboard())

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("send",   send_cmd))
    app.add_handler(CommandHandler("reject", reject_cmd))
    app.add_handler(CallbackQueryHandler(course_selected, pattern="^course_"))
    app.add_handler(CallbackQueryHandler(done_payment,    pattern="^done_"))
    app.add_handler(CallbackQueryHandler(back_home,       pattern="^back_home$"))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID),
        admin_forward
    ))
    print("Bot chal raha hai...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
