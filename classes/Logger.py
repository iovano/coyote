import datetime

class Logger():
    verbosity = 2
    target = 'STD'
    mode = 'a+'                 
    def __init__(self, target = 'STD', verbosity = 2):
        self.target = target
        self.verbosity = verbosity

    def log(self, message, level = 2):
        if self.verbosity >= level:
            if self.target != 'STD':
                logfile = open(self.target, self.mode)
                logfile.write("["+self.getCurrentTimestamp()+"]: "+message+"\n")
                logfile.close()
            else:
                print("["+self.getCurrentTimestamp()+"]: "+message)

    def getCurrentTimestamp(self, format = "%Y-%m-%d %H:%M:%S"):
        return datetime.datetime.now().strftime(format)