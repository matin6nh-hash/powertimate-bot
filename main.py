"""
PowerTeamit Telegram Bot
Compatible with python-telegram-bot==21.3
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters,
    ContextTypes
)

BOT_TOKEN = "8885657885:AAELo212q5imxrrH17P6CMNdj2wIdOzgUtI"
ADMIN_CHAT_ID = 1341460786

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GAME_NAME, TITLE, DESCRIPTION, MAIN_IMAGE, EXTRA_IMAGES, PRICE, IS_INSTANT, LOGIN_INFO, CONFIRM = range(9)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["extra_images"] = []
    await update.message.reply_text(
        "👋 خوش اومدی به پنل ثبت آیتم PowerTeamit!\n\n"
        "چند تا سوال ازت می‌پرسم تا اکانتت رو ثبت کنیم.\n\n"
        "❌ هر وقت خواستی لغو کنی، /cancel بزن.\n\n"
        "🎮 اول بگو اکانت مربوط به کدوم بازیه؟\n"
        "مثال: Call of Duty، Fortnite، CS2 ..."
    )
    return GAME_NAME


async def get_game_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["game_name"] = update.message.text.strip()
    await update.message.reply_text(
        "✅ ثبت شد.\n\n📝 یه تایتل جذاب برای اکانت بنویس:\n"
        "مثال: «اکانت سطح ۱۵۰ با ۳ اسکین لجندری»"
    )
    return TITLE


async def get_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["title"] = update.message.text.strip()
    await update.message.reply_text(
        "✅ ثبت شد.\n\n📄 یه توضیح کامل از اکانت بده:\n"
        "مثال: اسکین‌ها، سطح، rank، آیتم‌های خاص ..."
    )
    return DESCRIPTION


async def get_description(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["description"] = update.message.text.strip()
    await update.message.reply_text(
        "✅ ثبت شد.\n\n🖼 تصویر اصلی (main image) اکانت رو بفرست:"
    )
    return MAIN_IMAGE


async def get_main_image(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ لطفاً یه عکس بفرست (نه فایل).")
        return MAIN_IMAGE
    ctx.user_data["main_image"] = update.message.photo[-1].file_id
    keyboard = [[InlineKeyboardButton("✅ بدون عکس اضافه، ادامه بده", callback_data="skip_extra")]]
    await update.message.reply_text(
        "✅ تصویر اصلی ثبت شد.\n\n📸 اگه عکس‌های بیشتری داری بفرست، وگرنه دکمه زیر رو بزن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EXTRA_IMAGES


async def get_extra_images(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        ctx.user_data["extra_images"].append(update.message.photo[-1].file_id)
        count = len(ctx.user_data["extra_images"])
        keyboard = [[InlineKeyboardButton(f"✅ همین {count} تا کافیه، ادامه بده", callback_data="skip_extra")]]
        await update.message.reply_text(
            f"📸 عکس {count} ثبت شد:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("⚠️ لطفاً عکس بفرست یا دکمه «ادامه» رو بزن.")
    return EXTRA_IMAGES


async def skip_extra_images(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "✅ عکس‌ها ثبت شدن.\n\n💰 قیمت پیشنهادیت چقدره؟ (به دلار)\nمثال: 25.00"
    )
    return PRICE


async def get_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً یه عدد معتبر وارد کن. مثال: 25.00")
        return PRICE
    ctx.user_data["price"] = price
    keyboard = [[
        InlineKeyboardButton("⚡ بله، instant هست", callback_data="instant_yes"),
        InlineKeyboardButton("❌ نه", callback_data="instant_no"),
    ]]
    await update.message.reply_text(
        f"✅ قیمت ${price:.2f} ثبت شد.\n\n⚡ آیا این اکانت instant delivery هست؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return IS_INSTANT


async def is_instant_yes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    ctx.user_data["is_instant"] = True
    await update.callback_query.message.reply_text(
        "🔐 اطلاعات ورود به اکانت رو وارد کن:\n"
        "Email: example@mail.com\nPassword: yourpassword\n\n"
        "⚠️ این اطلاعات فقط برای ادمین ارسال میشه."
    )
    return LOGIN_INFO


async def is_instant_no(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    ctx.user_data["is_instant"] = False
    ctx.user_data["login_info"] = "N/A"
    return await show_summary(update.callback_query.message, ctx)


async def get_login_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["login_info"] = update.message.text.strip()
    return await show_summary(update.message, ctx)


async def show_summary(message, ctx: ContextTypes.DEFAULT_TYPE):
    d = ctx.user_data
    extra_count = len(d.get("extra_images", []))
    instant_text = "⚡ بله (Instant)" if d.get("is_instant") else "❌ خیر"
    summary = (
        "📋 *خلاصه آیتم ثبت‌شده:*\n\n"
        f"🎮 بازی: {d.get('game_name')}\n"
        f"📝 تایتل: {d.get('title')}\n"
        f"📄 توضیحات: {d.get('description')}\n"
        f"🖼 تصاویر: ۱ main + {extra_count} اضافه\n"
        f"💰 قیمت پیشنهادی: ${d.get('price'):.2f}\n"
        f"⚡ Instant: {instant_text}\n"
    )
    keyboard = [[
        InlineKeyboardButton("✅ تایید و ارسال", callback_data="submit"),
        InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart"),
    ]]
    await message.reply_text(summary, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM


async def submit_listing(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    d = ctx.user_data
    seller = update.callback_query.from_user
    seller_info = f"@{seller.username}" if seller.username else f"ID:{seller.id}"
    instant_text = "⚡ بله (Instant)" if d.get("is_instant") else "❌ خیر"
    admin_msg = (
        "🆕 *آیتم جدید برای بررسی*\n\n"
        f"👤 فروشنده: {seller_info}\n"
        f"🎮 بازی: {d.get('game_name')}\n"
        f"📝 تایتل: {d.get('title')}\n"
        f"📄 توضیحات: {d.get('description')}\n"
        f"💰 قیمت: ${d.get('price'):.2f}\n"
        f"⚡ Instant: {instant_text}\n"
    )
    if d.get("is_instant"):
        admin_msg += f"\n🔐 اطلاعات ورود:\n`{d.get('login_info')}`"
    keyboard = [[
        InlineKeyboardButton("✅ تایید", callback_data=f"approve_{seller.id}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject_{seller.id}"),
    ]]
    try:
        await ctx.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=d.get("main_image"),
            caption=admin_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        extra = d.get("extra_images", [])
        if extra:
            await ctx.bot.send_media_group(
                chat_id=ADMIN_CHAT_ID,
                media=[InputMediaPhoto(fid) for fid in extra]
            )
    except Exception as e:
        logger.error(f"خطا: {e}")
        await update.callback_query.message.reply_text("⚠️ مشکلی پیش اومد. دوباره تلاش کن.")
        return ConversationHandler.END
    await update.callback_query.message.reply_text(
        "✅ آیتمت ثبت شد و برای ادمین فرستاده شد! 🙏"
    )
    ctx.user_data.clear()
    return ConversationHandler.END


async def restart_listing(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    ctx.user_data.clear()
    ctx.user_data["extra_images"] = []
    await update.callback_query.message.reply_text("🔄 از اول شروع می‌کنیم!\n\n🎮 اسم بازی رو بنویس:")
    return GAME_NAME


async def admin_approve(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("✅ تایید شد!")
    seller_id = int(update.callback_query.data.split("_")[1])
    await update.callback_query.message.edit_reply_markup(reply_markup=None)
    await update.callback_query.message.reply_text("✅ این آیتم تایید شد.")
    try:
        await ctx.bot.send_message(
            chat_id=seller_id,
            text="🎉 آیتمت تایید شد! به زودی لیست میشه. ممنون 🙏"
        )
    except Exception as e:
        logger.error(f"خطا: {e}")


async def admin_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("❌ رد شد.")
    seller_id = int(update.callback_query.data.split("_")[1])
    await update.callback_query.message.edit_reply_markup(reply_markup=None)
    await update.callback_query.message.reply_text("❌ این آیتم رد شد.")
    try:
        await ctx.bot.send_message(
            chat_id=seller_id,
            text="❌ آیتمت تایید نشد. برای سوال با ادمین تماس بگیر.\nبرای ثبت مجدد /start بزن."
        )
    except Exception as e:
        logger.error(f"خطا: {e}")


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ لغو شد. هر وقت آماده بودی /start بزن.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GAME_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_game_name)],
            TITLE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            MAIN_IMAGE:   [MessageHandler(filters.PHOTO, get_main_image)],
            EXTRA_IMAGES: [
                MessageHandler(filters.PHOTO, get_extra_images),
                CallbackQueryHandler(skip_extra_images, pattern="^skip_extra$"),
            ],
            PRICE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            IS_INSTANT:   [
                CallbackQueryHandler(is_instant_yes, pattern="^instant_yes$"),
                CallbackQueryHandler(is_instant_no, pattern="^instant_no$"),
            ],
            LOGIN_INFO:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login_info)],
            CONFIRM:      [
                CallbackQueryHandler(submit_listing, pattern="^submit$"),
                CallbackQueryHandler(restart_listing, pattern="^restart$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_approve, pattern=r"^approve_\d+$"))
    app.add_handler(CallbackQueryHandler(admin_reject, pattern=r"^reject_\d+$"))
    print("🤖 ربات PowerTeamit در حال اجراست...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
