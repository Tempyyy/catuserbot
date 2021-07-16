import random
import re
from datetime import datetime

from telethon import Button, functions
from telethon.events import CallbackQuery
from telethon.utils import get_display_name

from userbot import catub
from userbot.core.logger import logging

from ..Config import Config
from ..core.managers import edit_delete, edit_or_reply
from ..helpers.utils import _format, get_user_from_event, reply_id
from ..sql_helper import global_collectionjson as sql
from ..sql_helper import global_list as sqllist
from ..sql_helper import pmpermit_sql
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from . import mention

plugin_category = "utils"
LOGS = logging.getLogger(__name__)
cmdhd = Config.COMMAND_HAND_LER


async def do_pm_permit_action(event, chat):  # sourcery no-metrics
    reply_to_id = await reply_id(event)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    me = await event.client.get_me()
    mention = f"[{chat.first_name}](tg://user?id={chat.id})"
    my_mention = f"[{me.first_name}](tg://user?id={me.id})"
    first = chat.first_name
    last = chat.last_name
    fullname = f"{first} {last}" if last else first
    username = f"@{chat.username}" if chat.username else mention
    userid = chat.id
    my_first = me.first_name
    my_last = me.last_name
    my_fullname = f"{my_first} {my_last}" if my_last else my_first
    my_username = f"@{me.username}" if me.username else my_mention
    if str(chat.id) not in PM_WARNS:
        PM_WARNS[str(chat.id)] = 0
    try:
        MAX_FLOOD_IN_PMS = int(gvarstatus("MAX_FLOOD_IN_PMS") or 6)
    except (ValueError, TypeError):
        MAX_FLOOD_IN_PMS = 6
    totalwarns = MAX_FLOOD_IN_PMS + 1
    warns = PM_WARNS[str(chat.id)] + 1
    remwarns = totalwarns - warns
    if PM_WARNS[str(chat.id)] >= MAX_FLOOD_IN_PMS:
        try:
            if str(chat.id) in PMMESSAGE_CACHE:
                await event.client.delete_messages(
                    chat.id, PMMESSAGE_CACHE[str(chat.id)]
                )
                del PMMESSAGE_CACHE[str(chat.id)]
        except Exception as e:
            LOGS.info(str(e))
        custompmblock = gvarstatus("pmblock") or None
        if custompmblock is not None:
            USER_BOT_WARN_ZERO = custompmblock.format(
                mention=mention,
                first=first,
                last=last,
                fullname=fullname,
                username=username,
                userid=userid,
                my_first=my_first,
                my_last=my_last,
                my_fullname=my_fullname,
                my_username=my_username,
                my_mention=my_mention,
                totalwarns=totalwarns,
                warns=warns,
                remwarns=remwarns,
            )
        else:
            USER_BOT_WARN_ZERO = f"**You were spamming my master** {my_mention}**'s inbox, henceforth you have been blocked.**"
        msg = await event.reply(USER_BOT_WARN_ZERO)
        await event.client(functions.contacts.BlockRequest(chat.id))
        the_message = f"#BLOCKED_PM\
                            \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                            \n**Message Count:** {PM_WARNS[str(chat.id)]}"
        del PM_WARNS[str(chat.id)]
        sql.del_collection("pmwarns")
        sql.del_collection("pmmessagecache")
        sql.add_collection("pmwarns", PM_WARNS, {})
        sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
        try:
            return await event.client.send_message(
                BOTLOG_CHATID,
                the_message,
            )
        except BaseException:
            return
    custompmpermit = gvarstatus("pmpermit_txt") or None
    if custompmpermit is not None:
        USER_BOT_NO_WARN = custompmpermit.format(
            mention=mention,
            first=first,
            last=last,
            fullname=fullname,
            username=username,
            userid=userid,
            my_first=my_first,
            my_last=my_last,
            my_fullname=my_fullname,
            my_username=my_username,
            my_mention=my_mention,
            totalwarns=totalwarns,
            warns=warns,
            remwarns=remwarns,
        )
    elif gvarstatus("pmmenu") is None:
        USER_BOT_NO_WARN = f"""__Hi__ {mention}__, I haven't approved you yet to personal message me. 

You have {warns}/{totalwarns} warns until you get blocked by the CatUserbot.

Choose an option from below to specify the reason of your message and wait for me to check it. __⬇️"""
    else:
        USER_BOT_NO_WARN = f"""__Hi__ {mention}__, I haven't approved you yet to personal message me.

You have {warns}/{totalwarns} warns until you get blocked by the CatUserbot.

Don't spam my inbox. say reason and wait until my response.__"""
    addgvar("pmpermit_text", USER_BOT_NO_WARN)
    PM_WARNS[str(chat.id)] += 1
    try:
        if gvarstatus("pmmenu") is None:
            results = await event.client.inline_query(
                Config.TG_BOT_USERNAME, "pmpermit"
            )
            msg = await results[0].click(chat.id, reply_to=reply_to_id, hide_via=True)
        else:
            PM_PIC = gvarstatus("pmpermit_pic")
            if PM_PIC:
                CAT = [x for x in PM_PIC.split()]
                PIC = list(CAT)
                CAT_IMG = random.choice(PIC)
            else:
                CAT_IMG = None
            if CAT_IMG is not None:
                msg = await event.client.send_file(
                    chat.id,
                    CAT_IMG,
                    caption=USER_BOT_NO_WARN,
                    reply_to=reply_to_id,
                    force_document=False,
                )
            else:
                msg = await event.client.send_message(
                    chat.id, USER_BOT_NO_WARN, reply_to=reply_to_id
                )
    except Exception as e:
        LOGS.error(e)
        msg = await event.reply(USER_BOT_NO_WARN)
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    PMMESSAGE_CACHE[str(chat.id)] = msg.id
    sql.del_collection("pmwarns")
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmwarns", PM_WARNS, {})
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})


