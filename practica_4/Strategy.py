from ReadyQueue import *

class AbstractScheduler():
    def isEmpty(self):
        return self._queue.isEmpty()
    
    def getNext(self):
        return self._queue.getNext()

    def add(self, program):
        self._queue.add(program)
    
    def mustExpropiate(self, runningPcb, pcbToAdd):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))

class FirstComeFirstServed(AbstractScheduler):
    def __init__(self):
        self._queue = NoPriorityQueue()
    
    def mustExpropiate(self, runningPcb, pcbToAdd):
        return False

class PreemtiveShortestJobFirst(AbstractScheduler):
    def __init__(self):
        self._queue = PriorityQueue()

    def mustExpropiate(self, runningPcb, pcbToAdd):
        return runningPcb.remainingInstructions() > pcbToAdd.remainingInstructions()

class NoPreemtiveShortestJobFirst(AbstractScheduler):
    def __init__(self):
        self._queue = PriorityQueue()

    def mustExpropiate(self, runningPcb, pcbToAdd):
        return False
