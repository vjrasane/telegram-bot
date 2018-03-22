
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
        return self.update.message.from_user.username
        
    @staticmethod
    def user():
        return TelegramService.instance().update.message.from_user
        
    @staticmethod
    def message(bot, update):
        inst = TelegramService.instance()
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
        inst.bot.send_message(chat_id=inst.update.message.chat_id, text=message)
        