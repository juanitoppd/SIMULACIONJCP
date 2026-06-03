from dataclasses import dataclass

@dataclass
class Servidor:
    id: int
    tiempo_ocupado: float = 0.0
    clientes_atendidos: int = 0

    def registrar_trabajo(self, duracion: float) -> None:
        self.tiempo_ocupado += duracion
        self.clientes_atendidos += 1
