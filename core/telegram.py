import pprint
import json
class TelegramException(Exception):
    pass

TELEGRAM = None
class TelegramService():
    @staticmethod
    def instance():
        global TELEGRAM
        if TELEGRAM == None:
            TELEGRAM = TelegramService()
        return TELEGRAM
        
    def __init__(self):
        self.bot = None
        self.update = None
        
    @property
    def username(self):
        return self.user.username
        
    @property
    def user(self):
        return self.update.message.from_user
    # @property
    # def chat_title(self):
        # return self.chat.title
        
    # @property
    # def chat_id(self):
        # return self.chat.chat_id
        
    @property
    def chat(self):
        return self.update.message.chat
        
    @staticmethod
    def current_user():
        return TelegramService.instance().user
        
    # @staticmethod
    # def chat():
        # inst = TelegramService.instance()
        # return { "id" : inst.chat_id, "title" : inst.chat_title, "type" : inst.chat.type }
        
    @staticmethod
    def message(bot, update):
        inst = TelegramService.instance()
        pprint.pprint(update.message.chat.__dict__)
        inst.bot = bot
        inst.update = update
        print "Message info set"
        
    @staticmethod
    def clear():
        inst = TelegramService.instance()
        inst.bot = None
        inst.update = None
        print "Message info cleared"
        
    @staticmethod
    def respond(message):
        inst = TelegramService.instance()
        inst.bot.send_message(chat_id=inst.chat.id, text=message)
        