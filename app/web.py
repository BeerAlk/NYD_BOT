import logging
from aiohttp import web

from app.config import WEB_HOST, WEB_PORT

async def health(request: web.Request) -> web.Response:
    """
    Простая health-check функция для проверки работы сервера.
    """
    return web.Response(text="OK")

def create_app() -> web.Application:
    """
    Создаёт и настраивает web-приложение.
    
    :return: Объект web.Application.
    """
    app = web.Application()
    app.add_routes([web.get("/", health)])
    return app

async def run_web_app() -> None:
    """
    Запускает web-сервер.
    """
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEB_HOST, WEB_PORT)
    await site.start()
    logging.info("Web-сервер запущен на %s:%d", WEB_HOST, WEB_PORT)
