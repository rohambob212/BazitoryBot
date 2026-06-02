import logging
from telegram.constants import ChatType, ChatMemberStatus
import json as js
import links as lnk
import names as nms
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler, CallbackQueryHandler
# from scraper import getgames
from asyncio import create_task
# games : list = list(getgames())
tkn = ""
with open("../token.txt", "r") as token:
    tkn = token.read()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
banlist : dict = {}
#bancs : list[str] = ["ban", "!ban", "بن", "!بن"]
bancs : list[str] = ["ban", "!ban", "بن", "!بن"]

def loadDB():
    with open("banDB.json", 'r', encoding='utf-8') as f:
        return js.load(f)

def saveDB(data):
    with open("banDB.json", 'w', encoding='utf-8') as f:
        js.dump(data, f, indent=2, ensure_ascii=False)

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
    if baned == update.effective_user:
        await update.message.reply_text("چرا میخوای خودکشی کنی ؟ 😭")
        return
    if baned == context.bot.get_me():
        await update.message.reply_text("چرا میخوای منو بکشی ؟ 😭")
    baned_member = await update.effective_chat.get_member(baned.id)
    if baned_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await update.message.reply_text("نمیتونی یه ادمین رو بن کنی 😭")
        return
    await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=baned.id)
    #await update.message.reply_to_message.delete()
    banlist[str(baned.id)] = {"id": str(baned.id), "name": baned.name, "msg": update.message.reply_to_message.text}
    saveDB(banlist)
    await update.message.reply_text(f"بن شد {baned.name} ")

async def banlistshow(update: Update, context: ContextTypes.DEFAULT_TYPE,pg: int) -> None:
    global banlist
    db = loadDB()
    amount : int = 5
    rpg = pg
    pg *= amount
    dblen : int = len(db.keys)
    allpgs = (dblen - (dblen % 5)) + 1
    if pg > dblen:
        pg = dblen
        amount = pg - dblen
    kb : list = []
    for key in db.keys()[(pg-amount):(pg)]:
        kb.append([InlineKeyboardButton(db[key]["name"], callback_data=("user"+key))])
    kb.append([InlineKeyboardButton(f"📄 صفحه : {pg}/{allpgs}")])
    pgmovers : list[InlineKeyboardButton] = []
    if pg < allpgs:
        pgmovers.append(InlineKeyboardButton("صفحه بعد ⬅️", callback_data=f"gobanlistpg{pg-1}"))
    if pg > 1:
        pgmovers.append(InlineKeyboardButton("➡️ صفحه قبل ", callback_data=f"gobanlistpg{pg+1}"))

    await update.message.reply_text("برادران از دست رفته 🫡")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("فقط توی گروه ها میتونی آن بن کنی")
        return

async def callbackhandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    callback = update.callback_query

    await callback.answer()

    if "gobanlistpg" in callback.data:
        num = int(callback.data[-1])
    banlistshow(pg=num)


# async def setgames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     ngames = getgames()
#     if len(ngames) > len(games):
#         pass

def main() -> None:
    app = Application.builder().token(tkn).build()

    app.add_handler(CallbackQueryHandler(callbackhandler))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(bancs) + r")$"), ban))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
