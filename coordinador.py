# coordinador.py - Componente E: coordinador del protocolo Two-Phase Commit (2PC)
# Se apoya en la Practica 9 (2PC) y en el Lab 9 (escribir el log ANTES de actuar).
import itertools
import os
import threading
from datetime import datetime
import config


class Coordinador:
    def __init__(self, participantes, archivo_log=config.LOG_COORDINADOR):
        self.participantes = participantes
        self.archivo_log = archivo_log
        self._contador = itertools.count(1)
        self._candado = threading.Lock()

    def nuevo_id(self):
        with self._candado:
            return f"TX-{datetime.now():%H%M%S}-{next(self._contador):03d}"

    def ejecutar(self, op):
        tx = self.nuevo_id()

        # ---------------- FASE 1: votacion (PREPARE) ----------------
        votos = []
        for p in self.participantes:
            try:
                voto, motivo = p.preparar(tx, op)
            except Exception as e:                 # un participante que falla cuenta como NO
                voto, motivo = "NO", f"no responde ({e})"
            votos.append((p.nombre, voto, motivo))

        decision = "COMMIT" if all(v == "SI" for _, v, _ in votos) else "ABORT"

        # ---- RF7: la decision se escribe en disco ANTES de ordenarla ----
        self._registrar(tx, decision, op, votos)

        # ---------------- FASE 2: decision (COMMIT / ABORT) ----------------
        for p in self.participantes:
            if decision == "COMMIT":
                p.confirmar(tx)
            else:
                p.abortar(tx)

        return {"tx": tx, "decision": decision,
                "votos": [{"participante": n, "voto": v, "motivo": m} for n, v, m in votos]}

    def _registrar(self, tx, decision, op, votos):
        detalle = ", ".join(f"{n}={v}" for n, v, _ in votos)
        linea = (f"{datetime.now():%Y-%m-%d %H:%M:%S} | {tx} | {decision:6} | "
                 f"{op['estudiante']} -> {op['curso']} | votos: {detalle}\n")
        with self._candado:
            with open(self.archivo_log, "a", encoding="utf-8") as f:
                f.write(linea)
                f.flush()
                os.fsync(f.fileno())   # obliga al sistema operativo a escribir en disco ya


# ---------- Prueba independiente (sin red): python coordinador.py ----------
if __name__ == "__main__":
    import bd_relacional, bd_documental
    from participantes import ParticipanteRelacional, ParticipanteDocumental

    bd_relacional.crear_esquema_y_datos()
    bd_documental.crear_datos()
    if os.path.exists(config.LOG_COORDINADOR):
        os.remove(config.LOG_COORDINADOR)
    coord = Coordinador([ParticipanteRelacional(), ParticipanteDocumental()])

    casos = [("Curso con cupos", "20201001", "ISA902"),
             ("Curso sin cupos", "20201002", "ISA903"),
             ("Estudiante sin historial", "20201003", "ISA902")]
    for titulo, est, curso in casos:
        antes = bd_relacional.cupos(curso)
        r = coord.ejecutar({"estudiante": est, "curso": curso, "semestre": config.SEMESTRE_ACTUAL})
        print(f"\n{titulo}: {r['decision']}  (cupos {curso}: {antes} -> {bd_relacional.cupos(curso)})")
        for v in r["votos"]:
            print(f"   {v['participante']:9} vota {v['voto']:2} - {v['motivo']}")
    print("\n--- coordinador.log ---")
    print(open(config.LOG_COORDINADOR, encoding="utf-8").read())