#!/usr/bin/env python

from hardware import *
from pcbState import *
from Gantt import *
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
        if not self.kernel._scheduler.isEmpty():
            pcb = self.kernel._scheduler.getNext()
            self.loadPcb(pcb)
    
    def loadIfNoRunningPcb(self, pcb):
        runningPcb = self.kernel._pcbTable.runningPCB

        if runningPcb:
            runningPcb.updatePC()
            if self.kernel._scheduler.mustExpropiate(runningPcb, pcb):
                self.kernel._pcbTable._runningPCB = None
                self.kernel._dispatcher.save(runningPcb)
                self.addPcbToReadyQueue(runningPcb)
                self.loadPcb(pcb)
            else:
                self.addPcbToReadyQueue(pcb)
        else:
            self.loadPcb(pcb)
    
    def loadPcb(self, pcb):
        pcb.state = PCBState.RUNNING
        self.kernel._dispatcher.load(pcb)
        self.kernel._pcbTable._runningPCB = pcb
    
    def addPcbToReadyQueue(self, pcb):
        pcb.state = PCBState.READY
        self.kernel._scheduler.add(pcb)


class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        log.logger.info(" Program Finished ")
        pcb = self.kernel._pcbTable.runningPCB
        self.kernel._gantt.finish(pcb._path)
        self.kernel._pcbTable._runningPCB = None
        self.kernel.freeFrames(pcb._pageTable)
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
        newParam = irq.parameters
        path = newParam['program']
        priority = newParam['priority']
        obj = self.kernel._loader.loadInMemory(path)
        pageTable = obj['pageTable']
        program = obj['program']
        progSize = len(program.instructions)
        pid = self.kernel._pcbTable.getNewPID()
        pcb = PCB(pid, pageTable, progSize, path, priority)
        self.kernel._pcbTable.add(pcb)
        self.loadIfNoRunningPcb(pcb)

class TimeoutInterruptionHandler(AbstractInterruptionHandler):
    
    def execute(self, irq):
        if not self.kernel._scheduler.isEmpty():
            pcb = self.kernel._pcbTable.runningPCB
            self.kernel._dispatcher.save(pcb)
            self.kernel._pcbTable._runningPCB = None
            self.addPcbToReadyQueue(pcb)
            self.loadIfReadyQueueNotEmpty()
        else:
            HARDWARE.timer.reset()

class StatsInterruptionHandler(AbstractInterruptionHandler):
    def execute(self, irq):
        if self.kernel._pcbTable.getAreAllPCBsTerminated():
            self.kernel._gantt.draw()
            HARDWARE.switchOff()

# emulates the core of an Operative System
class Kernel():

    def __init__(self):
        ## setup interruption handlers
        HARDWARE.mmu.frameSize = 4
        killHandler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, killHandler)

        ioInHandler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, ioInHandler)

        ioOutHandler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, ioOutHandler)

        newHandler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, newHandler)

        timeoutHandler = TimeoutInterruptionHandler(self)
        HARDWARE.interruptVector.register(TIMEOUT_INTERRUPTION_TYPE, timeoutHandler)

        statsHandler = StatsInterruptionHandler(self)
        HARDWARE.interruptVector.register(STAT_INTERRUPTION_TYPE, statsHandler)

        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)
        self._pcbTable = PCBTable()
        self._dispatcher = Dispatcher()
        self._scheduler = None
        self._gantt = Gantt.getInstance()
        self._gantt.setKernel(self)
        self._fileSystem = FileSystem()
        self._memoryManager = MemoryManager()
        self._loader = Loader(self._memoryManager, self._fileSystem)

    @property
    def ioDeviceController(self):
        return self._ioDeviceController

    ## emulates a "system call" for programs execution
    def run(self, path, priority):
        if self._scheduler == None:
            raise Exception("--- NO SCHEDULER SETTED ---")

        self._gantt.load(path)
        dictNewParam = {'program': path, 'priority': priority}

        newIRQ = IRQ(NEW_INTERRUPTION_TYPE, dictNewParam)
        HARDWARE.interruptVector.handle(newIRQ)

        # set CPU program counter at program's first intruction
        log.logger.info("\n Executing program: {name}".format(name=path))
        log.logger.info(HARDWARE)

    def __repr__(self):
        return "Kernel "
    
    def setSchedulingStrategy(self, strategy):
        self._scheduler = strategy
    
    def freeFrames(self, frames):
        self._memoryManager.freeFrames(frames)

    def enableGantt(self, enable):
        HARDWARE.cpu.enable_stats = enable

