from tabulate import tabulate

class Gantt():
    __instance = None

    @staticmethod
    def getInstance():
        if Gantt.__instance == None:
            Gantt.__instance = Gantt()
        return Gantt.__instance

    def __init__(self):
        self._kernel = None
        self._programs = []
        self._finished = []
        self._table = {
            "Proceso": self._programs
        }
    
    def tick(self, tickNbr):
        column = []
        currentPCB = self._kernel._pcbTable.runningPCB
        if (currentPCB):
            for programName in self._programs:
                if (programName == currentPCB._path):
                    column.append(currentPCB.remainingInstructions())
                elif (programName in self._finished):
                    column.append(" ")
                else:
                    column.append(".")
            self._table[str(tickNbr)] = column

    def load(self, programName):
        self._programs.append(programName)
    
    def finish(self, programName):
        self._finished.append(programName)
    
    def setKernel(self, kernel):
        self._kernel = kernel

    def draw(self):
        print(tabulate(self._table, headers="keys", tablefmt='pretty'))