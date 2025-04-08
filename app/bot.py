import logging
import asyncio
from typing import Any

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import API_TOKEN, MAIN_CHANNEL_ID, MAIN_CHANNEL_USERNAME, CLOSED_GROUP_CHAT, CLOSED_CHANNEL_LINK, ADMIN_ID, ADMIN_USERNAME
from app.db import add_subscriber, get_all_subscribers, remove_subscriber

# Инициализация бота, диспетчера и памяти для FSM
bot: Bot = Bot(token=API_TOKEN)
storage: MemoryStorage = MemoryStorage()
dp: Dispatcher = Dispatcher(bot=bot, storage=storage)

# Глобальный словарь для отслеживания обработанных media_group_id
processed_media_groups: dict[str, bool] = {}

async def delete_webhook():
    result = await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook удалён:", result)
    return result

async def check_subscription(user_id: int) -> bool:
    """
    Проверяет, подписан ли пользователь на основной канал.
    
    :param user_id: ID пользователя.
    :return: True, если подписан, иначе False.
    """
    try:
        member = await bot.get_chat_member(MAIN_CHANNEL_ID, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            return False
        # Дополнительная проверка активности пользователя (опционально)
        return True
    except Exception as e:
        logging.error(f"Ошибка проверки подписки для {user_id}: {e}")
        return False

def is_admin(message: types.Message) -> bool:
    """
    Проверяет, является ли отправитель администратором.
    
    :param message: Сообщение пользователя.
    :return: True, если админ.
    """
    return message.from_user.id == ADMIN_ID

# Обработчик заявок на вступление в группу
@dp.chat_join_request(F.chat.id == CLOSED_GROUP_CHAT)
async def handle_join_request(request: ChatJoinRequest) -> None:
    user_id: int = request.from_user.id
    username: str = request.from_user.username or "Без имени"
    if await check_subscription(user_id):
        await bot.approve_chat_join_request(CLOSED_GROUP_CHAT, user_id)
        logging.info("✅ Заявка одобрена: %s (%d)", username, user_id)
        await add_subscriber(user_id)
    else:
        await bot.decline_chat_join_request(CLOSED_GROUP_CHAT, user_id)
        logging.info("❌ Заявка отклонена: %s (%d)", username, user_id)

# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")],
        [InlineKeyboardButton(text="Написать администратору", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
    await message.answer(
        f"Привет! Я бот канала Not Yet Design!\n\n"
        f"Подпишитесь на основной канал: https://t.me/{MAIN_CHANNEL_USERNAME},\n"
        f"а затем нажмите \"Проверить подписку\".",
        reply_markup=keyboard
    )

# Обработчик callback для проверки подписки
@dp.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback_query: types.CallbackQuery) -> None:
    user_id: int = callback_query.from_user.id
    logging.info("Получен callback от пользователя %d", user_id)
    if await check_subscription(user_id):
        await add_subscriber(user_id)
        await callback_query.answer("Проверка пройдена!")
        await callback_query.message.answer(
            "Спасибо за подписку! 🎉 Теперь вы можете присоединиться к закрытому каналу: " + CLOSED_CHANNEL_LINK
        )
    else:
        await callback_query.answer("Вы ещё не подписаны на основной канал.", show_alert=True)

# Обработчик команды /post для рассылки постов
@dp.message(Command("post"))
async def post_command(message: types.Message) -> None:
    if not is_admin(message):
        await message.reply("Команда доступна только администратору.")
        return
    try:
        sent_message = None
        if message.photo:
            sent_message = await bot.send_photo(
                MAIN_CHANNEL_ID,
                message.photo[-1].file_id,
                caption=message.caption
            )
        elif message.video:
            sent_message = await bot.send_video(
                MAIN_CHANNEL_ID,
                message.video.file_id,
                caption=message.caption
            )
        else:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply("Укажите текст поста или прикрепите фото/видео.")
                return
            text = args[1]
            sent_message = await bot.send_message(MAIN_CHANNEL_ID, text)
        if sent_message:
            post_url = f"https://t.me/{MAIN_CHANNEL_USERNAME}/{sent_message.message_id}"
            subscribers = await get_all_subscribers()
            for user_id in subscribers:
                try:
                    await bot.send_message(user_id, f"Новый пост на канале: {post_url}")
                except Exception as e:
                    logging.error("Ошибка отправки сообщения пользователю %d: %s", user_id, e)
                    await remove_subscriber(user_id)
            await message.reply("Пост опубликован и отправлен подписчикам!")
    except Exception as e:
        logging.error("Ошибка при публикации поста: %s", e)

# Обработчик новых постов в канале
@dp.channel_post()
async def channel_post_handler(message: types.Message) -> None:
    if message.media_group_id:
        if processed_media_groups.get(message.media_group_id):
            logging.info("Media group %s уже обработан, пропускаем сообщение %d", message.media_group_id, message.message_id)
            return
        processed_media_groups[message.media_group_id] = True

    try:
        post_url = f"https://t.me/{MAIN_CHANNEL_USERNAME}/{message.message_id}"
        logging.info("Новый пост: %s", post_url)
        subscribers = await get_all_subscribers()
        for user_id in subscribers:
            try:
                await bot.send_message(user_id, f"Новый пост на канале: {post_url}")
            except Exception as e:
                logging.error("Ошибка отправки сообщения пользователю %d: %s", user_id, e)
                await remove_subscriber(user_id)
    except Exception as e:
        logging.error("Ошибка обработки поста из канала: %s", e)

# Команда /check_users – ручная проверка подписчиков
@dp.message(Command("check_users"))
async def check_users_command(message: types.Message) -> None:
    if not is_admin(message):
        await message.reply("Команда доступна только администратору.")
        return
    subscribers = await get_all_subscribers()
    removed_users = []
    if not subscribers:
        await message.reply("Список подписчиков пуст. Никого не нужно проверять.")
        return
    for user_id in subscribers:
        is_subscribed = await check_subscription(user_id)
        try:
            await bot.send_chat_action(user_id, "typing")
            is_active = True
        except Exception as e:
            is_active = False
            logging.warning("Пользователь %d не активен: %s", user_id, e)
        if not is_subscribed or not is_active:
            await remove_subscriber(user_id)
            removed_users.append(user_id)
            try:
                await bot.ban_chat_member(CLOSED_GROUP_CHAT, user_id)
                await bot.unban_chat_member(CLOSED_GROUP_CHAT, user_id)
                logging.info("Пользователь %d удалён из группы.", user_id)
            except Exception as e:
                logging.error("Ошибка удаления пользователя %d из группы: %s", user_id, e)
    await message.reply(f"Проверка завершена. Удалено пользователей: {len(removed_users)}")

# Команда /list_users – вывод списка подписчиков
@dp.message(Command("list_users"))
async def list_users_command(message: types.Message) -> None:
    if not is_admin(message):
        await message.reply("Команда доступна только администратору.")
        return
    subscribers = await get_all_subscribers()
    if subscribers:
        await message.reply("Подписчики:\n" + "\n".join(str(uid) for uid in subscribers))
    else:
        await message.reply("Список подписчиков пуст.")
