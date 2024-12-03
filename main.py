import asyncio
from bot import dp, bot
from handlers import register_handlers
from config import logger  

async def main():
    register_handlers(dp)
    logger.info("Bot started and is polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
