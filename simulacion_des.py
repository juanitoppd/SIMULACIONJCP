import random
from typing import Dict, List, Optional

import simpy

from cliente import Cliente


class Monitor:
    def __init__(self, t_warm: float, t_stop: float, n_servers: int):
        self.t_warm = t_warm
        self.t_stop = t_stop
        self.n_servers = n_servers
        self.last_update = 0.0
        self.busy_area = 0.0
        self.queue_area = 0.0
        self.system_area = 0.0
        self.n_busy = 0
        self.n_queue = 0
        self.times = [0.0]
        self.n_system = [0.0]

    def update(self, time: float, n_busy: int, n_queue: int) -> None:
        if time < self.last_update:
            return

        interval_start = self.last_update
        interval_end = time
        if interval_end > interval_start:
            effective_start = max(interval_start, self.t_warm)
            effective_end = min(interval_end, self.t_stop)
            duration = max(0.0, effective_end - effective_start)
            self.busy_area += self.n_busy * duration
            self.queue_area += self.n_queue * duration
            self.system_area += (self.n_busy + self.n_queue) * duration

        self.n_busy = n_busy
        self.n_queue = n_queue
        self.last_update = time
        self.times.append(time)
        self.n_system.append(n_busy + n_queue)

    def finalize(self) -> None:
        self.update(self.t_stop, self.n_busy, self.n_queue)

    @property
    def utilizacion(self) -> float:
        horizon = max(1e-9, self.t_stop - self.t_warm)
        return self.busy_area / (self.n_servers * horizon)

    @property
    def promedio_en_cola(self) -> float:
        horizon = max(1e-9, self.t_stop - self.t_warm)
        return self.queue_area / horizon

    @property
    def promedio_en_sistema(self) -> float:
        horizon = max(1e-9, self.t_stop - self.t_warm)
        return self.system_area / horizon


def cliente_proceso(env: simpy.Environment,
                    cliente: Cliente,
                    recurso: simpy.Resource,
                    tasa_servicio: float,
                    registros: List[Cliente],
                    monitor: Monitor,
                    t_warm: float) -> None:
    cliente.t_llegada = env.now
    monitor.update(env.now, recurso.count, len(recurso.queue))

    with recurso.request() as req:
        yield req
        cliente.t_inicio = env.now
        servicio = random.expovariate(tasa_servicio)
        cliente.t_servicio = servicio
        monitor.update(env.now, recurso.count, len(recurso.queue))

        yield env.timeout(servicio)
        cliente.t_fin = env.now
        monitor.update(env.now, recurso.count, len(recurso.queue))

    if cliente.t_llegada >= t_warm:
        registros.append(cliente)


def generador_llegadas(env: simpy.Environment,
                       tasa_llegadas: float,
                       recurso: simpy.Resource,
                       tasa_servicio: float,
                       registros: List[Cliente],
                       monitor: Monitor,
                       t_warm: float) -> None:
    cliente_id = 0
    while True:
        intervalo = random.expovariate(tasa_llegadas)
        yield env.timeout(intervalo)
        if env.now > monitor.t_stop:
            break
        cliente_id += 1
        cliente = Cliente(id=cliente_id)
        env.process(cliente_proceso(env, cliente, recurso, tasa_servicio, registros, monitor, t_warm))


def correr_una_replica(lmbda: float,
                       mu: float,
                       c: int,
                       t_sim: float,
                       t_warm: float,
                       seed: Optional[int] = None,
                       return_trace: bool = False) -> Dict[str, object]:
    if seed is not None:
        random.seed(seed)

    tasa_llegadas = lmbda / 60.0
    tasa_servicio = mu / 60.0
    env = simpy.Environment()
    recurso = simpy.Resource(env, capacity=c)
    monitor = Monitor(t_warm=t_warm, t_stop=t_sim, n_servers=c)
    registros: List[Cliente] = []

    env.process(generador_llegadas(env, tasa_llegadas, recurso, tasa_servicio, registros, monitor, t_warm))
    env.run(until=t_sim)
    monitor.finalize()

    wq_values = [cliente.wq for cliente in registros]
    ws_values = [cliente.ws for cliente in registros]

    medias = {
        "Wq_promedio": float(sum(wq_values) / len(wq_values)) if wq_values else 0.0,
        "Ws_promedio": float(sum(ws_values) / len(ws_values)) if ws_values else 0.0,
        "Lq_promedio": monitor.promedio_en_cola,
        "L_promedio": monitor.promedio_en_sistema,
        "rho": monitor.utilizacion,
        "n_clientes": len(registros),
        "wq_values": wq_values,
        "ws_values": ws_values,
        "times": monitor.times if return_trace else [],
        "n_system_trace": monitor.n_system if return_trace else [],
    }

    return medias
