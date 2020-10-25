from hardware import *
from so import *
import log
from Strategy import *


##
##  MAIN 
##
if __name__ == '__main__':
    log.setupLogger()
    log.logger.info('Starting emulator')

    ## setup our hardware and set memory size to 25 "cells"
    HARDWARE.setup(25)

    ## Switch on computer
    HARDWARE.switchOn()

    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    kernel = Kernel()

    # kernel.setSchedulingStrategy(FirstComeFirstServed())
    # kernel.setSchedulingStrategy(NoPreemtiveShortestJobFirst())
    # kernel.setSchedulingStrategy(PreemtiveShortestJobFirst())
    # kernel.setSchedulingStrategy(RoundRobin())
    # kernel.setSchedulingStrategy(PriorityExpropiativo())
    kernel.setSchedulingStrategy(PriorityNoExpropiativo())

    # Ahora vamos a intentar ejecutar 3 programas a la vez
    ##################
    prg1 = Program("prg1.exe", [ASM.CPU(6)])
    prg2 = Program("prg2.exe", [ASM.CPU(4)])
    prg3 = Program("prg3.exe", [ASM.CPU(3)])
    prg4 = Program("prg4.exe", [ASM.CPU(2)])

    # execute all programs "concurrently"
    kernel.run(prg1, 5)
    sleep(1)
    kernel.run(prg2, 2)
    sleep(1)
    kernel.run(prg3, 3)
    sleep(1)
    kernel.run(prg4, 1)
