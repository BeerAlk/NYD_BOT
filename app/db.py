import logging
from typing import List, Optional

import databases
from app.config import MYSQL_URL

# Инициализация подключения к базе данных MySQL
database = databases.Database(MYSQL_URL)

# SQL-запросы для работы с подписчиками
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS subscribers (
    user_id BIGINT PRIMARY KEY
);
"""

INSERT_SUBSCRIBER = "INSERT IGNORE INTO subscribers (user_id) VALUES (:user_id);"
SELECT_ALL_SUBSCRIBERS = "SELECT user_id FROM subscribers;"
DELETE_SUBSCRIBER = "DELETE FROM subscribers WHERE user_id = :user_id;"

async def init_db() -> None:
    """
    Инициализировать базу данных (создать таблицы, если необходимо).
    """
    await database.connect()
    await database.execute(query=CREATE_TABLE)
    logging.info("База данных и таблица subscribers инициализированы.")

async def add_subscriber(user_id: int) -> None:
    """
    Добавить подписчика в базу данных.
    
    :param user_id: ID пользователя.
    """
    await database.execute(query=INSERT_SUBSCRIBER, values={"user_id": user_id})
    logging.info(f"Пользователь {user_id} добавлен в БД.")

async def get_all_subscribers() -> List[int]:
    """
    Получить список всех подписчиков.
    
    :return: Список user_id.
    """
    rows = await database.fetch_all(query=SELECT_ALL_SUBSCRIBERS)
    return [row["user_id"] for row in rows]

async def remove_subscriber(user_id: int) -> None:
    """
    Удалить подписчика из базы данных.
    
    :param user_id: ID пользователя.
    """
    await database.execute(query=DELETE_SUBSCRIBER, values={"user_id": user_id})
    logging.info(f"Пользователь {user_id} удалён из БД.")
