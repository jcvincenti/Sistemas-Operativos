class AbstractQueue():
    def __init__(self):
        self._queue = []
    
    def isEmpty(self):
        return len(self._queue) == 0
    
    def getNext(self):
        return self._queue.pop(0)

class NoPriorityQueue(AbstractQueue):
    def add(self, program):
        self._queue.append(program)

class PriorityQueue(AbstractQueue):
    def add(self, program):
        self._queue.append(program)
        self._queue.sort(key=lambda x: x.priority)