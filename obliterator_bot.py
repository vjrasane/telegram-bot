from telegram.ext import Updater, CommandHandler, MessageHandler, InlineQueryHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                            TimedOut, ChatMigrated, NetworkError)
import datetime as dt
import logging
import sys
import json
import logging
import string
import random
import time
import shlex


current_milli_time = lambda : int(round(time.time() * 1000))
random_string = lambda N : ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class CommandFailure(TelegramError):
    def __init__(self, message):
        super(CommandFailure, self).__init__(message)

def get_arg(args, index=0):
    if len(args) > index:
        return args[index]
    return None
    
def rchop(string, sub):
    if string.endswith(sub):
        return string[:-len(sub)]

def lchop(string, sub):
    if string.startswith(sub):
        return string[len(sub):]

ARGUMENT_PREFIX = "-"
ARGUMENT_EQUATOR = "="
        
def _parse_args(args):
    arg_str = " ".join(args).encode('utf-8')
    shell_args = shlex.split(arg_str)

    labeled = {}
    unlabeled = []
    for s in shell_args:
        if s.startswith(ARGUMENT_PREFIX):
            arg_split = s.split(ARGUMENT_EQUATOR)
            key = lchop(arg_split[0].strip(), ARGUMENT_PREFIX)
            if len(arg_split) == 2:
                labeled[key] = arg_split[1].strip()
            else:
                labeled[key] = True
        else:
            unlabeled.append(s)
    
    return labeled, unlabeled

def echo_args(bot, update, args):
    send_message(bot, update, _parse_args(args))
    
def send_message(bot, update, message):
    bot.send_message(chat_id=update.message.chat_id, text=message)
    
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, lol yolo swag")

def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)

def caps(bot, update, args):
    text_caps = ' '.join(args).upper()
    bot.send_message(chat_id=update.message.chat_id, text=text_caps)
    
def require_permissions(user, required, password):
    username = user.username
    user_id = user.id
    if _use_master_password(password):
        return
    
    if username in data["access"]:
        access = data["access"][username]
        stored_id = access["user_id"]
        if stored_id == None:
            access["user_id"] = user_id
        elif stored_id != user_id:
            raise CommandFailure("User ID does not match the authorized user ID")
        
        permissions = access["permissions"]
            
        authorized = True
        for r in required:
            if not r in permissions:
                authorized = False
        if authorized:
            return

    raise CommandFailure("Unauthorized user %s. Required permissions: %s" % (username, ", ".join(required)))
        
def add_permissions(username, permissions): 
    if not username in data["access"]:
        data["access"][username] = { "user_id" : None, "permissions" : [] }
    
    user_permissions = data["access"][username]["permissions"]
    added = [ p for p in permissions if not p in user_permissions ]
        
    if len(added) > 0:    
        data["access"][username]["permissions"] += added
        _write_config()
        return "Authorized user %s: %s" % (username, ", ".join(added))
    else:
        return "No new permissions to add."
    
def remove_permissions(username, permissions):
    if not username in data["access"]:
        data["access"][username] = { "user_id" : None, "permissions" : [] }
    
    user_permissions = data["access"][username]["permissions"]
    removed = [ p for p in permissions if p in user_permissions ]
    
    if len(removed) > 0:    
        data["access"][username]["permissions"] = [ p for p in user_permissions if p not in removed ]
        _write_config()
        return "Deauthorized user %s: %s" % (username, ", ".join(removed))
    else:
        return "No permissions were removed."
    
def get_permissions(username):
    if username in data["access"]:
        return data["access"][username]["permissions"]
    return []
       
def permissions(bot, update, args):
    labeled, unlabeled = _parse_args(args)
    require_permissions(update.message.from_user, required=["inspect"], password=labeled.get("master_password", None))
    
    username = get_arg(unlabeled)
    if not username:
        username = update.message.from_user.username
        
    permissions = get_permissions(username)
    if len(permissions) > 0:
        send_message(bot, update, "User %s has permissions: %s" % (username, ", ".join(permissions)))
    else:
        send_message(bot, update, "No permissions set for user %s" % username)
  
