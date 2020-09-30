#!/usr/bin/env python

from hardware import *
from pcbState import *
import log



## emulates a compiled program
class Program():

    def __init__(self, name, instructions):
        self._name = name
        self._instructions = self.expand(instructions)

    @property
    def name(self):
        return self._name

    @property
    def instructions(self):
        return self._instructions

    def addInstr(self, instruction):
        self._instructions.append(instruction)

    def expand(self, instructions):
        expanded = []
        for i in instructions:
            if isinstance(i, list):
                ## is a list of instructions
                expanded.extend(i)
            else:
                ## a single instr (a String)
                expanded.append(i)

        ## now test if last instruction is EXIT
        ## if not... add an EXIT as final instruction
        last = expanded[-1]
        if not ASM.isEXIT(last):
            expanded.append(INSTRUCTION_EXIT)

        return expanded

    def __repr__(self):
        return "Program({name}, {instructions})".format(name=self._name, instructions=self._instructions)


## emulates an Input/Output device controller (driver)
class IoDeviceController():

    def __init__(self, device):
        self._device = device
        self._waiting_queue = []
        self._currentPCB = None

    def runOperation(self, pcb, instruction):
        pair = {'pcb': pcb, 'instruction': instruction}
        # append: adds the element at the end of the queue
        self._waiting_queue.append(pair)
        # try to send the instruction to hardware's device (if is idle)
        self.__load_from_waiting_queue_if_apply()

    def getFinishedPCB(self):
        finishedPCB = self._currentPCB
        self._currentPCB = None
        self.__load_from_waiting_queue_if_apply()
        return finishedPCB

    def __load_from_waiting_queue_if_apply(self):
        if (len(self._waiting_queue) > 0) and self._device.is_idle:
            ## pop(): extracts (deletes and return) the first element in queue
            pair = self._waiting_queue.pop(0)
            #print(pair)
            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb
            self._device.execute(instruction)


    def __repr__(self):
        return "IoDeviceController for {deviceID} running: {currentPCB} waiting: {waiting_queue}".format(deviceID=self._device.deviceId, currentPCB=self._currentPCB, waiting_queue=self._waiting_queue)

## emulates the  Interruptions Handlers
class AbstractInterruptionHandler():
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def kernel(self):
        return self._kernel

    def execute(self, irq):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))

    def loadIfReadyQueueNotEmpty(self):
        if not self.kernel._readyQueue.isEmpty():
            pcb = self.kernel._readyQueue.get()
            pcb.state = PCBState.RUNNING
            self.kernel._dispatcher.load(pcb)
            self.kernel._pcbTable._runningPCB = pcb
    
    def loadIfNoRunningPcb(self, pcb):
        if self.kernel._pcbTable.runningPCB:
            pcb.state = PCBState.READY
            self.kernel._readyQueue.add(pcb)
        else:
            pcb.state = PCBState.RUNNING
            self.kernel._dispatcher.load(pcb)
            self.kernel._pcbTable._runningPCB = pcb


class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        log.logger.info(" Program Finished ")
        pcb = self.kernel._pcbTable.runningPCB
        self.kernel._pcbTable._runningPCB = None
        pcb.state = PCBState.TERMINATED
        self.kernel._dispatcher.save(pcb)
        self.loadIfReadyQueueNotEmpty()
        

class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        operation = irq.parameters
        pcb = self.kernel._pcbTable.runningPCB
        self.kernel._dispatcher.save(pcb)
        self.kernel._pcbTable._runningPCB = None
        pcb.state = PCBState.WAITING
        self.kernel.ioDeviceController.runOperation(pcb, operation)
        log.logger.info(self.kernel.ioDeviceController)
        self.loadIfReadyQueueNotEmpty()


class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        pcb = self.kernel.ioDeviceController.getFinishedPCB()
        log.logger.info(self.kernel.ioDeviceController)
        self.loadIfNoRunningPcb(pcb)
        

class NewInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        program = irq.parameters
        dir = self.kernel._loader.loadInMemory(program)
        pid = self.kernel._pcbTable.getNewPID()
        pcb = PCB(pid, dir, program.name)
        self.kernel._pcbTable.add(pcb)
        self.loadIfNoRunningPcb(pcb)

# emulates the core of an Operative System
class Kernel():

    def __init__(self):
        ## setup interruption handlers
        killHandler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, killHandler)

        ioInHandler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, ioInHandler)

        ioOutHandler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, ioOutHandler)

        newHandler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, newHandler)

        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)
        self._pcbTable = PCBTable()
        self._loader = Loader()
        self._readyQueue = ReadyQueue()
        self._dispatcher = Dispatcher()

    @property
    def ioDeviceController(self):
        return self._ioDeviceController

    ## emulates a "system call" for programs execution
    def run(self, program):
        newIRQ = IRQ(NEW_INTERRUPTION_TYPE, program)
        HARDWARE.interruptVector.handle(newIRQ)

        # set CPU program counter at program's first intruction
        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)

    def __repr__(self):
        return "Kernel "

class PCB():
    
    def __init__(self, pid, basedir, path):
        self._pid = pid
        self._basedir = basedir
        self._path = path
        self._state = PCBState.NEW
        self._pc = 0

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

class PCBTable():
    
    def __init__(self):
        self._pcbs = []
        self._pidCounter = 0
        self._runningPCB = None

    @property
    def pidCounter(self):
        return self._pidCounter
    
    @property
    def runningPCB(self):
        return self._runningPCB

    def getNewPID(self):
        self._pidCounter += 1
        return self._pidCounter

    def add(self, pcb):
        self._pcbs.append(pcb)

    def get(self, pid):
        result = None
        for pcb in self._pcbs:
            if pcb._pid == pid:
                result = pcb
                break
        return result
    
    def remove(self, pid):
        pcb = self.get(pid)
        self._pcbs.remove(pcb)

class Loader():

    def __init__(self):
        self._baseDir = 0
    
    def loadInMemory(self, program):
        oldBaseDir = self._baseDir
        progSize = len(program.instructions)
        for index in range(0, progSize):
            inst = program.instructions[index]
            HARDWARE.memory.write(index + oldBaseDir, inst)
            self._baseDir += 1
        return oldBaseDir

class Dispatcher():

    def load(self, pcb):
        HARDWARE.cpu.pc = pcb._pc
        HARDWARE.mmu.baseDir = pcb._basedir

    def save(self, pcb):
        pcb._pc = HARDWARE.cpu.pc
        HARDWARE.cpu.pc = -1

class ReadyQueue():
    def __init__(self):
        self._queue = []
    
    def isEmpty(self):
        return len(self._queue) == 0
    
    def get(self):
        return self._queue.pop(0)

    def add(self, program):
        self._queue.append(program)