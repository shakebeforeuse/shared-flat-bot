import datetime
import logging
from collections import defaultdict
import random
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Filters, PicklePersistence, Updater, CallbackQueryHandler

from config import __TOKEN__
from models import *
from es_ANDALUCIA import Translations as s

REGISTER_HOME = range(1)
REQUEST_DISPLAYNAME = range(1)
REQUEST_ROOM_NAME = range(1)
REQUEST_LIST_NAME = range(1)
CHOOSE_LIST_NAME, ADD_ELEMENT, CHOOSE_ELEMENT_NAME, REMOVE_ELEMENT = range(4)
REQUEST_ROTATION_NAME, REQUEST_MEMBERS, REQUEST_ROOMS, REQUEST_FREQUENCY, CHOOSE_ROTATION_NAME = range(5)

def start(update, context):
    if "is_configured" in context.chat_data.keys() and context.chat_data["is_configured"]:
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ALREADY_CONFIGURED)
    else:
        if update.effective_chat.type == "group" or update.effective_chat.type == "supergroup":
            context.bot.send_message(chat_id=update.effective_chat.id, text=s.WELCOME)
            context.bot.send_message(chat_id=update.effective_chat.id, text=s.REQUEST_HOME_NAME)
            return REGISTER_HOME

        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=s.NOT_A_GROUP)

def register_home(update, context):
    name = update.message.text
    context.chat_data["home"] = Home(name)
    context.chat_data["home"].chat_id = update.effective_chat.id

    update.message.reply_text(s.HOME_NAME_REGISTERED)
    return ConversationHandler.END

def add_user_request_displayname(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.REQUEST_USER_DISPLAYNAME)
    return REQUEST_DISPLAYNAME

def add_user_check_displayname(update, context):
    displayname = update.message.text[1:]

    if context.chat_data["home"].is_member(displayname):
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.USER_EXISTS)
    else:
        context.chat_data["home"].members.append(Member(displayname))
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.USER_REGISTERED)

    return ConversationHandler.END

def add_room_request_name(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.REQUEST_ROOM_NAME)
    return REQUEST_ROOM_NAME

def add_room_check_name(update, context):
    name = update.message.text

    if context.chat_data["home"].is_room(name):
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROOM_EXISTS)
    else:
        context.chat_data["home"].rooms.append(Room(name))
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROOM_REGISTERED)

    return ConversationHandler.END

def add_list_request_name(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.REQUEST_LIST_NAME)
    return REQUEST_LIST_NAME

def add_list_check_name(update, context):
    name = update.message.text

    if context.chat_data["home"].is_list(name):
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.LIST_EXISTS)
    else:
        context.chat_data["home"].lists[name] = List(name)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.LIST_REGISTERED)

    return ConversationHandler.END

def add_element_request_list(update, context):
    if context.chat_data["home"].lists.keys():
        keyboard = [[InlineKeyboardButton(list_name, callback_data=list_name) for list_name in context.chat_data["home"].lists.keys()]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.CHOOSE_LIST, reply_markup=reply_markup)
        
        return CHOOSE_LIST_NAME
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.THERE_ARE_NO_LISTS)
    return ConversationHandler.END

def add_element_choose_list_button(update, context):
    answer = update.callback_query.data
    context.user_data["list"] = answer
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.REQUEST_ELEMENT.format(answer))

    return ADD_ELEMENT

def add_element_to_list(update, context):
    name = update.message.text
    context.chat_data["home"].lists[context.user_data["list"]].content.append(name)
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.ELEMENT_REGISTERED)

    return ConversationHandler.END
    
def remove_element_request_list(update, context):
    if context.chat_data["home"].lists.keys():
        keyboard = [[InlineKeyboardButton(list_name, callback_data=list_name) for list_name in context.chat_data["home"].lists.keys()]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.CHOOSE_LIST, reply_markup=reply_markup)
        
        return CHOOSE_LIST_NAME
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.THERE_ARE_NO_LISTS)
    return ConversationHandler.END

def remove_element_choose_list_button(update, context):
    answer = update.callback_query.data
    context.user_data["list"] = answer

    if context.chat_data["home"].lists[answer].content:
        keyboard = [
            [
                InlineKeyboardButton(s.ALL, callback_data="<ALL>"),
            ],
            [
                InlineKeyboardButton(element_name, callback_data=element_name) for element_name in context.chat_data["home"].lists[answer].content
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.CHOOSE_ELEMENT.format(answer), reply_markup=reply_markup)

        return CHOOSE_ELEMENT_NAME
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.THERE_ARE_NO_ELEMENTS)
    return ConversationHandler.END

