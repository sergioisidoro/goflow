class Event:

    def __init__(self):
        self.callbacks = set() 

    def __iadd__(self, callback):
        self.callbacks.add(callback)
        return self

    def __isub__(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)
        return self

    def __call__(self, *args, **kwds):
        for callback in self.callbacks:
            callback(*args, **kwds)


if __name__ == '__main__':
    
    def handler1(msg):
    	print("1: %s" % msg)


    def handler2(msg):
    	print("2: %s" % msg)

    ontestevent = Event()
    ontestevent += handler1
    ontestevent += handler2

    ontestevent("test")

