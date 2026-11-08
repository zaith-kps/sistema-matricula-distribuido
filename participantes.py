# participantes.py - Los dos participantes del 2PC (se apoya en el Lab 8 y la Practica 9).
# Cada participante sabe hacer 3 cosas:
#   preparar(tx, op)  -> Fase 1: hace el trabajo SIN confirmarlo y vota ("SI", motivo) o ("NO", motivo)
#   confirmar(tx)     -> Fase 2: hace permanente lo preparado
#   abortar(tx)       -> Fase 2: deshace lo preparado
# op = {"estudiante": "20201001", "curso": "ISA902", "semestre": "2026-2"}
import threading
import pymysql
import bd_relacional
import bd_documental


class ParticipanteRelacional:
    """MySQL: descuenta 1 cupo e inserta la matricula dentro de una transaccion ABIERTA.
    La transaccion queda pendiente (con el bloqueo de la fila del curso) hasta la fase 2."""
    nombre = "MySQL"

    def __init__(self):
        self._abiertas = {}            # tx -> conexion con la transaccion sin confirmar
        self._candado = threading.Lock()

    def preparar(self, tx, op):
        con = bd_relacional.conectar()
        try:
            con.begin()
            with con.cursor() as cur:
                cur.execute("UPDATE curso SET cupos = cupos - 1 WHERE codigo = %s", (op["curso"],))
                if cur.rowcount != 1:                    # UPDATE de 0 filas NO da error: se revisa
                    raise ValueError(f"el curso {op['curso']} no existe")
                cur.execute("INSERT INTO matricula (codigo_estudiante, codigo_curso, semestre) "
                            "VALUES (%s, %s, %s)", (op["estudiante"], op["curso"], op["semestre"]))
        except pymysql.MySQLError as e:
            con.rollback(); con.close()
            if e.args[0] == 3819:
                return "NO", "sin cupos (CHECK cupos >= 0)"
            if e.args[0] == 1062:
                return "NO", "ya matriculado en ese curso"
            return "NO", f"error MySQL {e.args[0]}"
        except ValueError as e:
            con.rollback(); con.close()
            return "NO", str(e)
        with self._candado:
            self._abiertas[tx] = con
        return "SI", "cupo descontado (sin confirmar)"

    def confirmar(self, tx):
        con = self._sacar(tx)
        if con:
            con.commit(); con.close()

    def abortar(self, tx):
        con = self._sacar(tx)
        if con:
            con.rollback(); con.close()          # aqui se REVIERTE el cupo descontado

    def _sacar(self, tx):
        with self._candado:
            return self._abiertas.pop(tx, None)


class ParticipanteDocumental:
    """Historial: mongomock no tiene transacciones, asi que la fase 1 solo VALIDA y deja
    la escritura pendiente en memoria; el $push real se hace recien en la fase 2."""
    nombre = "Historial"

    def __init__(self):
        self._pendientes = {}          # tx -> (codigo_estudiante, curso_a_agregar)
        self._candado = threading.Lock()

    def preparar(self, tx, op):
        h = bd_documental.historial(op["estudiante"])
        if h is None:
            return "NO", "el estudiante no tiene historial"
        if any(c["codigo"] == op["curso"] and c["semestre"] == op["semestre"] for c in h["cursos"]):
            return "NO", "el curso ya esta en el historial"
        with self._candado:
            self._pendientes[tx] = (op["estudiante"],
                                    {"codigo": op["curso"], "semestre": op["semestre"], "nota": None})
        return "SI", "historial listo para actualizar"

    def confirmar(self, tx):
        with self._candado:
            pendiente = self._pendientes.pop(tx, None)
        if pendiente:
            codigo, curso = pendiente
            bd_documental.db.historial.update_one({"codigo": codigo}, {"$push": {"cursos": curso}})

    def abortar(self, tx):
        with self._candado:
            self._pendientes.pop(tx, None)       # se descarta: nunca se escribio nada