def authorize(bot, update, args):
    labeled, unlabeled = _parse_args(args)
    require_permissions(user=update.message.from_user, required=["admin"], password=labeled.get("master_password", None))
    
    username = labeled.get("user", None)
    channel = labeled.get("channel", False)
    
    permissions = [ p for p in unlabeled ]
    
    if not username:
        send_message(bot, update, "No username given")
    elif len(permissions) == 0:
        send_message(bot, update, "No permissions given")
    else:
        message = add_permissions(username, permissions)
        send_message(bot, update, message)
    
def deauthorize(bot, update, args):
    labeled, unlabeled = _parse_args(args)
    require_permissions(user=update.message.from_user, required=["admin"], password=labeled.get("master_password", None))
    
    username = get_arg(unlabeled)
    permissions = [ p.encode('utf-8') for p in unlabeled[1:] ]
    
    if not username:
        send_message(bot, update, "No username given")
    elif len(permissions) == 0:
        send_message(bot, update, "No permissions given")
    else:
        message = remove_permissions(username, permissions)
        send_message(bot, update, message)
    
def inline_caps(bot, update):
    query = update.inline_query.query
    if not query:
        return
    results = list()
    results.append(
        InlineQueryResultArticle(
            id = query.upper(),
            title = 'Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    bot.answer_inline_query(update.inline_query.id, results)
    
def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")

def encode_list( u_list, encoding="utf-8" ):
    encoded = []
    for item in u_list:
        if isinstance(item, unicode):
            item = item.encode(encoding)
        elif isinstance(item, dict):
            item = encode_dict(item)
        elif isinstance(item, list):
            item = encode_list(item)
        encoded.append(item)
    return encoded

def encode_dict( u_dict, encoding="utf-8" ):
    encoded = {}
    for key,val in u_dict.iteritems():
        key = key.encode(encoding)
        if isinstance(val, unicode):
            val = val.encode(encoding)
        elif isinstance(val, list):
            val = encode_list(val, encoding)
        elif isinstance(val, dict):
            val = encode_dict(val, encoding)
        encoded[key] = val
    return encoded
    
def _use_master_password( password ):
    if master_password == password:
        _generate_master_password()
        return True
    return False

data = {}
data_file = "obliterator.data"
def _read_config( ):
    with open(data_file) as df:
        return json.load(df, encoding='utf-8', object_hook=encode_dict)

def _write_config( ):
    with open(data_file, 'w') as df:
        json.dump(data, df, encoding='utf-8', indent=4 )
    
password_file = "obliterator.password"
def _generate_master_password():
    global master_password
    pw = random_string(16)
    with open(password_file, 'w') as pwf:
        pwf.write(pw + "\n")
    master_password = pw

api_key_file = "obliterator.key"
def _read_api_key():
    with open(api_key_file) as akf:
        return akf.read()
    
def error_callback(bot, update, error):
    try:
        raise error
    except CommandFailure as f:
        send_message(bot, update, f.message)

try:
    data = _read_config()
except (IOError, ValueError):
    # Default config
    data = { "time" : str(dt.datetime.now()), "currency": [], "access": { "channels" : {}, "users": {} } }

api_key = _read_api_key().strip()
_generate_master_password()
_write_config()

updater = Updater(token=api_key)
dispatcher = updater.dispatcher
    
start_handler = CommandHandler('start', start)
caps_handler = CommandHandler('caps', caps, pass_args=True)

authorize_handler = CommandHandler('authorize', authorize, pass_args=True)
deauthorize_handler = CommandHandler('deauthorize', deauthorize, pass_args=True)
permissions_handler = CommandHandler('permissions', permissions, pass_args=True)

echo_args_handler = CommandHandler('args', echo_args, pass_args=True)

echo_handler = MessageHandler(Filters.text, echo)
inline_caps_handler = InlineQueryHandler(inline_caps)
unknown_handler = MessageHandler(Filters.command, unknown)

dispatcher.add_handler(authorize_handler)
dispatcher.add_handler(deauthorize_handler)
dispatcher.add_handler(permissions_handler)
dispatcher.add_handler(echo_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(caps_handler)
dispatcher.add_handler(inline_caps_handler)
dispatcher.add_handler(echo_args_handler)

dispatcher.add_handler(unknown_handler)

dispatcher.add_error_handler(error_callback)

updater.start_polling()