def remove_element_from_list_button(update, context):
    answer = update.callback_query.data

    if answer == "<ALL>":
        context.chat_data["home"].lists[context.user_data["list"]].content = []
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ELEMENT_REMOVED.format(s.ALL))
    else:
        context.chat_data["home"].lists[context.user_data["list"]].content.remove(answer)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ELEMENT_REMOVED.format(answer))

    return ConversationHandler.END

def show_list_request_list(update, context):
    if context.chat_data["home"].lists.keys():
        keyboard = [[InlineKeyboardButton(list_name, callback_data=list_name) for list_name in context.chat_data["home"].lists.keys()]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.CHOOSE_LIST, reply_markup=reply_markup)
        
        return CHOOSE_LIST_NAME
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.THERE_ARE_NO_LISTS)
    return ConversationHandler.END

def show_list_choose_list_button(update, context):
    answer = update.callback_query.data
    
    if context.chat_data["home"].lists[answer].content:
        response = s.ELEMENTS.format("\n".join(context.chat_data["home"].lists[answer].content))
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.THERE_ARE_NO_ELEMENTS)
    
    return ConversationHandler.END

def add_rotation_request_name(update, context):
    if context.chat_data["home"].members and context.chat_data["home"].rooms:
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.REQUEST_ROTATION_NAME)
        return REQUEST_ROTATION_NAME
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.REQUEST_ROTATION_NAME)
        return ConversationHandler.END

def add_rotation_check_name(update, context):
    name = update.message.text

    if context.chat_data["home"].is_rotation(name):
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROTATION_EXISTS)
        return ConversationHandler.END
    else:
        context.user_data["rotation"] = Rotation(name)

        keyboard = [[InlineKeyboardButton(member.displayname, callback_data=member.displayname) for member in context.chat_data["home"].members]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROTATION_REQUEST_MEMBERS, reply_markup=reply_markup)

        return REQUEST_MEMBERS

def add_rotation_request_member_button(update, context):
    answer = update.callback_query.data
    rotation = context.user_data["rotation"]

    if answer != "<END>":
        rotation.members.append(answer)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROTATION_MEMBER_REGISTERED)

        keyboard = [
            [
                InlineKeyboardButton("nadie más", callback_data="<END>")
            ],
            [
                InlineKeyboardButton(member.displayname, callback_data=member.displayname) for member in context.chat_data["home"].members if not member.displayname in rotation.members
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROTATION_REQUEST_MEMBERS, reply_markup=reply_markup)
        return REQUEST_MEMBERS
    
    else:
        keyboard = [[InlineKeyboardButton(room.name, callback_data=room.name) for room in context.chat_data["home"].rooms]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROTATION_REQUEST_ROOMS, reply_markup=reply_markup)

        return REQUEST_ROOMS

def add_rotation_request_rooms_button(update, context):
    answer = update.callback_query.data
    rotation = context.user_data["rotation"]

    if answer != "<END>":
        rotation.rooms.append(answer)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROTATION_ROOM_REGISTERED)

        keyboard = [
            [
                InlineKeyboardButton("ninguna más", callback_data="<END>")
            ],
            [
                InlineKeyboardButton(room.name, callback_data=room.name) for room in context.chat_data["home"].rooms if not room.name in rotation.rooms
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROTATION_REQUEST_ROOMS, reply_markup=reply_markup)
        return REQUEST_ROOMS
    
    else:
        keyboard = [[InlineKeyboardButton(freq, callback_data=str(key)) for key, freq in enumerate(s.FREQUENCIES)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROTATION_REQUEST_FREQUENCY, reply_markup=reply_markup)

        return REQUEST_FREQUENCY

def add_rotation_request_frequency_button(update, context):
    answer = int(update.callback_query.data)
    rotation = context.user_data["rotation"]
    rotation.frequency = Frequency(answer)
    rotation._home = context.chat_data["home"]
    context.chat_data["home"].rotations[rotation.name] = rotation

    context.bot.send_message(chat_id=update.effective_chat.id, text=s.ROTATION_REGISTERED)

    register_rotation(context.job_queue, rotation)

    return ConversationHandler.END

def remove_rotation_request_name(update, context):
    if context.chat_data["home"].rotations.keys():
        keyboard = [
            [
                InlineKeyboardButton(s.NONE, callback_data="<END>")
            ],
            [
                InlineKeyboardButton(rotation_name, callback_data=rotation_name) for rotation_name in context.chat_data["home"].rotations.keys()
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.CHOOSE_ROTATION, reply_markup=reply_markup)
        
        return CHOOSE_ROTATION_NAME
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.THERE_ARE_NO_ROTATIONS)
    return ConversationHandler.END

def remove_rotation_button(update, context):
    answer = update.callback_query.data

    if answer != "<END>":
        del context.chat_data["home"].rotations[answer]
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.ELEMENT_REMOVED.format(answer))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.OK)

    return ConversationHandler.END