async def do_pm_options_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = "⛔️ 𝗦𝗰𝗲𝗴𝗹𝗶 un messaggio o verrai 𝗕𝗹𝗼𝗰𝗰𝗮𝘁𝗼 𝗔𝘂𝘁𝗼𝗺𝗮𝘁𝗶𝗰𝗮𝗺𝗲𝗻𝘁𝗲 ⛔️"
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = f"ㅤㅤㅤ  ㅤㅤㅤ🚫 𝗕𝗟𝗢𝗖𝗖𝗔𝗧𝗢 🚫 \
Sei stato 𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 𝗮𝘂𝘁𝗼𝗺𝗮𝘁𝗶𝗰𝗮𝗺𝗲𝗻𝘁𝗲, appena verrai 𝗻𝗼𝘁𝗮𝘁𝗼,  \
se verrà ritenuto 𝙣𝙚𝙘𝙚𝙨𝙨𝙖𝙧𝙞𝙤, verrai 𝘀𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 e 𝗰𝗼𝗻𝘁𝗮𝘁𝘁𝗮𝘁𝗼, nel frattempo potresti finire di 𝗯𝗲𝗿𝗲 il tuo 𝘀𝘂𝗰𝗰𝗼, va bene? 🧃"
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                            \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                            \n**Reason:** __He/She didn't opt for any provided options and kept on messaging.__"
    sqllist.rm_from_list("pmoptions", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_enquire_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = """🧘🏻‍♂️ 𝗦𝗶𝗶 𝗣𝗮𝘇𝗶𝗲𝗻𝘁𝗲, di solito 𝗿𝗶𝘀𝗽𝗼𝗻𝗱𝗼 entro 𝟭 𝗼𝗿𝗮, se è passato più tempo, beh 𝙥𝙧𝙤𝙗𝙖𝙗𝙞𝙡𝙢𝙚𝙣𝙩𝙚 è \
qualcosa di 𝗶𝗺𝗽𝗼𝗿𝘁𝗮𝗻𝘁𝗲, non preoccuparti, ti risponderò il 𝙥𝙧𝙞𝙢𝙖 𝙥𝙤𝙨𝙨𝙞𝙗𝙞𝙡𝙚.\n\n⛔️ **Non spammare inutilmente o verrai Bloccato Automaticamente.** ⛔️"""
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = f"ㅤㅤㅤ  ㅤㅤㅤ🚫 𝗕𝗟𝗢𝗖𝗖𝗔𝗧𝗢 🚫 \
Sei stato 𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 𝗮𝘂𝘁𝗼𝗺𝗮𝘁𝗶𝗰𝗮𝗺𝗲𝗻𝘁𝗲, appena verrai 𝗻𝗼𝘁𝗮𝘁𝗼,  \
se verrà ritenuto 𝙣𝙚𝙘𝙚𝙨𝙨𝙖𝙧𝙞𝙤, verrai 𝘀𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 e 𝗰𝗼𝗻𝘁𝗮𝘁𝘁𝗮𝘁𝗼, nel frattempo potresti finire di 𝗯𝗲𝗿𝗲 il tuo 𝘀𝘂𝗰𝗰𝗼, va bene? 🧃"
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                \n**Reason:** __He/She opted for enquire option but didn't wait after being told also and kept on messaging so blocked.__"
    sqllist.rm_from_list("pmenquire", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_request_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = """🧘🏻‍♂️ 𝗦𝗶𝗶 𝗣𝗮𝘇𝗶𝗲𝗻𝘁𝗲, di solito 𝗿𝗶𝘀𝗽𝗼𝗻𝗱𝗼 entro 𝟭 𝗼𝗿𝗮, se è passato più tempo, beh 𝙥𝙧𝙤𝙗𝙖𝙗𝙞𝙡𝙢𝙚𝙣𝙩𝙚 è \
qualcosa di 𝗶𝗺𝗽𝗼𝗿𝘁𝗮𝗻𝘁𝗲, non preoccuparti, ti risponderò il 𝙥𝙧𝙞𝙢𝙖 𝙥𝙤𝙨𝙨𝙞𝙗𝙞𝙡𝙚.\n\n⛔️ **Non spammare inutilmente o verrai Bloccato Automaticamente.** ⛔️"""
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = f"ㅤㅤㅤ  ㅤㅤㅤ🚫 𝗕𝗟𝗢𝗖𝗖𝗔𝗧𝗢 🚫 \
Sei stato 𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 𝗮𝘂𝘁𝗼𝗺𝗮𝘁𝗶𝗰𝗮𝗺𝗲𝗻𝘁𝗲, appena verrai 𝗻𝗼𝘁𝗮𝘁𝗼,  \
se verrà ritenuto 𝙣𝙚𝙘𝙚𝙨𝙨𝙖𝙧𝙞𝙤, verrai 𝘀𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 e 𝗰𝗼𝗻𝘁𝗮𝘁𝘁𝗮𝘁𝗼, nel frattempo potresti finire di 𝗯𝗲𝗿𝗲 il tuo 𝘀𝘂𝗰𝗰𝗼, va bene? 🧃"
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                \n**Reason:** __He/She opted for the request option but didn't wait after being told also so blocked.__"
    sqllist.rm_from_list("pmrequest", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_chat_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = """🧘🏻‍♂️ 𝗦𝗶𝗶 𝗣𝗮𝘇𝗶𝗲𝗻𝘁𝗲, di solito 𝗿𝗶𝘀𝗽𝗼𝗻𝗱𝗼 entro 𝟭 𝗼𝗿𝗮, se è passato più tempo, beh 𝙥𝙧𝙤𝙗𝙖𝙗𝙞𝙡𝙢𝙚𝙣𝙩𝙚 è \
qualcosa di 𝗶𝗺𝗽𝗼𝗿𝘁𝗮𝗻𝘁𝗲, non preoccuparti, ti risponderò il 𝙥𝙧𝙞𝙢𝙖 𝙥𝙤𝙨𝙨𝙞𝙗𝙞𝙡𝙚.\n\n⛔️ **Non spammare inutilmente o verrai Bloccato Automaticamente.** ⛔️"""
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = f"ㅤㅤㅤ  ㅤㅤㅤ🚫 𝗕𝗟𝗢𝗖𝗖𝗔𝗧𝗢 🚫 \
Sei stato 𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 𝗮𝘂𝘁𝗼𝗺𝗮𝘁𝗶𝗰𝗮𝗺𝗲𝗻𝘁𝗲, appena verrai 𝗻𝗼𝘁𝗮𝘁𝗼,  \
se verrà ritenuto 𝙣𝙚𝙘𝙚𝙨𝙨𝙖𝙧𝙞𝙤, verrai 𝘀𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 e 𝗰𝗼𝗻𝘁𝗮𝘁𝘁𝗮𝘁𝗼, nel frattempo potresti finire di 𝗯𝗲𝗿𝗲 il tuo 𝘀𝘂𝗰𝗰𝗼, va bene? 🧃"
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                \n**Reason:** __He/She select opted for the chat option but didn't wait after being told also so blocked.__"
    sqllist.rm_from_list("pmchat", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_spam_action(event, chat):
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    USER_BOT_WARN_ZERO = f"ㅤㅤㅤ  ㅤㅤㅤ🚫 𝗕𝗟𝗢𝗖𝗖𝗔𝗧𝗢 🚫 \
Sei stato 𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 𝗮𝘂𝘁𝗼𝗺𝗮𝘁𝗶𝗰𝗮𝗺𝗲𝗻𝘁𝗲, appena verrai 𝗻𝗼𝘁𝗮𝘁𝗼,  \
se verrà ritenuto 𝙣𝙚𝙘𝙚𝙨𝙨𝙖𝙧𝙞𝙤, verrai 𝘀𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 e 𝗰𝗼𝗻𝘁𝗮𝘁𝘁𝗮𝘁𝗼, nel frattempo potresti finire di 𝗯𝗲𝗿𝗲 il tuo 𝘀𝘂𝗰𝗰𝗼, va bene? 🧃"
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                            \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                            \n**Reason:** he opted for spam option and messaged again."
    sqllist.rm_from_list("pmspam", chat.id)
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


@catub.cat_cmd(incoming=True, func=lambda e: e.is_private, edited=False, forword=None)
async def on_new_private_message(event):
    if gvarstatus("pmpermit") is None:
        return
    chat = await event.get_chat()
    if chat.bot or chat.verified:
        return
    if pmpermit_sql.is_approved(chat.id):
        return
    if str(chat.id) in sqllist.get_collection_list("pmspam"):
        return await do_pm_spam_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmchat"):
        return await do_pm_chat_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmrequest"):
        return await do_pm_request_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmenquire"):
        return await do_pm_enquire_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmoptions"):
        return await do_pm_options_action(event, chat)
    await do_pm_permit_action(event, chat)


@catub.cat_cmd(outgoing=True, func=lambda e: e.is_private, edited=False, forword=None)
async def you_dm_other(event):
    if gvarstatus("pmpermit") is None:
        return
    chat = await event.get_chat()
    if chat.bot or chat.verified:
        return
    if str(chat.id) in sqllist.get_collection_list("pmspam"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmchat"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmrequest"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmenquire"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmoptions"):
        return
    if event.text and event.text.startswith(
        (
            f"{cmdhd}block",
            f"{cmdhd}disapprove",
            f"{cmdhd}a",
            f"{cmdhd}da",
            f"{cmdhd}approve",
        )
    ):
        return
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    start_date = str(datetime.now().strftime("%B %d, %Y"))
    if not pmpermit_sql.is_approved(chat.id) and str(chat.id) not in PM_WARNS:
        pmpermit_sql.approve(
            chat.id, get_display_name(chat), start_date, chat.username, "For Outgoing"
        )
        try:
            PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
        except AttributeError:
            PMMESSAGE_CACHE = {}
        if str(chat.id) in PMMESSAGE_CACHE:
            try:
                await event.client.delete_messages(
                    chat.id, PMMESSAGE_CACHE[str(chat.id)]
                )
            except Exception as e:
                LOGS.info(str(e))
            del PMMESSAGE_CACHE[str(chat.id)]
        sql.del_collection("pmmessagecache")
        sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"show_pmpermit_options")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit these options are for users who messages you, not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = f"""Ecco la 𝗹𝗶𝘀𝘁𝗮 dei 𝗠𝗼𝘁𝗶𝘃𝗶 di {mention}.\n
__Quale buon Vento ti porta qui Straniero?__

**Scegli il Motivo per il quale mi stai Contattando:**"""
    buttons = [
        (Button.inline(text="Ho bisogno di un'informazione", data="to_enquire_something"),),
        (Button.inline(text="Ho una richiesta", data="to_request_something"),),
        (Button.inline(text="Vorrei solo chiacchierare", data="to_chat_with_my_master"),),
        (
            Button.inline(
                text="Voglio rompere i coglioni",
                data="to_spam_my_master_inbox",
            ),
        ),
    ]
    sqllist.add_to_list("pmoptions", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    await event.edit(text, buttons=buttons)


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"to_enquire_something")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit this options for user who messages you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = """📬 𝗩𝗮 𝗯𝗲𝗻𝗲, la tua richiesta è stata 𝗿𝗲𝗴𝗶𝘀𝘁𝗿𝗮𝘁𝗮, non scrivere più o verrai 𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 𝙖𝙪𝙩𝙤𝙢𝙖𝙩𝙞𝙘𝙖𝙢𝙚𝙣𝙩𝙚 \
al momento sono 𝗼𝗰𝗰𝘂𝗽𝗮𝘁𝗼, appena sarò disponibile 𝘃𝗲𝗿𝗿𝗮𝗶 𝗰𝗼𝗻𝘁𝗮𝘁𝘁𝗮𝘁𝗼 e potrai dirmi ciò che vuoi.\n\n__Ovviamente qualcosa di sensato...__"""
    sqllist.add_to_list("pmenquire", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"to_request_something")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit this options for user who messages you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = """📬 𝗩𝗮 𝗯𝗲𝗻𝗲, la tua richiesta è stata 𝗿𝗲𝗴𝗶𝘀𝘁𝗿𝗮𝘁𝗮, non scrivere più o verrai 𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 𝙖𝙪𝙩𝙤𝙢𝙖𝙩𝙞𝙘𝙖𝙢𝙚𝙣𝙩𝙚 \
al momento sono 𝗼𝗰𝗰𝘂𝗽𝗮𝘁𝗼, appena sarò disponibile 𝘃𝗲𝗿𝗿𝗮𝗶 𝗰𝗼𝗻𝘁𝗮𝘁𝘁𝗮𝘁𝗼 e potrai dirmi ciò che vuoi.\n\n__Ovviamente qualcosa di sensato...__"""
    sqllist.add_to_list("pmrequest", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"to_chat_with_my_master")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Coglione queste opzioni non sono per te, sono per chi ti scrive."
        return await event.answer(text, cache_time=0, alert=True)
    text = """📬 𝗩𝗮 𝗯𝗲𝗻𝗲, la tua richiesta è stata 𝗿𝗲𝗴𝗶𝘀𝘁𝗿𝗮𝘁𝗮, non scrivere più o verrai 𝗯𝗹𝗼𝗰𝗰𝗮𝘁𝗼 𝙖𝙪𝙩𝙤𝙢𝙖𝙩𝙞𝙘𝙖𝙢𝙚𝙣𝙩𝙚 \
al momento sono 𝗼𝗰𝗰𝘂𝗽𝗮𝘁𝗼, appena sarò disponibile 𝘃𝗲𝗿𝗿𝗮𝗶 𝗰𝗼𝗻𝘁𝗮𝘁𝘁𝗮𝘁𝗼 e potrai dirmi ciò che vuoi.\n\n__Ovviamente qualcosa di sensato...__"""
    sqllist.add_to_list("pmchat", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"to_spam_my_master_inbox")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Coglione queste opzioni non sono per te, sono per chi ti scrive."
        return await event.answer(text, cache_time=0, alert=True)
    text = "`███████▄▄███████████▄\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓███░░░░░░░░░░░░█\
         \n██████▀▀▀█░░░░██████▀ \
         \n░░░░░░░░░█░░░░█\
         \n░░░░░░░░░░█░░░█\
         \n░░░░░░░░░░░█░░█\
         \n░░░░░░░░░░░█░░█\
         \n░░░░░░░░░░░░▀▀`\
         \n**Ma dove credi di essere, vai a rompere i coglioni a qualcun'altro.\
         \n\nAl prossimo messaggio verrai bloccato.**"
    sqllist.add_to_list("pmspam", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmspam").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@catub.cat_cmd(
    pattern="pmguard (on|off)$",
    command=("pmguard", plugin_category),
    info={
        "header": "To turn on or turn off pmpermit.",
        "usage": "{tr}pmguard on/off",
    },
)
async def pmpermit_on(event):
    "Turn on/off pmpermit."
    input_str = event.pattern_match.group(1)
    if input_str == "on":
        if gvarstatus("pmpermit") is None:
            addgvar("pmpermit", "true")
            await edit_delete(
                event, "__Pmpermit has been enabled for your account successfully.__"
            )
        else:
            await edit_delete(event, "__Pmpermit is already enabled for your account__")
    elif gvarstatus("pmpermit") is not None:
        delgvar("pmpermit")
        await edit_delete(
            event, "__Pmpermit has been disabled for your account successfully__"
        )
    else:
        await edit_delete(event, "__Pmpermit is already disabled for your account__")


@catub.cat_cmd(
    pattern="pmmenu (on|off)$",
    command=("pmmenu", plugin_category),
    info={
        "header": "To turn on or turn off pmmenu.",
        "usage": "{tr}pmmenu on/off",
    },
)
async def pmpermit_on(event):
    "Turn on/off pmmenu."
    input_str = event.pattern_match.group(1)
    if input_str == "off":
        if gvarstatus("pmmenu") is None:
            addgvar("pmmenu", "false")
            await edit_delete(
                event,
                "__Pmpermit Menu has been disabled for your account successfully.__",
            )
        else:
            await edit_delete(
                event, "__Pmpermit Menu is already disabled for your account__"
            )
    elif gvarstatus("pmmenu") is not None:
        delgvar("pmmenu")
        await edit_delete(
            event, "__Pmpermit Menu has been enabled for your account successfully__"
        )
    else:
        await edit_delete(
            event, "__Pmpermit Menu is already enabled for your account__"
        )


@catub.cat_cmd(
    pattern="(a|approve)(?:\s|$)([\s\S]*)",
    command=("approve", plugin_category),
    info={
        "header": "To approve user to direct message you.",
        "usage": [
            "{tr}a/approve <username/reply reason> in group",
            "{tr}a/approve <reason> in pm",
        ],
    },
)
async def approve_p_m(event):  # sourcery no-metrics
    "To approve user to pm"
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(2)
    else:
        user, reason = await get_user_from_event(event, secondgroup=True)
        if not user:
            return
    if not reason:
        reason = "Nessuno"
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if not pmpermit_sql.is_approved(user.id):
        if str(user.id) in PM_WARNS:
            del PM_WARNS[str(user.id)]
        start_date = str(datetime.now().strftime("%B %d, %Y"))
        pmpermit_sql.approve(
            user.id, get_display_name(user), start_date, user.username, reason
        )
        chat = user
        if str(chat.id) in sqllist.get_collection_list("pmspam"):
            sqllist.rm_from_list("pmspam", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmchat"):
            sqllist.rm_from_list("pmchat", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmrequest"):
            sqllist.rm_from_list("pmrequest", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmenquire"):
            sqllist.rm_from_list("pmenquire", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmoptions"):
            sqllist.rm_from_list("pmoptions", chat.id)
        await edit_delete(
            event,
            f"✅ [{user.first_name}](tg://user?id={user.id}) la tua 𝗿𝗶𝗰𝗵𝗶𝗲𝘀𝘁𝗮 è stata 𝗮𝗽𝗽𝗿𝗼𝘃𝗮𝘁𝗮 ✅",
        )
        try:
            PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
        except AttributeError:
            PMMESSAGE_CACHE = {}
        if str(user.id) in PMMESSAGE_CACHE:
            try:
                await event.client.delete_messages(
                    user.id, PMMESSAGE_CACHE[str(user.id)]
                )
            except Exception as e:
                LOGS.info(str(e))
            del PMMESSAGE_CACHE[str(user.id)]
        sql.del_collection("pmwarns")
        sql.del_collection("pmmessagecache")
        sql.add_collection("pmwarns", PM_WARNS, {})
        sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    else:
        await edit_delete(
            event,
            f"✅ [{user.first_name}](tg://user?id={user.id}) è 𝗴𝗶𝗮' 𝗮𝗽𝗽𝗿𝗼𝘃𝗮𝘁𝗼 ✅",
        )


@catub.cat_cmd(
    pattern="(da|disapprove)(?:\s|$)([\s\S]*)",
    command=("disapprove", plugin_category),
    info={
        "header": "To disapprove user to direct message you.",
        "note": "This command works only for approved users",
        "options": {"all": "To disapprove all approved users"},
        "usage": [
            "{tr}da/disapprove <username/reply> in group",
            "{tr}da/disapprove in pm",
            "{tr}da/disapprove all - To disapprove all users.",
        ],
    },
)
async def disapprove_p_m(event):
    "To disapprove user to direct message you."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(2)

    else:
        reason = event.pattern_match.group(2)
        if reason != "all":
            user, reason = await get_user_from_event(event, secondgroup=True)
            if not user:
                return
    if reason == "all":
        pmpermit_sql.disapprove_all()
        return await edit_delete(
            event, "__Ok! I have disapproved everyone successfully.__"
        )
    if not reason:
        reason = "Nessuno."
    if pmpermit_sql.is_approved(user.id):
        pmpermit_sql.disapprove(user.id)
        await edit_or_reply(
            event,
            f"🚫 [{user.first_name}](tg://user?id={user.id}) la tua 𝗿𝗶𝗰𝗵𝗶𝗲𝘀𝘁𝗮 𝙣𝙤𝙣 è stata 𝗮𝗽𝗽𝗿𝗼𝘃𝗮𝘁𝗮 🚫\nㅤ\n𝗠𝗼𝘁𝗶𝘃𝗼:__ {reason}__",
        )
    else:
        await edit_delete(
            event,
            f"⚠️ [{user.first_name}](tg://user?id={user.id}) 𝙣𝙤𝙣 è 𝗮𝗽𝗽𝗿𝗼𝘃𝗮𝘁𝗼 ⚠️",
        )


@catub.cat_cmd(
    pattern="block(?:\s|$)([\s\S]*)",
    command=("block", plugin_category),
    info={
        "header": "To block user to direct message you.",
        "usage": [
            "{tr}block <username/reply reason> in group",
            "{tr}block <reason> in pm",
        ],
    },
)
async def block_p_m(event):
    "To block user to direct message you."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(1)
    else:
        user, reason = await get_user_from_event(event)
        if not user:
            return
    if not reason:
        reason = "Nessuno."
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(user.id) in PM_WARNS:
        del PM_WARNS[str(user.id)]
    if str(user.id) in PMMESSAGE_CACHE:
        try:
            await event.client.delete_messages(user.id, PMMESSAGE_CACHE[str(user.id)])
        except Exception as e:
            LOGS.info(str(e))
        del PMMESSAGE_CACHE[str(user.id)]
    if pmpermit_sql.is_approved(user.id):
        pmpermit_sql.disapprove(user.id)
    sql.del_collection("pmwarns")
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmwarns", PM_WARNS, {})
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    await event.client(functions.contacts.BlockRequest(user.id))
    await edit_delete(
        event,
        f"[{user.first_name}](tg://user?id={user.id}) __is blocked, he can no longer personal message you.__\n**Reason:** __{reason}__",
    )


@catub.cat_cmd(
    pattern="unblock(?:\s|$)([\s\S]*)",
    command=("unblock", plugin_category),
    info={
        "header": "To unblock a user.",
        "usage": [
            "{tr}unblock <username/reply reason> in group",
            "{tr}unblock <reason> in pm",
        ],
    },
)
async def unblock_pm(event):
    "To unblock a user."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(1)
    else:
        user, reason = await get_user_from_event(event)
        if not user:
            return
    if not reason:
        reason = "Nessuno."
    await event.client(functions.contacts.UnblockRequest(user.id))
    await event.edit(
        f"[{user.first_name}](tg://user?id={user.id}) __is unblocked he/she can personal message you from now on.__\n**Reason:** __{reason}__"
    )


@catub.cat_cmd(
    pattern="listapproved$",
    command=("listapproved", plugin_category),
    info={
        "header": "To see list of approved users.",
        "usage": [
            "{tr}listapproved",
        ],
    },
)
async def approve_p_m(event):
    "To see list of approved users."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __to work this plugin__",
        )
    approved_users = pmpermit_sql.get_all_approved()
    APPROVED_PMs = "**Current Approved PMs**\n\n"
    if len(approved_users) > 0:
        for user in approved_users:
            APPROVED_PMs += f"• 👤 {_format.mentionuser(user.first_name , user.user_id)}\n**ID:** `{user.user_id}`\n**UserName:** @{user.username}\n**Date: **__{user.date}__\n**Reason: **__{user.reason}__\n\n"
    else:
        APPROVED_PMs = "`You haven't approved anyone yet`"
    await edit_or_reply(
        event,
        APPROVED_PMs,
        file_name="approvedpms.txt",
        caption="`Current Approved PMs`",
    )
