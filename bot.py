import logging
import json
import redis
from datetime import datetime, timedelta
from telegram import ReplyKeyboardMarkup, Update, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ChatMemberUpdatedFilter,
)
import pytz
import os

# 设置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 配置
GROUP_INVITE_BASE = "https://t.me/DMAROMA2"
CHANNEL_ID = "@ROMADMA"
SHANGHAI_TZ = pytz.timezone("Asia/Shanghai")
KEYBOARD = [
    ["签到", "下载"],
    ["使用说明", "推广", "购买"],
]

# Redis 连接
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_type = update.effective_chat.type
    user_id = str(user.id)

    # 处理 /start 123456789 格式的邀请
    if context.args:
        inviter_id = context.args[0]
        if inviter_id != user_id:
            redis_client.incr(f"invites:{inviter_id}")

    # 私聊显示键盘
    if chat_type == "private":
        keyboard = ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(
            f"欢迎使用机器人！{user.first_name}，键盘已加载，请点击下方按钮：",
            reply_markup=keyboard,
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    text = update.message.text

    if text == "签到":
        today = datetime.now(SHANGHAI_TZ).strftime("%Y-%m-%d")
        last_checkin = redis_client.get(f"checkin:{user_id}:date")

        if last_checkin == today:
            points = redis_client.get(f"points:{user_id}") or 0
            await update.message.reply_text(
                f"{user.first_name}，你今天已签到过啦！明天0点再来吧！当前积分：{points}"
            )
        else:
            redis_client.incr(f"points:{user_id}", 20)
            redis_client.set(f"checkin:{user_id}:date", today)
            redis_client.incr(f"checkin:count:{today}")
            points = redis_client.get(f"points:{user_id}")
            count = redis_client.get(f"checkin:count:{today}")
            await update.message.reply_text(
                f"{user.first_name}，你已成功签到！本次 +20 积分，当前累计积分：{points}\n今天签到人数：{count}"
            )

    elif text == "推广":
        invites = redis_client.get(f"invites:{user_id}") or 0
        invite_link = f"{GROUP_INVITE_BASE}?start={user_id}"
        await update.message.reply_text(
            f"{user.first_name}，你的专属邀请链接：{invite_link}\n已邀请 {invites} 人加入群！"
        )

    elif text == "下载":
        await update.message.reply_text("下载链接：暂未开放，敬请期待！")

    elif text == "使用说明":
        await update.message.reply_text(
            "机器人功能：\n- 签到：每天0点可签到，+20积分\n- 推广：分享邀请链接，统计邀请人数\n- 群限制：新用户需关注 @ROMADMA 后 /verify 解禁"
        )

    elif text == "购买":
        await update.message.reply_text("购买服务：暂未开放，敬请期待！")

async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member_update = update.chat_member
    if not chat_member_update:
        return

    new_member = chat_member_update.new_chat_member
    user_id = str(new_member.user.id)
    chat_id = str(update.effective_chat.id)

    if new_member.status in ["member", "administrator", "creator"]:
        # 新用户加入群
        if chat_id == redis_client.get("group_chat_id"):
            redis_client.set(f"restricted:{user_id}", chat_id)
            await context.bot.send_message(
                user_id,
                f"欢迎加入群！请先关注 {CHANNEL_ID}，然后回复 /verify 解锁发言权限！",
            )
            await context.bot.restrict_chat_member(
                chat_id, int(user_id), permissions={"can_send_messages": False}
            )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = redis_client.get(f"restricted:{user_id}")

    if not chat_id:
        await update.message.reply_text("你无需验证或已验证！")
        return

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, int(user_id))
        if member.status in ["member", "administrator", "creator"]:
            await context.bot.restrict_chat_member(
                chat_id, int(user_id), permissions={"can_send_messages": True}
            )
            redis_client.delete(f"restricted:{user_id}")
            await update.message.reply_text("已验证！你可以发言了！")
        else:
            await update.message.reply_text(f"请先关注 {CHANNEL_ID} 再验证！")
    except Exception as e:
        logger.error(f"验证错误：{e}")
        await update.message.reply_text("验证失败，请稍后再试！")

async def main():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(ChatMemberUpdatedFilter(), handle_chat_member)
    application.add_handler(CommandHandler("verify", verify))
    logger.info("机器人启动中...")
    return application

if __name__ == "__main__":
    import asyncio
    port = int(os.environ.get("PORT", 5000))
    application = asyncio.run(main())
    application.run_webhook(listen="0.0.0.0", port=port)