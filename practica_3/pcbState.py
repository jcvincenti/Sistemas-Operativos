from enum import Enum

class PCBState(Enum):
    NEW = 'New'
    READY = "Ready"
    RUNNING = "Running"
    WAITING = "Waiting"
    TERMINATED = "Terminated"
