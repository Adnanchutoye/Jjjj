# commands.py
import requests
import feedparser
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from datetime import datetime, timedelta
from Emilia import anibot, custom_filter
from Emilia.utils.data_parser import get_wo, get_wols
from Emilia.utils.db import get_collection
from Emilia.utils.helper import check_user, control_user

class Commands:
    def __init__(self, app: Client, db):
        self.app = app
        self.db = db
        self.register_commands()

    def register_commands(self):
        """Register all bot commands and callbacks."""
        # Commands
        self.app.on_message(filters.command("start"))(self.start)
        self.app.on_message(filters.command("help"))(self.help_command)
        self.app.on_message(filters.command("recommend"))(self.recommend)
        self.app.on_message(filters.command("setgenres"))(self.set_genres)
        self.app.on_message(filters.command("search"))(self.search)
        self.app.on_message(filters.command("join"))(self.join)
        self.app.on_message(filters.command("news"))(self.news)
        self.app.on_message(filters.command("addtolist"))(self.add_to_list)
        self.app.on_message(filters.command("viewlist"))(self.view_list)
        self.app.on_message(filters.command("removefromlist"))(self.remove_from_list)
        self.app.on_message(filters.command("episodes"))(self.episodes)
        self.app.on_message(filters.command("notify"))(self.notify)
        self.app.on_message(filters.command("watch") & custom_filter.command(commands="watch"))(self.get_watch_order)
        # Callbacks
        self.app.on_callback_query(filters.regex(pattern=r"watch_(.*)"))(self.watch_callback)
        self.app.on_callback_query(filters.regex(pattern=r"wol_(.*)"))(self.wls_callback)

    @control_user
    async def start(self, client: Client, message: Message, mdata: dict = None):
        """Handle /start command."""
        user = message.from_user
        await self.db.add_user(user.id, user.username)
        await message.reply_text(
            f"Yo, {user.first_name}! Welcome to Anime Watchers Bot! 🎉\n"
            "Track anime and manga, get episode alerts, watch orders, and more!\n"
            "Use /help to see what I can do!"
        )

    async def help_command(self, client: Client, message: Message):
        """Handle /help command."""
        await message.reply_text(
            "Here’s what I can do for anime/manga fans:\n"
            "/recommend - Get anime recommendations\n"
            "/setgenres <genres> - Set favorite genres (e.g., action,shonen)\n"
            "/search <name> - Search for anime or manga\n"
            "/join - Join our community\n"
            "/news - Get latest anime news\n"
            "/addtolist <name> <anime|manga> - Add to watch/read list\n"
            "/viewlist [anime|manga] - View watch/read list\n"
            "/removefromlist <name> <anime|manga> - Remove from watch/read list\n"
            "/episodes [genre|watchlist] - See recent/upcoming episodes\n"
            "/notify <on|off> - Enable/disable episode notifications\n"
            "/watch <query> - Get anime watch order\n"
            "All suggestions are from legal sources like Crunchyroll!"
        )

    async def recommend(self, client: Client, message: Message):
        """Recommend anime based on user's favorite genres."""
        user_id = message.from_user.id
        user_data = await self.db.get_user(user_id)
        genre = message.command[1] if len(message.command) > 1 else (user_data["favorite_genres"] if user_data and user_data["favorite_genres"] else "action")

        query = '''
        query ($genre: String) {
            Page {
                media(genre_in: [$genre], sort: POPULARITY_DESC) {
                    title { romaji }
                    description
                    siteUrl
                }
            }
        }
        '''
        variables = {"genre": genre}
        url = "https://graphql.anilist.co"
        try:
            response = requests.post(url, json={"query": query, "variables": variables})
            data = response.json()
            anime = data["data"]["Page"]["media"][0]
            await message.reply_text(
                f"Recommended: {anime['title']['romaji']}\n"
                f"{anime['description'][:200]}...\n"
                f"More info: {anime['siteUrl']}"
            )
        except Exception:
            await message.reply_text("Oops, something went wrong! Try again later.")

    async def set_genres(self, client: Client, message: Message):
        """Set user's favorite genres."""
        user_id = message.from_user.id
        genres = ",".join(message.command[1:]).strip()
        if not genres:
            await message.reply_text("Please provide genres, e.g., /setgenres action,shonen")
            return
        await self.db.update_genres(user_id, genres)
        await message.reply_text(f"Your favorite genres are now: {genres}")

    async def search(self, client: Client, message: Message):
        """Search for an anime or manga by name."""
        query_text = " ".join(message.command[1:])
        if not query_text:
            await message.reply_text("Please provide a name, e.g., /search Naruto")
            return

        query = '''
        query ($search: String, $type: MediaType) {
            Media(search: $search, type: $type) {
                title { romaji }
                description
                siteUrl
            }
        }
        '''
        variables = {"search": query_text, "type": "ANIME"}
        url = "https://graphql.anilist.co"
        try:
            response = requests.post(url, json={"query": query, "variables": variables})
            data = response.json()
            media = data["data"]["Media"]
            if not media:
                variables["type"] = "MANGA"
                response = requests.post(url, json={"query": query, "variables": variables})
                data = response.json()
                media = data["data"]["Media"]
            if media:
                await message.reply_text(
                    f"Found: {media['title']['romaji']} ({variables['type'].lower()})\n"
                    f"{media['description'][:200]}...\n"
                    f"More info: {media['siteUrl']}"
                )
            else:
                await message.reply_text("Not found!")
        except Exception:
            await message.reply_text("Search failed. Try again!")

    async def join(self, client: Client, message: Message):
        """Provide link to anime community."""
        await message.reply_text("Join our anime community: t.me/AnimeWatchersGroup")

    async def news(self, client: Client, message: Message):
        """Fetch latest anime news from Anime News Network RSS."""
        rss_url = "https://www.animenewsnetwork.com/rss.xml"
        try:
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                await message.reply_text("No news found right now. Try again later!")
                return

            news = feed.entries[:3]
            response = "Latest Anime News:\n\n"
            for entry in news:
                response += f"📰 {entry.title}\n{entry.link}\n\n"
            await message.reply_text(response)
        except Exception:
            await message.reply_text("Failed to fetch news. Try again later!")

    async def add_to_list(self, client: Client, message: Message):
        """Add an anime or manga to the user's watchlist."""
        user_id = message.from_user.id
        args = message.command[1:]
        if len(args) < 2:
            await message.reply_text("Please provide a name and type, e.g., /addtolist Jujutsu Kaisen anime")
            return

        query_text = " ".join(args[:-1])
        media_type = args[-1].lower()
        if media_type not in ["anime", "manga"]:
            await message.reply_text("Type must be 'anime' or 'manga'!")
            return

        query = '''
        query ($search: String, $type: MediaType) {
            Media(search: $search, type: $type) {
                title { romaji }
                siteUrl
            }
        }
        '''
        variables = {"search": query_text, "type": media_type.upper()}
        url = "https://graphql.anilist.co"
        try:
            response = requests.post(url, json={"query": query, "variables": variables})
            data = response.json()
            media = data["data"]["Media"]
            if media:
                await self.db.add_to_watchlist(user_id, media["title"]["romaji"], media["siteUrl"], media_type)
                await message.reply_text(f"Added {media['title']['romaji']} ({media_type}) to your watch/read list!")
            else:
                await message.reply_text(f"{media_type.capitalize()} not found!")
        except Exception:
            await message.reply_text(f"Failed to add {media_type}. Try again!")

    async def view_list(self, client: Client, message: Message):
        """Show user's watchlist/read list."""
        user_id = message.from_user.id
        media_type = message.command[1].lower() if len(message.command) > 1 and message.command[1].lower() in ["anime", "manga"] else None
        watchlist = await self.db.get_watchlist(user_id, media_type)
        if not watchlist:
            await message.reply_text(f"Your {'watch/read' if not media_type else media_type} list is empty! Add with /addtolist <name> <anime|manga>")
            return

        response = f"Your {'Watch/Read' if not media_type else media_type.capitalize()} List:\n\n"
        for item in watchlist:
            response += f"📺 {item['title']} ({item['type']})\n{item['url']}\n\n"
        await message.reply_text(response)

    async def remove_from_list(self, client: Client, message: Message):
        """Remove an anime or manga from the user's watchlist."""
        user_id = message.from_user.id
        args = message.command[1:]
        if len(args) < 2:
            await message.reply_text("Please provide a name and type, e.g., /removefromlist Jujutsu Kaisen anime")
            return

        title = " ".join(args[:-1])
        media_type = args[-1].lower()
        if media_type not in ["anime", "manga"]:
            await message.reply_text("Type must be 'anime' or 'manga'!")
            return

        await self.db.remove_from_watchlist(user_id, title, media_type)
        await message.reply_text(f"Removed {title} ({media_type}) from your watch/read list!")

    async def episodes(self, client: Client, message: Message):
        """Fetch recent/upcoming episodes, filter by genre or watchlist."""
        user_id = message.from_user.id
        filter_type = message.command[1].lower() if len(message.command) > 1 else None
        notify = "notify" in message.command

        if filter_type not in ["genre", "watchlist", None]:
            await message.reply_text("Use /episodes [genre|watchlist] [notify], e.g., /episodes watchlist notify")
            return

        watchlist = [item["title"] for item in await self.db.get_watchlist(user_id, "anime")]
        user_data = await self.db.get_user(user_id)
        genres = user_data["favorite_genres"].split(",") if user_data and user_data["favorite_genres"] else []

        rss_url = "https://www.livechart.me/feeds/episodes"
        try:
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                await message.reply_text("No episode data found. Try again later!")
                return

            now = datetime.utcnow()
            one_week_ago = now - timedelta(days=7)
            episodes = []
            for entry in feed.entries[:5]:
                pub_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
                pub_date = pub_date.replace(tzinfo=None)
                if one_week_ago <= pub_date <= now or pub_date > now:
                    title = entry.title
                    link = entry.link
                    episodes.append((title, link, pub_date))

            if not episodes:
                await message.reply_text("No recent or upcoming episodes found!")
                return

            filtered_episodes = []
            if filter_type == "watchlist":
                filtered_episodes = [
                    (title, link, pub_date) for title, link, pub_date in episodes
                    if any(watch_title.lower() in title.lower() for watch_title in watchlist)
                ]
            elif filter_type == "genre" and genres:
                query = '''
                query ($search: String) {
                    Media(search: $search, type: ANIME) {
                        title { romaji }
                        genres
                    }
                }
                '''
                url = "https://graphql.anilist.co"
                for title, link, pub_date in episodes:
                    try:
                        variables = {"search": title.split("Episode")[0].strip()}
                        response = requests.post(url, json={"query": query, "variables": variables})
                        data = response.json()
                        anime = data["data"]["Media"]
                        if anime and any(genre.lower() in genres for genre in anime["genres"]):
                            filtered_episodes.append((title, link, pub_date))
                    except Exception:
                        continue
            else:
                filtered_episodes = episodes

            if not filtered_episodes:
                await message.reply_text(f"No episodes found for {'watchlist' if filter_type == 'watchlist' else 'selected genres'}!")
                return

            response = f"{'Filtered' if filter_type else 'Recent & Upcoming'} Episodes:\n\n"
            for title, link, pub_date in filtered_episodes:
                date_str = pub_date.strftime("%Y-%m-%d %H:%M UTC")
                response += f"📅 {title}\nAired/Airing: {date_str}\n{link}\n\n"

            await message.reply_text(response)

            if notify and filter_type == "watchlist":
                await self.db.set_notification(user_id, True)
                await message.reply_text("Notifications enabled for watchlist anime episodes!")
        except Exception:
            await message.reply_text("Failed to fetch episodes. Try again later!")

    async def notify(self, client: Client, message: Message):
        """Enable or disable episode notifications."""
        user_id = message.from_user.id
        if len(message.command) < 2 or message.command[1].lower() not in ["on", "off"]:
            await message.reply_text("Use /notify <on|off>, e.g., /notify on")
            return

        enabled = message.command[1].lower() == "on"
        await self.db.set_notification(user_id, enabled)
        await message.reply_text(f"Episode notifications {'enabled' if enabled else 'disabled'}!")

    @control_user
    async def get_watch_order(self, client: Client, message: Message, mdata: dict):
        """Get anime watch order."""
        gid = mdata["chat"]["id"]
        find_gc = await get_collection("DISABLED_CMDS").find_one({"_id": gid})
        if find_gc is not None and "watch" in find_gc["cmd_list"].split():
            return
        x = message.text.split(" ", 1)
        if len(x) == 1:
            await message.reply_text("Nothing given to search for!!!")
            return
        try:
            user = mdata["from_user"]["id"]
        except KeyError:
            user = mdata["sender_chat"]["id"]
        data = get_wols(x[1])
        msg = f"Found related animes for the query {x[1]}"
        buttons = []
        if data == []:
            await client.send_message(gid, "No results found!!!")
            return
        for i in data:
            buttons.append(
                [InlineKeyboardButton(str(i[1]), callback_data=f"watch_{i[0]}_{x[1]}_0_{user}")]
            )
        await client.send_message(gid, msg, reply_markup=InlineKeyboardMarkup(buttons))

    @check_user
    async def watch_callback(self, client: Client, cq: CallbackQuery, cdata: dict):
        """Handle watch order callback."""
        kek, id_, qry, req, user = cdata["data"].split("_")
        msg, total = get_wo(int(id_), int(req))
        totalpg, lol = divmod(total, 50)
        button = []
        if lol != 0:
            totalpg += 1
        if total > 50:
            if int(req) == 0:
                button.append(
                    [InlineKeyboardButton(text="Next", callback_data=f"{kek}_{id_}_{qry}_{int(req)+1}_{user}")]
                )
            elif int(req) == totalpg:
                button.append(
                    [InlineKeyboardButton(text="Prev", callback_data=f"{kek}_{id_}_{qry}_{int(req)-1}_{user}")]
                )
            else:
                button.append(
                    [
                        InlineKeyboardButton(text="Prev", callback_data=f"{kek}_{id_}_{qry}_{int(req)-1}_{user}"),
                        InlineKeyboardButton(text="Next", callback_data=f"{kek}_{id_}_{qry}_{int(req)+1}_{user}")
                    ]
                )
        button.append([InlineKeyboardButton("Back", callback_data=f"wol_{qry}_{user}")])
        await cq.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(button))

    async def wls_callback(self, client: Client, cq: CallbackQuery):
        """Handle watch order list callback."""
        kek, qry, user = cq.data.split("_")
        data = get_wols(qry)
        msg = f"Found related animes for the query {qry}"
        buttons = []
        for i in data:
            buttons.append(
                [InlineKeyboardButton(str(i[1]), callback_data=f"watch_{i[0]}_{qry}_0_{user}")]
            )
        await cq.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(buttons))
