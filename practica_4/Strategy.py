class FirstComeFirstServed():
    def __init__(self):
        self._queue = []
    
    def isEmpty(self):
        return len(self._queue) == 0
    
    def getNext(self):
        return self._queue.pop(0)

    def add(self, program):
        self._queue.append(program)
