from telegram.error import TelegramError

class CommandFailure(TelegramError):
    def __init__(self, message):
        super(CommandFailure, self).__init__(message)
        