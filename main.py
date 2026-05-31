import logging

from telegram.constants import ChatType, ChatMemberStatus

import links as lnk
import names as nms
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler
# from scraper import getgames
from asyncio import create_task
# games : list = list(getgames())
tkn = ""
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

#bancs : list[str] = ["ban", "!ban", "بن", "!بن"]
bancs : list[str] = ["ban", "!ban", "بن", "!بن"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type != ChatType.PRIVATE:
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


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("فقط توی گروه ها میتونی بن کنی")
        return

    baner = await update.effective_chat.get_member(update.effective_user.id)
    if baner.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("برای بن کردن باید به مسیج ریپلای بدی 😭")
        return

    baned = update.message.reply_to_message.from_user
    baned_member = await update.effective_chat.get_member(baned.id)
    if baned_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await update.message.reply_text("داش نمیتونی یه ادمین رو بن کنی 😭")
        return

    await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=baned.id)
    await update.message.reply_text(f"{baned.first_name} بن شد")


# async def setgames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     ngames = getgames()
#     if len(ngames) > len(games):
#         pass

def main() -> None:
    app = Application.builder().token(tkn).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(bancs) + r")$"), ban))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
