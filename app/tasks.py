import logging
import asyncio
import aiocron

from app.bot import bot, dp, check_subscription
from app.db import get_all_subscribers, remove_subscriber

async def check_users_manual() -> int:
    """
    Ручная проверка подписчиков без объекта message.
    
    :return: Количество удалённых пользователей.
    """
    subscribers = await get_all_subscribers()
    removed_users = []
    if not subscribers:
        logging.info("Список подписчиков пуст.")
        return 0
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
                await bot.ban_chat_member(dp.chat_id, user_id)  # dp.chat_id не используется, оставьте логику из bot.py если нужно
                await bot.unban_chat_member(dp.chat_id, user_id)
            except Exception as e:
                logging.error("Ошибка удаления пользователя %d из группы: %s", user_id, e)
    logging.info("Автопроверка завершена. Удалено пользователей: %d", len(removed_users))
    return len(removed_users)

async def scheduled_check() -> None:
    """
    Функция для cron-задачи, запускается по расписанию.
    """
    removed_count = await check_users_manual()
    logging.info("Cron-задача: удалено пользователей: %d", removed_count)

def start_cron_tasks() -> None:
    """
    Регистрирует cron-задачу, которая выполняется каждые 4 часа.
    """
    # Расписание: каждые 4 часа
    aiocron.crontab("0 */4 * * *", func=scheduled_check)
    logging.info("Cron-задача scheduled_check зарегистрирована.")
