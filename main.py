import logging
from telegram.constants import ChatType, ChatMemberStatus
import json as js
import links as lnk
import names as nms
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler, CallbackQueryHandler
# from scraper import getgames
from asyncio import create_task
# games : list = list(getgames())
tkn = ""
with open("../token.txt", "r") as token:
    tkn = token.read().replace("\n", "")
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
bancs : list[str] = ["ban", "!ban", "بن", "!بن"]
banlistcs : list[str] = ["ban list", "!ban list", "لیست بن", "!لیست بن"]
unbancs : list[str] = ["unban", "!unban", "آن بن", "!آن بن"]

def loadDB():
    with open("BanDB.json", 'r', encoding='utf-8') as f:
        return js.load(f)

def saveDB(data):
    with open("BanDB.json", 'w', encoding='utf-8') as f:
        js.dump(data, f, indent=2, ensure_ascii=False)
banlist : dict = loadDB()
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

async def tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(update.effective_chat.type)
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("فقط توی گروه ها میتونی تگت رو عوض کنی")
        return
    await context.bot.set_chat_member_tag(update.effective_chat.id, update.message.from_user.id, update.message.text.replace("/tag ", ""))
    await update.message.reply_text(f"تگ شما به {update.message.text.replace("/tag ", "")} تغییر کرد")

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
    if baned == await context.bot.get_me():
        await update.message.reply_text("چرا میخوای منو بکشی ؟ 😭")
        return
    baned_member = await update.effective_chat.get_member(baned.id)
    if baned_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await update.message.reply_text("نمیتونی یه ادمین رو بن کنی 😭")
        return
    await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=baned.id)
    #await update.message.reply_to_message.delete()
    banlist[str(baned.id)] = {"id": str(baned.id), "name": baned.name, "msg": update.message.reply_to_message.text}
    saveDB(banlist)
    await update.message.reply_text(f"بن شد {baned.name} ")

async def banlistshow(update: Update, context: ContextTypes.DEFAULT_TYPE,pg: int = 1) -> None:
    global banlist
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    baner = await update.effective_chat.get_member(update.effective_user.id)
    if baner.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return
    db = loadDB()
    amount : int = 5
    rpg = pg
    pg *= amount
    dblen : int = len(db.keys())
    print(dblen)
    allpgs : int = 1
    if dblen == 0:
        await update.message.reply_text("شما هنوز کسی را بن نکرده اید")
        return
    if dblen <= amount:
        allpgs = 1
    if dblen > amount:
        allpgs = (dblen // amount) + 1
    if pg > dblen:
        amount = pg - dblen
        pg = dblen
    if pg < 5:
        amount = pg
    kb : list = []
    print(list(db.keys())[(pg-amount):(pg)])
    for key in list(db.keys())[(pg-amount):(pg)]:
        kb.append([InlineKeyboardButton(db[key]["name"].replace("@", ""), callback_data=("user"+key))])
    kb.append([InlineKeyboardButton(f"📖 صفحه : {rpg}/{allpgs}", callback_data="pg")])
    pgmovers : list[InlineKeyboardButton] = []
    if rpg < allpgs:
        pgmovers.append(InlineKeyboardButton("صفحه بعد ⬅️", callback_data=f"gobanlistpg{rpg-1}"))
    if rpg > 1:
        pgmovers.append(InlineKeyboardButton("➡️ صفحه قبل ", callback_data=f"gobanlistpg{rpg+1}"))
    kb.append(pgmovers)
    if update.message:
        await update.message.reply_text("برادران از دست رفته 🫡", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.callback_query.edit_message_text("برادران از دست رفته 🫡", reply_markup=InlineKeyboardMarkup(kb))

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("فقط توی گروه ها میتونی آن بن کنی")
        return
    db = loadDB()
    baner = await update.effective_chat.get_member(update.effective_user.id)
    if baner.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("برای آن بن کردن باید به مسیج ریپلای بدی 😭")
        return
    baned = update.message.reply_to_message.from_user
    if str(baned.id) in db.keys():
        await context.bot.unbanChatMember(chat_id=update.effective_chat.id, user_id=baned.id)
        del banlist[str(baned.id)]
        saveDB(banlist)
        await update.message.reply_text(f"آن بن شد {baned.name} ")
    else:
        await update.message.reply_text("بن نیست")

async def callbackhandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    callback = update.callback_query

    await callback.answer()
    if callback.data.startswith("unban"):
        usr = await update.effective_chat.get_member(update.effective_user.id)
        if usr.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
        id = callback.data.split("unban")[1]
        await context.bot.unbanChatMember(chat_id=update.effective_chat.id, user_id=id)
        del banlist[str(id)]
        saveDB(banlist)
        buser = await context.bot.get_chat(id)
        await callback.edit_message_text(f"آن بن شد {buser.first_name} ")
    if callback.data.startswith("gobanlistpg"):
        usr = await update.effective_chat.get_member(update.effective_user.id)
        if usr.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
        num = int(callback.data.replace("gobanlistpg", ""))
        await banlistshow(update, context, num)
    if callback.data.startswith("user"):
        usr = await update.effective_chat.get_member(update.effective_user.id)
        if usr.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
        id = int(callback.data.replace("user", ""))
        db = loadDB()
        await callback.edit_message_text(f"یوزرنیم : {db[str(id)]["name"]}\nپیام : {db[str(id)]["msg"]}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("آن بن",callback_data="unban"+str(id))],[InlineKeyboardButton("بازگشت به صفحه قبل 📄",callback_data="gobanlistpg1")]]))

# async def setgames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     ngames = getgames()
#     if len(ngames) > len(games):
#         pass
def main() -> None:
    app = Application.builder().token(tkn).build()

    app.add_handler(CallbackQueryHandler(callbackhandler))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tag", tag))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(bancs) + r")$"), ban))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(banlistcs) + r")$"), banlistshow))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(unbancs) + r")$"), unban))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()