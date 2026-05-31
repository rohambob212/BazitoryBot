import logging
import links as lnk
import names as nms
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes
# from scraper import getgames
from asyncio import create_task
# games : list = list(getgames())
tkn = "enter token here"
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        return
    keyboard = [
        [InlineKeyboardButton("🌐 سایتمون", url=lnk.website)],
        [
            InlineKeyboardButton("👥 گروه چت اصلی", url=lnk.chat),
            InlineKeyboardButton("🔈 کانال اطلاع رسانی", url=lnk.channel),
        ],
        # [InlineKeyboardButton("poshtibani", url=lnk)],
        [InlineKeyboardButton("💸 دونیت", url=lnk.donate)],
        [InlineKeyboardButton("💫 سرور های zerotier", url=lnk.zerotier)],
        [InlineKeyboardButton("🧪 بازی های کانفیگ شده", url=lnk.games)],

    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(nms.stxt, reply_markup=reply_markup)

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(update.effective_chat.id)


# async def setgames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     ngames = getgames()
#     if len(ngames) > len(games):
#         pass

def main() -> None:
    application = Application.builder().token(tkn).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", id))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
