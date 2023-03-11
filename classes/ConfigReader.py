import yaml
import shlex
import time
from yaml.loader import SafeLoader

class ConfigReader():
    path = ''
    data = None
    callback = None

    def __init__(self, path, callback = None, autoLoad = True):
        self.callback = callback
        self.bind(path)
        if (autoLoad):
            self.load()

    def bind(self, path):
        self.path = path

    def load(self, path = None):
        with open(self.path or path) as f:
            self.data = yaml.load(f, Loader=SafeLoader)
        if self.callback:
            self.callback(time = time.strftime('%Y-%m-%d %H:%M:%S'), event = 'ConfigLoaded', data = self.data)

    def dump(self):
        if not self.data:
            self.load()
        print(self.data)
    
    def readWithDefaults(self, data, key, defaultsKey = '_defaults', dropDefaultsAfterMerge = True):
        if hasattr(data, defaultsKey):
            # merge defaults
            buf = {**data[defaultsKey], **data[key]}
            if dropDefaultsAfterMerge:
                # drop _defaults - key from dict
                buf.pop(defaultsKey)
            return buf
        else: 
            return data[key]

    def read(self, keys, useDefaults = True):
        try:
            return self.readWithDefaults(self.data, keys) if useDefaults else self.data[keys]
        except TypeError:
            # retrieve config value by using hashed tokens (e.g. ["config","category","item"])
            buf = self.data
            for key in keys:
                buf = self.readWithDefaults(buf, key) if useDefaults else buf[key]
            return buf
        except KeyError:
            # retrieve config value by token query (e.g. "config.category.item")
                tokens = keys.split(".")
                buf = self.data
                for key in tokens:
                    try:
                        buf = self.readWithDefaults(buf, key) if useDefaults else buf[key]
                    except KeyError:
                        msg = "key "+key+" could not be found (context: "+keys+")"
                        if self.callback:
                            self.callback(time = time.strftime('%Y-%m-%d %H:%M:%S'), event = 'KeyError', error = 'KeyError', message = msg)
                        else:
                            raise KeyError(msg)
                        return
                return buf

