from dataclasses import dataclass

@dataclass
class Cliente:
    id: int
    tipo: str = "normal"
    prioridad: str = "normal"
    t_llegada: float = 0.0
    t_inicio: float = 0.0
    t_fin: float = 0.0
    t_servicio: float = 0.0

    @property
    def wq(self) -> float:
        return max(0.0, self.t_inicio - self.t_llegada)

    @property
    def ws(self) -> float:
        return max(0.0, self.t_fin - self.t_llegada)

    def registrar_inicio(self, t_inicio: float) -> None:
        self.t_inicio = t_inicio

    def registrar_fin(self, t_fin: float) -> None:
        self.t_fin = t_fin

    def registrar_servicio(self, t_servicio: float) -> None:
        self.t_servicio = t_servicio
