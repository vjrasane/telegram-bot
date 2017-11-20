from telegram.ext import Updater, CommandHandler, MessageHandler, InlineQueryHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                            TimedOut, ChatMigrated, NetworkError)
import datetime as dt
import logging
import sys
import json
import logging

import time
import shlex

from modules.economy import Economy

from utils.errors import CommandFailure
from utils.database import Database
from utils.utils import replace_placeholders
from utils.utils import rchop, lchop, encode_dict, parse_args
from utils.utils import get_or_init, random_string, read_json, CommandFailure


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_arg(args, index=0):
    if len(args) > index:
        return args[index]
    return None

def echo_args(bot, update, args):
    _send_message(bot, update, _parse_args(args))
    
def _send_message(bot, update, message):
    bot.send_message(chat_id=update.message.chat_id, text=message)
    
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, lol yolo swag")

def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)
        
def _get_user_access_data(username, create=True):
    user_access_group = database.group("access").group("users")
    user_access_table = user_access_group.table(username, create)
    if user_access_table:
        user_access_data = user_access_table.read()
        return user_access_data, user_access_table
    else:
        return {}, None

password_file = "obliterator.password"
def _generate_master_password():
    global master_password
    pw = random_string(16)
    with open(password_file, 'w') as pwf:
        pwf.write(pw + "\n")
    master_password = pw
        
def _use_master_password( password ):
    if master_password == password:
        _generate_master_password()
        return True
    return False
        
def _require_permissions(required, user, params=None):
    username = user.username
    user_id = user.id
    params = params or {}
    required = replace_placeholders(required, params)
    if "password" in params and _use_master_password(params["password"]):
        return
    
    data, table = _get_user_access_data(username)
    stored_id = get_or_init(data, "user_id", None)
    if not stored_id:
        data["user_id"] = user_id
        stored_id = user_id
        table.write(data)
        
    if stored_id == user_id:
        permissions = data.get("permissions", [])
        for r in required:
            if r in permissions:
                return

    raise CommandFailure("I'm afraid I can't let you do that %s" % username)
        
def _add_permissions(username, permissions):
    data, table = _get_user_access_data(username)
    
    user_permissions = get_or_init(data, "permissions", [])
    added = [ p for p in permissions if not p in user_permissions ]
        
    if len(added) > 0:    
        data["permissions"] += added # Here we can be sure the permissions exist
        table.write(data)
        return "Authorized user %s: %s" % (username, ", ".join(added))
    else:
        return "No new permissions to add."
    
def _remove_permissions(username, permissions):
    data, table = _get_user_access_data(username)
    
    user_permissions = get_or_init(data, "permissions", [])
    removed = [ p for p in permissions if p in user_permissions ]
    
    if len(removed) > 0:    
        data["permissions"] = [ p for p in user_permissions if p not in removed ]
        table.write(data)
        return "Deauthorized user %s: %s" % (username, ", ".join(removed))
    else:
        return "No permissions were removed."
    
def _get_permissions(username):
    data, table = _get_user_access_data(username, False)
    return data.get("permissions", [])
       
def permissions(bot, update, args):
    labeled, unlabeled = parse_args(args)
    _require_permissions(
        required=[ "admin", "permissions", "permissions:inspect" ],
        user=update.message.from_user,
        password=labeled.get("master_password", None))
    
    username = get_arg(unlabeled)
    if not username:
        username = update.message.from_user.username
        
    permissions = _get_permissions(username)
    if len(permissions) > 0:
        _send_message(bot, update, "User %s has permissions: %s" % (username, ", ".join(permissions)))
    else:
        _send_message(bot, update, "No permissions set for user %s" % username)
  
def authorize(bot, update, args):
    labeled, unlabeled = parse_args(args)
    _require_permissions(
        required=[ "admin", "permissions", "permissions:add" ],
        user=update.message.from_user,
        password=labeled.get("master_password", None))
    
    username = labeled.get("user", None)
    if not username:
        username = update.message.from_user.username
    else:
        username = lchop(username, "@")

    channel = labeled.get("channel", False) 
    permissions = [ p for p in unlabeled ]
    if len(permissions) == 0:
        _send_message(bot, update, "No permissions given")
    else:
        message = _add_permissions(username, permissions)
        _send_message(bot, update, message)
    
def deauthorize(bot, update, args):
    labeled, unlabeled = parse_args(args)
    _require_permissions(
        required=[ "admin", "permissions", "permissions:remove" ],
        user=update.message.from_user,
        password=labeled.get("master_password", None))
    
    username = labeled.get("user", None)
    if not username:
        username = update.message.from_user.username   
    else:
        username = lchop(username, "@")

    channel = labeled.get("channel", False)  
    permissions = [ p.encode('utf-8') for p in unlabeled ]
    if len(permissions) == 0:
        _send_message(bot, update, "No permissions given")
    else:
        message = _remove_permissions(username, permissions)
        _send_message(bot, update, message)
    
def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")
    
def error_callback(bot, update, error):
    try:
        raise error
    except CommandFailure as f:
        _send_message(bot, update, f.message)

config_file = ".config"
images_file = "images.data"

config = read_json(config_file)
database = Database(config["database"])

images = read_json(images_file)

_generate_master_password()

updater = Updater(token=config["api_token"])
dispatcher = updater.dispatcher

module_config = { "database" : database, "images" : images }
module_callbacks = { "respond" : _send_message, "permissions" : _require_permissions }

modules = [ Economy(module_config, module_callbacks) ]
for m in modules:
    for h in m.handlers or []:
        dispatcher.add_handler(h)
        

main_handlers = [
    CommandHandler('start', start),
    CommandHandler('authorize', authorize, pass_args=True),
    CommandHandler('deauthorize', deauthorize, pass_args=True),
    CommandHandler('permissions', permissions, pass_args=True),
    CommandHandler('args', echo_args, pass_args=True),
    MessageHandler(Filters.text, echo),
    MessageHandler(Filters.command, unknown)
]

for h in main_handlers:
    dispatcher.add_handler(h)
    
dispatcher.add_error_handler(error_callback)
updater.start_polling()

# schedule.run_continuously()


