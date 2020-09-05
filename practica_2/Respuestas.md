# Práctica 2

1. Entender las clases __InterruptVector()__ y __Clock()__ y poder explicar como funcionan.
    - __Clock():__ La clase clock sigue el patrón observer. Cada hardware creado, se suscribe al clock por     medio del `addSubscriber`. Esa suscripción lo que hace es agregar a dicho hardware a un array que posee el clock. Una vez encendido el hardware por medio del `switchOn`, se setea la variable running en `true` y el clock recibe el `start`. Dicho `start`, entre otras cosas, comienza a recorrer el array de suscriptores (siempre que el running siga seteado en `true`), enviándoles el método `tick`. En caso de que el hardware reciba el mensaje `switchOff`, la variable running es seteada en `false`.
    
    - __InterruptVector():__

2. Explicar cómo se llegan a ejecutar __KillInterruptionHandler.execute()__
    
    - __KillInterruptionHandler.execute():__