def register_rotation(job_queue, rotation):
    if rotation.frequency == Frequency.DAILY:
        job_queue.run_daily(run_rotation, datetime.time(7, 30), context=rotation)
        job_queue.run_daily(run_rotation, datetime.time(7, 30), context=rotation)
    elif rotation.frequency == Frequency.WEEKLY:
        job_queue.run_daily(run_rotation, datetime.time(7, 30), days=(0,), context=rotation)
    elif rotation.frequency == Frequency.MONTHLY:
        job_queue.run_monthly(run_rotation, datetime.time(7, 30), 1, context=rotation)
    elif rotation.frequency == Frequency.YEARLY:
        job_queue.run_monthly(run_rotation, datetime.time(7, 30), 1, context=rotation)

def run_rotation(context):
    rotation_name = context.job.context.name
    home = context.job.context._home
    # if want the offset to persist, we need to change the data in _dispatcher
    # because context is a local copy
    rotation = context._dispatcher.chat_data[home.chat_id]["home"].rotations[rotation_name]

    completed = s.COMPLETED_ROTATIONS.format(" ".join(rotation.completed))
    context.bot.send_message(chat_id=rotation._home.chat_id, text=completed)
    rotation.completed = []

    rotation.offset = (rotation.offset + 1) % len(rotation.members)
    current = ""
    for room_number, room in enumerate(rotation.rooms):
        current += f" - {room}: @{rotation.members[(room_number + rotation.offset) % len(rotation.members)]}\n"
    
    context.bot.send_message(chat_id=rotation._home.chat_id, text=s.CURRENT_ROTATIONS.format(rotation.name, current))

def show_rotations(update, context):
    response = ""
    for name, rotation in context.chat_data["home"].rotations.items():
        current = ""
        for room_number, room in enumerate(rotation.rooms):
            member = rotation.members[(room_number + rotation.offset) % len(rotation.members)]
            completed = s.DONE if member in rotation.completed else ""
            current += f" - {room}: @{member} {completed}\n"
        
        response += s.CURRENT_ROTATIONS.format(name, current) + '\n'
    
    context.bot.send_message(chat_id=rotation._home.chat_id, text=response)

def done_rotation_request_rotation(update, context):
    if context.chat_data["home"].rotations.keys():
        keyboard = [
            [
                InlineKeyboardButton(s.ALL, callback_data="<ALL>"),
                InlineKeyboardButton(s.NONE, callback_data="<END>")
            ],
            [
                InlineKeyboardButton(rotation_name, callback_data=rotation_name) for rotation_name in context.chat_data["home"].rotations.keys()
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.CHOOSE_ROTATION, reply_markup=reply_markup)
        
        return CHOOSE_ROTATION_NAME
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=s.THERE_ARE_NO_ROTATIONS)
    return ConversationHandler.END

def done_rotation_button(update, context):
    answer = update.callback_query.data
    username = update.effective_user.username

    if answer == "<END>":
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.OK)
    elif answer == "<ALL>":
        for _, rotation in context.chat_data["home"].rotations.items():
            if username in rotation.members:
                rotation.completed.append(username)
        context.bot.send_message(chat_id=update.effective_chat.id, text=s.THANKS)
    else:
        if username in context.chat_data["home"].rotations[answer].members:
            context.chat_data["home"].rotations[answer].completed.append(username)
            context.bot.send_message(chat_id=update.effective_chat.id, text=s.THANKS)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=s.NOT_MEMBER_OF_ROTATION)


    return ConversationHandler.END

def random_message(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=random.choice(s.RANDOM))


def show_me_what_you_got(update, context):
    response = f"Home: {context.chat_data['home'].name}\n  Members: "
    response += " ".join(map(str, context.chat_data["home"].members))
    response += "\nRooms: " + " ".join(map(str, context.chat_data["home"].rooms))
    response += "\nLists: " + " ".join(map(str, context.chat_data["home"].lists))
    response += "\nRotations: " + " \n".join(map(str, context.chat_data["home"].rotations))

    context.bot.send_message(chat_id=update.effective_chat.id, text=response)


