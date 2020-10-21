# grupo_5

### Integrantes:

| Nombre y Apellido              |      Mail                      |     usuario Gitlab   |
| -----------------------------  | ------------------------------ | -------------------  |
| Juan Cruz Vincenti              | juancruzvincenti@gmail.com     | jcvincenti           |
| Andres Mora                     | andres.mora@alu.unq.edu.ar     | andres.mora          |




### Practica 1:
- 07/09/2020 -  Aprobado


### Practica 2:
- 07/09/2020 - Aprobado

### Practica 3:
- 30/09/2020 - Aprobado (Kernel.run())

 
### Practica 4:

 No corre el main (solo muestra la memoria)

 Me parece que mezclaron los Schedulers de Priority con SJF 

## Acotaciones:

 No esta mal lo que hacen en TimeoutInterruptionHandler, pero que pasaria si hay un único PCB  (no hay nada en la ReadyQ. solo el runningPCB). 
   Se podria mejorar ??



por que hacen esto??

```
    def remainingInstructions(self):
        return self._progSize - HARDWARE.cpu.pc if self.state == PCBState.RUNNING else self._progSize
```


