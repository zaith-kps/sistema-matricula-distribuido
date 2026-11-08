# servicios.py - Los tres servicios de red del sistema. Al arrancar, cada uno se
# registra en el servicio de nombres (RF1). Hablan JSON sobre TCP (ver red.py).
import json
import config
import red
import servicio_nombres
import directorio_ldap
import bd_relacional
import mapreduce_notas
from coordinador import Coordinador
from participantes import ParticipanteRelacional, ParticipanteDocumental

coordinador = Coordinador([ParticipanteRelacional(), ParticipanteDocumental()])


def _json(funcion):
    """Convierte una funcion dict->dict en un manejador linea->linea, con errores controlados."""
    def manejador(linea):
        try:
            mensaje = json.loads(linea)
        except json.JSONDecodeError:
            return json.dumps({"ok": False, "motivo": "mensaje no es JSON"})
        try:
            return json.dumps(funcion(mensaje))
        except Exception as e:
            return json.dumps({"ok": False, "motivo": f"error interno: {e}"})
    return manejador


# ---------------- Servicio "ldap": autenticacion (componente B) ----------------
def servicio_ldap(m):
    if m.get("op") != "AUTH":
        return {"ok": False, "motivo": "operacion desconocida"}
    ok, motivo = directorio_ldap.autenticar(m.get("codigo"), m.get("clave"))
    return {"ok": ok, "motivo": motivo}


# ---------------- Servicio "matricula": autentica y lanza el 2PC (componente E) ----------------
def servicio_matricula(m):
    if m.get("op") != "MATRICULAR":
        return {"ok": False, "motivo": "operacion desconocida"}
    # RF3: el propio servicio verifica con LDAP (no confia en el cliente).
    # Tambien descubre al servicio ldap por nombre, no por un puerto fijo.
    host, puerto = servicio_nombres.buscar("ldap")
    auth = red.enviar_json(host, puerto, {"op": "AUTH", "codigo": m.get("codigo"), "clave": m.get("clave")})
    if not auth["ok"]:
        return {"ok": False, "decision": "DENEGADO", "motivo": auth["motivo"]}
    op = {"estudiante": m["codigo"], "curso": m.get("curso", "").upper(), "semestre": config.SEMESTRE_ACTUAL}
    resultado = coordinador.ejecutar(op)
    resultado["ok"] = resultado["decision"] == "COMMIT"
    return resultado


# ---------------- Servicio "reportes": promedios con MapReduce (componente F) ----------------
def servicio_reportes(m):
    if m.get("op") != "PROMEDIOS":
        return {"ok": False, "motivo": "operacion desconocida"}
    filas = bd_relacional.notas()
    mr = mapreduce_notas.promedios_mapreduce(filas, config.PROCESOS_MAPREDUCE)
    sql = bd_relacional.promedios_sql()
    return {"ok": True, "mapreduce": mr, "sql": sql, "coinciden": mr == sql,
            "procesos": config.PROCESOS_MAPREDUCE, "filas": len(filas)}


SERVICIOS = {"ldap": servicio_ldap, "matricula": servicio_matricula, "reportes": servicio_reportes}


def iniciar_servicios():
    for nombre, funcion in SERVICIOS.items():
        puerto = config.PUERTOS_SERVICIOS[nombre]
        red.iniciar_servidor(config.HOST, puerto, _json(funcion), f"servicio-{nombre}")
        print(f"  [{nombre}] escuchando en {config.HOST}:{puerto} ->",
              servicio_nombres.registrar(nombre, config.HOST, puerto))