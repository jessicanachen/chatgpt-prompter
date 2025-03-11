from bot.discord_bot import bot
import os
from dotenv import load_dotenv

load_dotenv()
bot.run(os.getenv("DISCORD_TOKEN"))
