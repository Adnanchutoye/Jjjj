import asyncio
import importlib
import traceback
import os
from os.path import dirname
from sys import platform

import uvloop
from pyrogram import idle
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import feedparser
import logging

# Import from emelia.config
from emelia.config import mangodb, start_pic, help_pic
from Emilia import LOGGER, anibot, create_indexes, pgram, telethn, ORIGINAL_EVENT_LOOP, db, start_session
from Emilia.info import ALL_MODULES
from Emilia.tele.clone import clone_start_up

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HELP_MSG = "Click the button below to get help menu in your pm ~"
START_MSG = "**Hie Senpai ~ UwU** I am well and alive ;)"

# Rest of the imports and module loading logic remains the same
IMPORTED = {}
HELPAble = {}
SUB_MODE = {}
HIDDEN_MOD = {}
USER_INFO = []

cdir = dirname(__file__)
if platform == "linux" or platform == "linux2":
    path_dirSec = "/"
elif platform == "win32":
    path_dirSec = "\\"

for mode in ALL_MODULES:
    module = mode.replace(cdir, "").replace(path_dirSec, ".")
    imported_module = importlib.import_module("Emilia" + module)
    # ... rest of module import logic ...

# Episode checking function
async def check_episodes():
    """Check for new episodes and notify users."""
    rss_url = "https://www.livechart.me/feeds/episodes"
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            logging.warning("No episode data found in RSS feed.")
            return

        now = datetime.utcnow()
        one_day_ago = now - timedelta(days=1)

        users = db.users.find({"notifications": True})
        for user in users:
            user_id = user["user_id"]
            watchlist = [item["title"] for item in db.watchlist.find({"user_id": user_id, "type": "anime"})]
            if not watchlist:
                continue

            for entry in feed.entries:
                pub_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
                pub_date = pub_date.replace(tzinfo=None)
                if one_day_ago <= pub_date <= now:
                    title = entry.title
                    link = entry.link
                    if any(watch_title.lower() in title.lower() for watch_title in watchlist):
                        await pgram.send_message(
                            chat_id=user_id,
                            text=f"📅 New Episode Alert: {title}\nAired: {pub_date.strftime('%Y-%m-%d %H:%M UTC')}\n{link}"
                        )
    except Exception as e:
        logging.error(f"Error checking episodes: {e}")

async def start_anibot():
    await anibot.start()

async def start_pgram():
    uvloop.install()  # Comment out if using Windows
    await pgram.start()

    # Initialize scheduler for episode checks
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_episodes,
        "interval",
        days=1
    )
    scheduler.start()

    await idle()

async def gae():
    tasks = [start_anibot(), start_pgram()]
    await create_indexes()
    await start_session()
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        if ORIGINAL_EVENT_LOOP:  # Main Bot
            os.chdir("/app")  # Change to your directory
            asyncio.get_event_loop().run_until_complete(asyncio.gather(clone_start_up(), gae()))
        else:
            asyncio.get_event_loop().run_until_complete(gae())  # Clone Bot
        telethn.run_until_disconnected()
    except KeyboardInterrupt:
        pass
    except Exception:
        err = traceback.format_exc()
        LOGGER.error(err)
    finally:
        asyncio.get_event_loop().stop()
        LOGGER.error("Stopped Services.")



