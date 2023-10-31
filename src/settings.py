import logging
from pathlib import Path
import asyncio

import pytz
import timezonefinder as timezonefinder
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from environs import Env
from starlette.templating import Jinja2Templates

from utils import File, TextApp, KeyboardApp

# Windows, there seems to be a problem with EventLoopPolicy.
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Definition of a root project
BASE_DIR = Path(__file__).resolve().parent.parent


"""----------LOGGING----------"""

# Configuring Logging
formater_logging_message = logging.Formatter("%(message)s")
file_log = logging.FileHandler(f"{BASE_DIR}/logs/logs.txt")
console_log = logging.StreamHandler()
file_log.setFormatter(formater_logging_message)
console_log.setFormatter(formater_logging_message)
logging.basicConfig(level=logging.INFO, handlers=(file_log, console_log))
"""
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
"""

"""----------ENV_PARS/GET_PATHS----------"""

env = Env()
env.read_env()

"""----------PARS_FILES----------"""

CLIENT_TEXT_PATH = env.str("CLIENT_TEXT_PATH")

KEYBOARD_PATH = env.str("KEYBOARD_PATH")

CONFIG_PATH = env.str("CONFIG_PATH")

# Opening configuration and resource files
try:
    # Resource files
    f_keyboard = File(f"{BASE_DIR}{KEYBOARD_PATH}")
    f_client_text = File(f"{BASE_DIR}{CLIENT_TEXT_PATH}")
    # Configuration file
    f_config = File(f"{BASE_DIR}{CONFIG_PATH}")
except Exception as e:
    # Error handling in file parsing attempt
    logging.error(f"settings.\n{str(e)}", exc_info=True)
    exit()


"""----------DATABASE----------"""

DB_USER = f_config.text["DATABASE"]["DB_USER"]
DB_PASS = f_config.text["DATABASE"]["DB_PASS"]
DB_HOST = f_config.text["DATABASE"]["DB_HOST"]
DB_PORT = f_config.text["DATABASE"]["DB_PORT"]
DB_NAME = f_config.text["DATABASE"]["DB_NAME"]

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

"""----------TASK SCHEDULER----------"""

DATABASE_JOB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

job_defaults = {
    'coalesce': False,
    'max_instances': 10
}
# Initializing the task manager
scheduler = AsyncIOScheduler(job_defaults=job_defaults)
# Defining a job repository
scheduler.add_jobstore('sqlalchemy', url=DATABASE_JOB_URL)

"""----------BOT----------"""

TOKEN_BOT = f_config.text["TELEGRAM"]["TOKEN"]

# Creating Storage object
storage = MemoryStorage()
# Creating Bot object
bot = Bot(token=TOKEN_BOT)
# Creating Dispatcher object
dp = Dispatcher(storage=storage)

"""----------WEB----------"""

WEBAPP_HOST = f_config.text["WEBAPP"]["HOST"]
WEBAPP_PORT = f_config.text["WEBAPP"]["PORT"]

WEBHOOK_HOST = f_config.text["WEBHOOK"]["HOST"]
WEBHOOK_PATH = f"{f_config.text['WEBHOOK']['PATH']}{TOKEN_BOT}"
WEBHOOK_URL = "{}{}".format(
    WEBHOOK_HOST,
    WEBHOOK_PATH
)

"""----------CONST----------"""

# Time of user inactivity
TIME_AFK = f_config.text["OTHER_CONST"]["TIME_AFK"]
TIME_AFK_SESSION = f_config.text["OTHER_CONST"]["TIME_AFK_SESSION"]

"""----------FORMATIONS_OF_ELEMENTS----------"""

try:
    # Forming client text
    client_text = TextApp(f_client_text)
    # Forming keyboards
    keyboard = KeyboardApp(f_keyboard, f_config)
except Exception as e:
    # Error. Formations of elements.
    logging.error(f"settings.\n{str(e)}", exc_info=True)
    exit()

"""----------TIME ZONE DETECTOR----------"""

# Initializing time zone finder
tzw = timezonefinder.TimezoneFinder()
locale_tz = pytz.timezone("Europe/Moscow")

"""----------CONST----------"""

# Time of user inactivity
TIME_AFK = f_config.text['OTHER_CONST']['TIME_AFK']
TIME_AFK_SESSION = f_config.text['OTHER_CONST']['TIME_AFK_SESSION']


# Number of tasks per session
COUNT_QUESTIONS = f_config.text['OTHER_CONST']['COUNT_QUESTIONS']

# Input validation
MAX_LEN_TEXT = f_config.text['OTHER_CONST']['MAX_LEN_TEXT']
MAX_LEN_INPUT = f_config.text['OTHER_CONST']['MAX_LEN_INPUT']

"""-------TEMPLATES-------"""
# Creating the application
templates = Jinja2Templates(directory=f"{BASE_DIR}/src/site/templates/")

"""----------AUTH----------"""

SECRET = env.str("SECRET")

