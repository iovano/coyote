import datetime

class Logger():
    verbosity = 4
    target = 'STD'
    mode = 'a+'                 
    levels = ['FATAL  ', 'CRITICAL', 'ERROR  ', 'WARN   ', 'NOTICE ', 'DEBUG  ']
    lastMessage = None
    lastMessageLevel = None
    redundantMessages = 0
    def __init__(self, target = 'STD', verbosity = 4):
        self.target = target
        self.verbosity = verbosity

    def log(self, message, level = 4):
        if self.verbosity >= level:
            if message == self.lastMessage:
                self.redundantMessages += 1
            else:
                if (self.redundantMessages > 0):
                    redundantMessage = self.lastMessage + " [repeated "+str(self.redundantMessages)+" times]"
                    self.redundantMessages = 0
                    self.log(redundantMessage, self.lastMessageLevel)
                if self.target != 'STD':
                    logfile = open(self.target, self.mode)
                    logfile.write("["+self.getCurrentTimestamp()+"]: "+message+"\n")
                    logfile.close()
                else:
                    print(self.getCurrentTimestamp()+" | "+(self.levels[level] if len(self.levels) > level else '')+" : "+message)
                self.lastMessage = message
                self.lastMessageLevel = level

    def getCurrentTimestamp(self, format = "%y-%m-%d %H:%M:%S"):
        return datetime.datetime.now().strftime(format)