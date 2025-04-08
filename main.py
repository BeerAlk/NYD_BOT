import asyncio
import logging

from app.db import init_db, database
from app.bot import dp, delete_webhook, bot  # Импортируем объект bot
from app.tasks import start_cron_tasks
from app.web import run_web_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def main() -> None:
    # Инициализация базы данных и создание таблиц
    await init_db()

    # Удаляем webhook, если он установлен
    await delete_webhook()

    # Регистрируем cron-задачи
    start_cron_tasks()

    # Создаём задачи polling и web-сервера,
    # передаём объект bot явно в start_polling, чтобы диспетчер точно его увидел.
    polling_task = asyncio.create_task(dp.start_polling(bot))
    web_task = asyncio.create_task(run_web_app())

    # Ожидаем выполнение обоих задач (они работают бесконечно, пока не будет ошибка)
    await asyncio.gather(polling_task, web_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as err:
        logging.error("Основная ошибка: %s", err)
    finally:
        # Перед окончательным завершением пытаемся закрыть сессию бота и отключиться от базы
        try:
            asyncio.run(bot.session.close())
        except Exception as e:
            logging.warning("Ошибка при закрытии сессии бота: %s", e)
        try:
            asyncio.run(database.disconnect())
        except Exception as e:
            logging.warning("Ошибка при отключении от базы данных: %s", e)