def general_error_message(update, context):
    update.message.reply_text(s.GENERAL_ERROR)


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

    persistence = PicklePersistence(filename="choza_persistence.pkl")
    updater = Updater(token=__TOKEN__, persistence=persistence, use_context=True)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue


    start_conv = ConversationHandler(
        entry_points=[
                CommandHandler("start", start),
            ],
        states={
            REGISTER_HOME: [
                MessageHandler(Filters.text, register_home)
            ]
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)]
    )

    add_user_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add_user", add_user_request_displayname)
        ],
        states={
            REQUEST_DISPLAYNAME: [
                MessageHandler(Filters.regex('^@[a-zA-Z0-9_]{3,}$'), add_user_check_displayname)
            ],
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)]
    )

    add_room_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add_room", add_room_request_name)
        ],
        states={
            REQUEST_ROOM_NAME: [
                MessageHandler(Filters.text, add_room_check_name)
            ],
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)]
    )

    add_list_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add_list", add_list_request_name)
        ],
        states={
            REQUEST_LIST_NAME: [
                MessageHandler(Filters.text, add_list_check_name)
            ],
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)]
    )

    add_element_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add_element_to_list", add_element_request_list),
            CommandHandler("add_element", add_element_request_list)
        ],
        states={
            CHOOSE_LIST_NAME: [
                CallbackQueryHandler(add_element_choose_list_button)
            ],
            ADD_ELEMENT: [
                MessageHandler(Filters.text, add_element_to_list)
            ],
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)],
        per_message=False
    )

    remove_element_conv = ConversationHandler(
        entry_points=[
            CommandHandler("remove_element_from_list", remove_element_request_list),
            CommandHandler("remove_element", remove_element_request_list),
        ],
        states={
            CHOOSE_LIST_NAME: [
                CallbackQueryHandler(remove_element_choose_list_button)
            ],
            CHOOSE_ELEMENT_NAME: [
                CallbackQueryHandler(remove_element_from_list_button),
            ],
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)],
        per_message=False
    )

    show_list_conv = ConversationHandler(
        entry_points=[
            CommandHandler("show_list", show_list_request_list)
        ],
        states={
            CHOOSE_LIST_NAME: [
                CallbackQueryHandler(show_list_choose_list_button),
            ]
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)],
        per_message=False
    )

    add_rotation_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add_rotation", add_rotation_request_name)
        ],
        states={
            REQUEST_ROTATION_NAME: [
                MessageHandler(Filters.text, add_rotation_check_name)
            ],
            REQUEST_MEMBERS: [
                CallbackQueryHandler(add_rotation_request_member_button)
            ],
            REQUEST_ROOMS: [
                CallbackQueryHandler(add_rotation_request_rooms_button)
            ],
            REQUEST_FREQUENCY: [
                CallbackQueryHandler(add_rotation_request_frequency_button)
            ],
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)],
        per_message=False
    )

    remove_rotation_conv = ConversationHandler(
        entry_points=[
            CommandHandler("remove_rotation", remove_rotation_request_name)
        ],
        states={
            CHOOSE_ROTATION_NAME: [
                CallbackQueryHandler(remove_rotation_button)
            ]
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)],
        per_message=False
    )

    done_rotation_conv = ConversationHandler(
        entry_points=[
            CommandHandler("done_rotation", done_rotation_request_rotation),
            CommandHandler("done", done_rotation_request_rotation),
        ],
        states={
            CHOOSE_ROTATION_NAME: [
                CallbackQueryHandler(done_rotation_button),
            ],
        },
        fallbacks=[MessageHandler(Filters.all, general_error_message)],
        per_message=False
    )

    dispatcher.add_handler(start_conv)
    dispatcher.add_handler(add_user_conv)
    dispatcher.add_handler(add_room_conv)
    dispatcher.add_handler(add_list_conv)
    dispatcher.add_handler(add_element_conv)
    dispatcher.add_handler(remove_element_conv)
    dispatcher.add_handler(show_list_conv)
    dispatcher.add_handler(add_rotation_conv)
    dispatcher.add_handler(remove_rotation_conv)
    dispatcher.add_handler(done_rotation_conv)

    dispatcher.add_handler(CommandHandler("show_me_what_you_got", show_me_what_you_got))
    dispatcher.add_handler(CommandHandler("show_rotations", show_rotations))
    dispatcher.add_handler(CommandHandler("random", random_message))

    # Reload rotations
    for _, chat in persistence.get_chat_data().items():
        if "home" in chat.keys():
            for _, rotation in chat["home"].rotations.items():
                register_rotation(job_queue, rotation)


    # dispatcher.add_handler(CommandHandler("start_rotation", start_rotation))
    # dispatcher.add_handler(CommandHandler("schedule", schedule))
    # dispatcher.add_handler(CommandHandler("debug_bypass_date", debug_bypass_date))
    # dispatcher.add_handler(CommandHandler("done", done))
    # dispatcher.add_handler(CommandHandler("not_done", not_done))


    updater.start_polling()
    updater.idle()