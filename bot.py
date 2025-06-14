from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ChatMemberHandler,
)
from telegram import Update
import os
import redis

# Redis 连接（用于积分系统）
redis_url = os.environ.get("REDIS_URL")
r = redis.from_url(redis_url) if redis_url else None

# 频道 ID
CHANNEL_ID = "@ROMADMA2"

# 启动命令
async def start(update: Update, context):
    keyboard = [["[签到]", "[下载]"], ["[使用说明]", "[推广]"], ["[购买]"]]
    reply_markup = {"keyboard": keyboard, "resize_keyboard": True}
    await update.message.reply_text("欢迎使用！请选择：", reply_markup=reply_markup)

# 签到功能
async def sign(update: Update, context):
    user_id = update.message.from_user.id
    if r and r.get(f"signed_{user_id}") is None:
        r.setex(f"signed_{user_id}", 86400, "1")  # 24小时有效
        await update.message.reply_text("+20 积分，今天签到人数：1")
    else:
        await update.message.reply_text("今天已签到！")

# 下载功能
async def download(update: Update, context):
    await update.message.reply_text("下载功能待开发，请稍后！")

# 使用说明
async def usage(update: Update, context):
    await update.message.reply_text("使用说明：/start 开始，[签到] 每日+20积分，[推广] 获取邀请链接，[购买] 联系管理员。")

# 推广功能
async def promote(update: Update, context):
    user_id = update.message.from_user.id
    invite_link = f"https://t.me/ceshi1087?start={user_id}"
    await update.message.reply_text(f"推广链接：{invite_link}，邀请好友得积分！")

# 购买功能
async def buy(update: Update, context):
    await update.message.reply_text("购买请点击：https://mall.lcfaka.com.cn/shop/H49PS9FX 或联系 @ROMADMA 管理员！")

# 验证并解禁
async def verify(update: Update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    member_status = await context.bot.get_chat_member(CHANNEL_ID, user_id)
    if member_status.status in ["member", "creator", "administrator"]:
        await context.bot.restrict_chat_member(chat_id, user_id, can_send_messages=True)
        await update.message.reply_text("已验证并解禁，请自由发言！")
    else:
        await update.message.reply_text("请先关注 @ROMADMA2 频道，然后再回复 /verify")

# 新成员进群禁言
async def handle_new_member(update: Update, context):
    for member in update.message.new_chat_members:
        user_id = member.id
        chat_id = update.message.chat_id
        await context.bot.restrict_chat_member(chat_id, user_id, can_send_messages=False)
        await context.bot.send_message(chat_id, f"欢迎 {member.username}！请关注 @ROMADMA2 并私聊我回复 /verify 解禁发言")

# 主函数
def main():
    application = (
        Application.builder()
        .token(os.environ["BOT_TOKEN"])
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verify", verify))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: update.message.reply_text("未知命令，请用 /start 查看菜单！")))

    render_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if not render_url:
        raise ValueError("RENDER_EXTERNAL_HOSTNAME 未设置，请检查 Render 环境变量")
    webhook_url = f"https://{render_url}"

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    main()
