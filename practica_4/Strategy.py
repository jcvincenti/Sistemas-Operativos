from ReadyQueue import *
from hardware import *

class AbstractScheduler():
    def isEmpty(self):
        return self._queue.isEmpty()
    
    def getNext(self):
        return self._queue.getNext()

    def add(self, program):
        self._queue.add(program)
    
    def mustExpropiate(self, runningPcb, pcbToAdd):
        return False

class FirstComeFirstServed(AbstractScheduler):
    def __init__(self):
        self._queue = NoPriorityQueue()

class PreemtiveShortestJobFirst(AbstractScheduler):
    def __init__(self):
        self._queue = SJFQueue()

    def mustExpropiate(self, runningPcb, pcbToAdd):
        return runningPcb.remainingInternalInstructions() > pcbToAdd.remainingInternalInstructions()

class NoPreemtiveShortestJobFirst(AbstractScheduler):
    def __init__(self):
        self._queue = SJFQueue()

class RoundRobin(AbstractScheduler):
    def __init__(self):
        self._queue = NoPriorityQueue()
        HARDWARE.timer.quantum = 3

class PriorityExpropiativo(AbstractScheduler):
    def __init__(self):
        self._queue = PriorityQueue()

    def mustExpropiate(self, runningPcb, pcbToAdd):
        return runningPcb._priority > pcbToAdd._priority

class PriorityNoExpropiativo(AbstractScheduler):
    def __init__(self):
        self._queue = PriorityQueue()    
