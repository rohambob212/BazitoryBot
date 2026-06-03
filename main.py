import logging
from telegram.constants import ChatType, ChatMemberStatus
import json as js
import links as lnk
import names as nms
from datetime import datetime, timedelta, timezone
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler, CallbackQueryHandler
from asyncio import create_task

tkn = ""
with open("../token.txt", "r") as token:
    tkn = token.read().replace("\n", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
#ban
bancs : list[str] = ["ban", "!ban", "بن", "!بن"]
banlistcs : list[str] = ["ban list", "!ban list", "لیست بن", "!لیست بن"]
unbancs : list[str] = ["unban", "!unban", "آن بن", "!آن بن"]

# لیست کلمات کلیدی برای سکوت (جدید)
mutecs : list[str] = ["mute", "!mute", "سکوت", "!سکوت"]
mutelistcs : list[str] = ["mutelist", "!mutelist", "لیست سکوت", "!لیست سکوت"]
unmutecs : list[str] = ["unmute", "!unmute", "حذف سکوت", "!حذف سکوت"]

# توابع دیتابیس بن
def loadDB():
    with open("BanDB.json", 'r', encoding='utf-8') as f:
        return js.load(f)

def saveDB(data):
    with open("BanDB.json", 'w', encoding='utf-8') as f:
        js.dump(data, f, indent=2, ensure_ascii=False)

banlist : dict = loadDB()

# توابع دیتابیس سکوت (جدید)
def loadMuteDB():
    try:
        with open("MuteDB.json", 'r', encoding='utf-8') as f:
            return js.load(f)
    except FileNotFoundError:
        return {}

def saveMuteDB(data):
    with open("MuteDB.json", 'w', encoding='utf-8') as f:
        js.dump(data, f, indent=2, ensure_ascii=False)

mutelist : dict = loadMuteDB()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type != ChatType.PRIVATE:
        return
    keyboard = [
        [InlineKeyboardButton("🌐 سایتمون", url=lnk.website)],
        [
            InlineKeyboardButton("👥 گروه چت اصلی", url=lnk.chat),
            InlineKeyboardButton("🔈 کانال اطلاع رسانی", url=lnk.channel),
        ],
        [InlineKeyboardButton("💸 دونیت", url=lnk.donate)],
        [InlineKeyboardButton("💫 سرور های zerotier", url=lnk.zerotier)],
        [InlineKeyboardButton("🧪 بازی های کانفیگ شده", url=lnk.games)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(nms.stxt, reply_markup=reply_markup)


async def tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("فقط توی گروه ها میتونی تگت رو عوض کنی")
        return
    await context.bot.set_chat_member_tag(update.effective_chat.id, update.message.from_user.id, update.message.text.replace("/tag ", ""))
    await update.message.reply_text(f"تگ شما به {update.message.text.replace('/tag ', '')} تغییر کرد")


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
    banlist[str(baned.id)] = {"id": str(baned.id), "name": baned.name, "msg": update.message.reply_to_message.text}
    saveDB(banlist)
    await update.message.reply_text(f"بن شد {baned.name} ")


async def banlistshow(update: Update, context: ContextTypes.DEFAULT_TYPE, pg: int = 1) -> None:
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


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("فقط توی گروه ها میتونی سکوت بزنی")
        return

    muter = await update.effective_chat.get_member(update.effective_user.id)
    if muter.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("برای سکوت کردن باید رو پیام کاربر ریپلای کنی 😭")
        return

    muted = update.message.reply_to_message.from_user
    if muted == update.effective_user:
        await update.message.reply_text("نمیتونی خودت رو سکوت کنی! 😂")
        return
    if muted == await context.bot.get_me():
        await update.message.reply_text("منو میخوای لال کنی؟ نکن ادمین عزیز 😭")
        return
    
    muted_member = await update.effective_chat.get_member(muted.id)
    if muted_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await update.message.reply_text("نمیتونی یه ادمین رو سکوت کنی 😭")
        return

    # اصلاح نحوه خواندن کامند و تایم
    tokens = update.message.text.split()
    until_date = None
    duration_text = "همیشگی"

    # اگر چیزی بعد از کلمه کلیدی mute نوشته شده بود (مثلا 10m یا 1h)
    if len(tokens) > 1:
        time_str = tokens[1]
        try:
            amount = int(time_str[:-1])
            unit = time_str[-1].lower()
            
            if unit == 'm':
                delta = timedelta(minutes=amount)
                duration_text = f"{amount} دقیقه"
            elif unit == 'h':
                delta = timedelta(hours=amount)
                duration_text = f"{amount} ساعت"
            elif unit == 'd':
                delta = timedelta(days=amount)
                duration_text = f"{amount} روز"
            else:
                raise ValueError()
                
            # استفاده از timezone.utc برای تطابق با زمان کلاینت سرورهای تلگرام
            until_date = datetime.now(timezone.utc) + delta
        except (ValueError, IndexError):
            await update.message.reply_text("فرمت زمان اشتباهه! نمونه صحیح: `mute 10m` یا `mute 2h`")
            return

    # بستن تمام دسترسی‌های ارسال پیام
    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )

    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=muted.id,
            permissions=permissions,
            until_date=until_date
        )
        
        # ذخیره در دیتابیس سکوت
        global mutelist
        mutelist[str(muted.id)] = {
            "id": str(muted.id),
            "name": muted.name,
            "duration": duration_text
        }
        saveMuteDB(mutelist)
        
        await update.message.reply_text(f"کاربر {muted.name} برای {duration_text} سکوت شد 🤫")
    except Exception as e:
        await update.message.reply_text(f"خطایی رخ داد: {e}")


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
        await callback.edit_message_text(f"یوزرنیم : {db[str(id)]['name']}\nپیام : {db[str(id)]['msg']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("آن بن",callback_data="unban"+str(id))],[InlineKeyboardButton("بازگشت به صفحه قبل 📄",callback_data="gobanlistpg1")]]))


def main() -> None:
    app = Application.builder().token(tkn).build()

    app.add_handler(CallbackQueryHandler(callbackhandler))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tag", tag))
    
    # هندلرهای Ban
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(bancs) + r")$"), ban))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(banlistcs) + r")$"), banlistshow))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(unbancs) + r")$"), unban))
    
    # اصلاح رجکس Mute برای پذیرش پارامترهای بعدی مانند فاصله و تایم
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(mutecs) + r")(\s|$)"), mute))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(mutelistcs) + r")$"), mutelistshow))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"(?i)^(" + "|".join(unmutecs) + r")$"), unmute))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()