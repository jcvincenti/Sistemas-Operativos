# Práctica 2

1. Entender las clases __InterruptVector()__ y __Clock()__ y poder explicar como funcionan.
    - __Clock():__ La clase clock sigue el patrón observer. Cada hardware creado, se suscribe al clock por medio del `addSubscriber`. Esa suscripción lo que hace es agregar a dicho hardware a un array que posee el clock. Una vez encendido el hardware por medio del `switchOn`, se setea la variable running en `true` y el clock recibe el `start`. Dicho `start`, entre otras cosas, comienza a recorrer el array de suscriptores (siempre que el running siga seteado en `true`), enviándoles el mensaje `tick`. En caso de que el hardware reciba el mensaje `switchOff`, la variable running es seteada en `false`.
    
    - __InterruptVector():__ La clase InterruptVector posee un array asociativo, en el cual se encuentra como key el tipo de interrupción y como value el handler correspondiente a ese tipo. Para agregar los tipos de handlers se utiliza el mensaje `register` y por medio del mensaje `handle`, cuando se recibe un interruption request, se busca el handler correspondiente y se le envía el mensaje `execute`.

2. Explicar cómo se llegan a ejecutar __KillInterruptionHandler.execute()__
    
    - __KillInterruptionHandler.execute():__ El mensaje `execute` del KillInterruptionHandler se envía desde el CPU una vez que se llega a la instrucción `exit`. En cada uno de los ticks enviados por el clock, el CPU realiza el `fetch - decode - execute`. En el `execute` del cpu, se evalua la instrucción actual y en caso de ser exit, se envía un IRQ (con el tipo kill), el `InterruptVector` busca al handler correspondiente al tipo del IRQ y ejecuta el método `execute`.