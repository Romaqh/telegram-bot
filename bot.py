from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    Application,
)
from telegram import Update

import os
import asyncio
import redis

# Redis 连接
redis_url = os.environ.get("REDIS_URL")
r = redis.from_url(redis_url) if redis_url else None

# 命令处理
async def start(update: Update, context):
    keyboard = [
        ["[签到]", "[下载]"],
        ["[使用说明]", "[推广]"],
        ["[购买]"]
    ]
    reply_markup = {"keyboard": keyboard, "resize_keyboard": True}
    await update.message.reply_text("欢迎使用！请选择：", reply_markup=reply_markup)

async def sign(update: Update, context):
    user_id = update.message.from_user.id
    if r and r.get(f"signed_{user_id}") is None:
        r.setex(f"signed_{user_id}", 86400, "1")  # 24小时有效
        await update.message.reply_text("+20 积分，今天签到人数：1")
    else:
        await update.message.reply_text("今天已签到！")

async def download(update: Update, context):
    await update.message.reply_text("下载功能待开发，请稍后！")

async def usage(update: Update, context):
    await update.message.reply_text("使用说明：/start 开始，[签到] 每日+20积分，[推广] 获取邀请链接，[购买] 联系管理员。")

async def promote(update: Update, context):
    user_id = update.message.from_user.id
    invite_link = f"https://t.me/DMAROMA2?start={user_id}"
    await update.message.reply_text(f"推广链接：{invite_link}，邀请好友得积分！")

async def buy(update: Update, context):
    await update.message.reply_text("购买功能：请联系 @ROMADMA 管理员！")

async def verify(update: Update, context):
    await update.message.reply_text("已验证，请自由发言！")

# 群成员更新
async def member_update(update: Update, context):
    if update.chat_member and update.chat_member.new_chat_member:
        user = update.chat_member.new_chat_member.user
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"欢迎 {user.username}！请关注 @ROMADMA，回复 /verify")

# 主函数
async def main():
    application = Application.builder().token(os.environ["BOT_TOKEN"]).build()

    # 添加处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sign", sign))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CommandHandler("usage", usage))
    application.add_handler(CommandHandler("promote", promote))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("verify", verify))
    application.add_handler(MessageHandler(filters.StatusUpdate.CHAT_MEMBER, member_update))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: update.message.reply_text("未知命令，请用 /start 查看菜单！")))

    return application

if __name__ == "__main__":
    import asyncio
    port = int(os.environ.get("PORT", 5000))
    application = asyncio.run(main())
    application.run_webhook(listen="0.0.0.0", port=port)
