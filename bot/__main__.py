import os
import shutil, psutil
import signal

from sys import executable
import time
from datetime import datetime
import pytz

from telegram.ext import CommandHandler
from bot import bot, dispatcher, updater, botStartTime
from bot import *
from bot.helper.ext_utils import fs_utils
from bot.helper.ext_utils import *
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.ext_utils.bot_utils import *
from .helper.telegram_helper.filters import CustomFilters
from telegram.error import BadRequest, Unauthorized
from .modules import authorize, list, cancel_mirror, mirror_status, mirror, clone, watch, delete, speedtest, count
from .modules import *

from pyrogram import idle
from bot import app

now = datetime.now(pytz.timezone(f'{TIMEZONE}'))

def stats(update, context):
    currentTime = get_readable_time(time() - botStartTime)
    current = now.strftime('%m/%d %I:%M:%S %p')
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>Bot Uptime ⌚:</b> {currentTime}\n' \
            f'<b>Started At :</b> {current}\n' \
            f'<b>Total disk space🗄️:</b> {total}\n' \
            f'<b>Used 🗃️:</b> {used}  ' \
            f'<b>Free 🗃️:</b> {free}\n\n' \
            f'📇Data Usage📇\n<b>Uploaded :</b> {sent}\n' \
            f'<b>Downloaded:</b> {recv}\n\n' \
            f'<b>CPU 🖥️:</b> {cpuUsage}% ' \
            f'<b>RAM ⛏️:</b> {memory}% ' \
            f'<b>Disk 🗄️:</b> {disk}%'
    sendMessage(stats, context.bot, update)


def start(update, context):
    LOGGER.info(
        f'UID: {update.message.chat.id} - UN: {update.message.chat.username} - MSG: {update.message.text}'
    )

    uptime = get_readable_time((time() - botStartTime))
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        if update.message.chat.type == "private" :
            reply_message = sendMessage(f"<b>🤗нєℓℓσ {update.message.chat.first_name}</b>,\n\nɯҽʅƈσɱҽ ƚσ ҽɱιʅყ ɱιɾɾσɾ Ⴆσƚ", context.bot, update)
            threading.Thread(target=auto_delete_message, args=(bot, update.message, reply_message)).start()
        else :
            sendMessage(f"<b>ɪ'ᴍ ᴀᴡᴀᴋᴇ ᴀʟʀᴇᴀᴅʏ!</b>\n<b>🇭‌🇦‌🇻‌🇪‌🇳‌'🇹‌ 🇸‌🇱‌🇪‌🇵‌🇹‌ 🇸‌🇮‌🇳‌🇨‌🇪‌:</b> <code>{uptime}</code>", context.bot, update)


def restart(update, context):
    restart_message = sendMessage("Restarting, Please wait!", context.bot, update)
    # Save restart message ID and chat ID in order to edit it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    fs_utils.clean_all()
    os.execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update)


def bot_help(update, context):
    help_string = f'''
/{BotCommands.HelpCommand}: To get this message

/{BotCommands.MirrorCommand} [download_url][magnet_link]: Start mirroring the link to google drive.\n

/{BotCommands.UnzipMirrorCommand} [download_url][magnet_link] : starts mirroring and if downloaded file is any archive , extracts it to google drive

/{BotCommands.CountCommand}: Count files/folders of G-Drive Links

/{BotCommands.TarMirrorCommand} [download_url][magnet_link]: start mirroring and upload the archived (.tar) version of the download

/{BotCommands.WatchCommand} [youtube-dl supported link]: Mirror through youtube-dl. Click /{BotCommands.WatchCommand} for more help.

/{BotCommands.TarWatchCommand} [youtube-dl supported link]: Mirror through youtube-dl and tar before uploading

/{BotCommands.CancelMirror} : Reply to the message by which the download was initiated and that download will be cancelled

/{BotCommands.StatusCommand}: Shows a status of all the downloads

/{BotCommands.ListCommand} [search term]: Searches the search term in the Google drive, if found replies with the link

/{BotCommands.StatsCommand}: Show Stats of the machine the bot is hosted on

/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Can only be invoked by owner of the bot)

/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports

/{BotCommands.SpeedCommand} : Check Internet Speed Of The Host

'''
    sendMessage(help_string, context.bot, update)
    
    
botcmds = [

    (f'{BotCommands.MirrorCommand}', 'Mirror using Aria2'),
    (f'{BotCommands.TarMirrorCommand}', 'Mirror and upload as tar'),
    (f'{BotCommands.UnzipMirrorCommand}', 'Mirror and extract files'),
    (f'{BotCommands.WatchCommand}', 'Mirror yt-dlp supported link'),
    (f'{BotCommands.TarWatchCommand}', 'Mirror yt-dlp supported link as tar'),
    (f'{BotCommands.CloneCommand}', 'Copy file/folder to Drive'),
    (f'{BotCommands.CountCommand}', 'Count file/folder of Drive'),
    (f'{BotCommands.deleteCommand}', 'Delete file/folder from Drive'),
    (f'{BotCommands.CancelMirror}', 'Cancel a task'),
    (f'{BotCommands.CancelAllCommand}', 'Cancel all downloading tasks'),
    (f'{BotCommands.ListCommand}', 'Search in Drive'),
    (f'{BotCommands.StatusCommand}', 'Get mirror status message'),
    (f'{BotCommands.StatsCommand}', 'Bot usage stats'),
    (f'{BotCommands.RestartCommand}', 'Restart the bot'),
    (f'{BotCommands.LogCommand}', 'Get the bot Log'),
    (f'{BotCommands.HelpCommand}', 'Get detailed help')
]    


def main():
    # Heroku restarted (Group Message)
    GROUP_ID = f'{RESTARTED_GROUP_ID}'
    kie = datetime.now(pytz.timezone(f'{TIMEZONE}'))
    jam = kie.strftime('\n 𝗗𝗮𝘁𝗲 : %d/%m/%Y\n 𝗧𝗶𝗺𝗲: %I:%M%P')
    if GROUP_ID is not None and isinstance(GROUP_ID, str):        
        try:
            dispatcher.bot.sendMessage(f"{GROUP_ID}", f" 𝐁𝐎𝐓 𝐆𝐎𝐓 𝐑𝐄𝐒𝐓𝐀𝐑𝐓𝐄𝐃 \n{jam}\n\n 𝗧𝗶𝗺𝗲 𝗭𝗼𝗻𝗲 : {TIMEZONE}\n\nρℓєαѕє ѕтαят уσυя ∂σωиℓσα∂ѕ αgαιи!\n\n#Restarted")
        except Unauthorized:
            LOGGER.warning(
                "Bot is not able to send Restart Message to Group !"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)
            
            
            
    fs_utils.start_cleanup()
    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("Restarted successfully!", chat_id, msg_id)
        os.remove(".restartmsg")
        
    bot.set_my_commands(botcmds)
    start_handler = CommandHandler(BotCommands.StartCommand, start,
                                   filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter| CustomFilters.authorized_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling()
    LOGGER.info("⚠️ If Any optional vars are not filled The Bot will use Defaults values")
    LOGGER.info("📶 Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)

app.start()
main()
idle()
