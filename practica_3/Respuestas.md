- __1:__ Describir como funciona el __MMU__ y que datos necesitamos para correr un proceso

El __MMU__ es el intermediario entre la CPU y la memoria. Es quien va a servir para acceder a las instrucciones del programa en memoria. A diferencia de las prácticas anteriores, ahora la CPU delega el `fetch` en el MMU. Cuando el MMU hace el `fetch`, toma su dirección base que tenga cargada, le suma la dirección lógica (el valor del pc que le pasa la cpu) y devuelve la dirección física. En el caso de que la dirección lógica sea mayor al límite, el MMU lanza una excepción.

- __2:__ Entender las clases __IoDeviceController__, __PrinterIODevice__ y poder explicar como funcionan

El __IoDeviceController__ es el encargado de "manejar" el device, encolando los pedidos para ir sirviéndolos a medida que el dispositivo se libere. Para ello, tiene una cola de espera, la cual la va llenando el kernel cuando llama al método `runOperation`, pasándole como parámetro el __pcb__ y la __operación__. Si la cola no está vacía y el device está libre, se ejecuta dicha operación.
La clase __PrinterIODevice__ emula una impresora, la cual se compone por un id, un time y un estado representado por un booleano para saber si está ocupado o no. Cuando el controller envía la instrucción de ejecución, si el dispositivo está ocupado lanza una excepción, y sino, se setea el flag en true de "ocupado" y la ejecuta.

- __3:__ Explicar cómo se llegan a ejecutar __IoInInterruptionHandler.execute()__ y  __IoOutInterruptionHandler.execute()__

Cuando la CPU procesa una instrucción de I/O, genera una interrupción de __I/O in__ y se la envía al vector de interrupciones, el cual handlea esta interrupción y la manda a ejecutar.
__I/O out__ también llega a través del vector de interrupciones, pero en cambio lo envía el dispositivo de I/O una vez terminó de procesar la instrucción que tenía a cargo. 