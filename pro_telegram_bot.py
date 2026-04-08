from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3

TOKEN = "8657547531:AAF5Wd2PT9NYGORAg4I3ONGKLWaD97pAv6M"
BOT_USERNAME = "dgnsgjsfbot"
CHANNEL_USERNAME = "@sjdbskdb"
ADMIN_ID = 7897070744  # ضع ايدي حسابك هنا

# قاعدة البيانات
conn = sqlite3.connect("pro_bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    invited_by INTEGER
)
""")
conn.commit()

# التحقق من الاشتراك
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    invited_by = None
    if context.args:
        invited_by = int(context.args[0])

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id, invited_by) VALUES (?,?)", (user_id, invited_by))
        conn.commit()

        if invited_by and invited_by != user_id:
            cursor.execute("UPDATE users SET points = points + 50 WHERE user_id=?", (invited_by,))
            conn.commit()

    keyboard = [
        [InlineKeyboardButton("🎯 نقاطي", callback_data="points")],
        [InlineKeyboardButton("📋 المهام", callback_data="tasks")],
        [InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="invite")],
        [InlineKeyboardButton("💰 سحب", callback_data="withdraw")]
    ]

    await update.message.reply_text("💸 أهلاً بك في بوت الربح", reply_markup=InlineKeyboardMarkup(keyboard))

# الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "points":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        await query.answer()
        await query.message.reply_text(f"🎯 نقاطك: {points}")

    elif query.data == "tasks":
        is_subscribed = await check_subscription(user_id, context)

        if not is_subscribed:
            keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")]]
            await query.message.reply_text("❗ لازم تشترك بالقناة أولاً", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        cursor.execute("UPDATE users SET points = points + 20 WHERE user_id=?", (user_id,))
        conn.commit()
        await query.answer()
        await query.message.reply_text("✅ تم التحقق +20 نقطة")

    elif query.data == "invite":
        link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        await query.answer()
        await query.message.reply_text(f"👥 رابطك:\n{link}\n\n💰 تحصل 50 نقطة لكل شخص")

    elif query.data == "withdraw":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]

        if points >= 200:
            await context.bot.send_message(
                ADMIN_ID,
                f"💰 طلب سحب\n\n👤 المستخدم: {user_id}\n🎯 النقاط: {points}"
            )

            cursor.execute("UPDATE users SET points = 0 WHERE user_id=?", (user_id,))
            conn.commit()

            await query.message.reply_text("✅ تم إرسال طلبك للإدارة")
        else:
            await query.message.reply_text("❌ تحتاج 200 نقطة")

# لوحة الأدمن
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    await update.message.reply_text(f"👑 عدد المستخدمين: {users}")

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(buttons))

print("🔥 البوت الاحترافي يعمل")
app.run_polling()