class PCB():
    
    def __init__(self, pid, pageTable, progSize, path, priority):
        self._pid = pid
        self._pageTable = pageTable
        self._path = path
        self._state = PCBState.NEW
        self._progSize = progSize
        self._pc = 0
        self._priority = priority

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    @property
    def priority(self):
        return self._priority
    
    def remainingInternalInstructions(self):
        return self._progSize - self._pc

    def updatePC(self):
        self._pc = HARDWARE.cpu.pc

    def remainingInstructions(self):
        # metodo solo para el Gantt
        return self._progSize - HARDWARE.cpu.pc if self.state == PCBState.RUNNING else self._progSize

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

    def getAreAllPCBsTerminated(self):
        return all(pcb.state == PCBState.TERMINATED for pcb in self._pcbs)

class Loader():

    def __init__(self, memoryManager, fileSystem):
        self._baseDir = 0
        self._memoryManager = memoryManager
        self._fileSystem = fileSystem
    
    def loadInMemory(self, path):
        program = self._fileSystem.read(path)
        neccesaryPages = self.getNeccesaryPages(program)
        pageTable = self._memoryManager.allocFrames(neccesaryPages)
        paged = self.paginate(program.instructions)
        dictionary = self.assignKeys(paged, pageTable)
        
        for page in dictionary.items():
            self.loadPage(page)

        return {'pageTable': pageTable, 'program': program}

    def assignKeys(self, paged, pageTable):
        return dict(zip(pageTable, paged))

    def paginate(self, instructions):
        frameSize = HARDWARE.mmu.frameSize
        result = [instructions[i: i + frameSize] for i in range(0, len(instructions), frameSize)]
        return result

    def getNeccesaryPages(self, program):
        if(len(program.instructions)) % HARDWARE.mmu.frameSize != 0:
            return (len(program.instructions)) // HARDWARE.mmu.frameSize + 1
        return (len(program.instructions)) // HARDWARE.mmu.frameSize
            
    def loadPage(self, page):
        instructions = page[1] #El value
        self._baseDir = page[0] * HARDWARE.mmu.frameSize  #La key(frame que me devuelve el MM) * frameSize
        for i in range(len(instructions)):
            inst = instructions[i]
            HARDWARE.memory.write(self._baseDir, inst)
            self._baseDir += 1

class Dispatcher():

    def load(self, pcb):
        HARDWARE.cpu.pc = pcb._pc
        HARDWARE.timer.reset()
        HARDWARE.mmu.resetTLB()

        for pageTable in pcb._pageTable:
            HARDWARE.mmu.setPageFrame(pcb._pageTable.index(pageTable), pageTable)

    def save(self, pcb):
        pcb._pc = HARDWARE.cpu.pc
        HARDWARE.cpu.pc = -1

class FileSystem:

    def __init__(self):
        self._disk = []

    def write(self, path, program):
        process = {'path': path, 'program': program }
        self._disk.append(process)

    def read(self, path):
        result = None
        for program in self._disk:
            if program['path'] == path:
                result = program['program']
                break
        if not result:
            raise Exception	("Path invalido")
        
        return result
            
class MemoryManager():

    def __init__(self):
        self._freeFrames = self.getFrames()

    def getFrames(self):
        result = []
        totalFrames = HARDWARE.memory.size // HARDWARE.mmu.frameSize

        for i in range(totalFrames):
            result.append(i)

        return result

    def allocFrames(self, quantity):
        if len(self._freeFrames) < quantity:
            raise Exception("Frames insuficientes para cargar el proceso")
        result = []
        for i in range(quantity):
            result.append(self._freeFrames.pop(0))

        return result

    def freeFrames(self, frames):
        self._freeFrames.extend(frames)