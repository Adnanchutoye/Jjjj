import json
import os


def get_user_list(config, key):
    with open("{}/Emilia/{}".format(os.getcwd(), config), "r") as json_file:
        return json.load(json_file)[key]


class Config(object):
    API_HASH = "4e81464b29d79c58d0ad8a0c55ece4a5" # API_HASH from my.telegram.org
    API_ID = 20718334 # API_ID from my.telegram.org

    BOT_ID = 7403693425 # BOT_ID
    BOT_USERNAME = "animevortex_bot" # BOT_USERNAME

    MONGO_DB_URL = "mongodb+srv://spxsolo:umaid2008@cluster0.7fbux.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" # MongoDB URL from MongoDB Atlas

    SUPPORT_CHAT = "ahss_help_zone" # Support Chat Username
    UPDATE_CHANNEL = "anime_beyond" # Update Channel Username
    DEV_USERS = [5585016974] # Dev Users
    TOKEN = "7403693425:AAHaGlkp-zNNPvNeO62xWqwmsRI5apY0Dcs" # Bot Token from @BotFather

    EVENT_LOGS = -1002078429106 # Event Logs Chat ID
    OWNER_ID = 5585016974 # Owner ID
 
    TEMP_DOWNLOAD_DIRECTORY = "./" # Temporary Download Directory
    BOT_NAME = "mithi" # Bot Name
    WALL_API = "6950f53" # Wall API from wall.alphacoders.com
    ORIGINAL_EVENT_LOOP = True # Do not Change
    HELP_IMG = "https://graph.org/file/29a3acbbab9de5f45a5fe.jpg" # help pic url
    START_IMG = "https://graph.org/file/29a3acbbab9de5f45a5fe.jpg" # start pic url


class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
