# bd_documental.py - Componente D: historial academico en una base documental
# (se apoya en el Lab 6 y la Practica 10). mongomock = MongoDB simulado en memoria.
# Para usar MongoDB real: reemplace mongomock.MongoClient() por pymongo.MongoClient("mongodb://localhost:27017")
import mongomock

_cliente = mongomock.MongoClient()
db = _cliente["universidad_dist"]

# Modelo INCRUSTADO: cada estudiante es UN documento que contiene su lista de cursos.
# Leer el historial completo = 1 sola lectura, sin JOIN.
HISTORIALES = [
    {"codigo": "20201001", "nombre": "Juan Perez", "cursos": [
        {"codigo": "ISA801", "semestre": "2026-1", "nota": 15},
        {"codigo": "ISA802", "semestre": "2026-1", "nota": 12}]},
    {"codigo": "20201002", "nombre": "Maria Quispe", "cursos": [
        {"codigo": "ISA801", "semestre": "2026-1", "nota": 18},
        {"codigo": "ISA802", "semestre": "2026-1", "nota": 16}]},
    {"codigo": "20201004", "nombre": "Rosa Condori", "cursos": [
        {"codigo": "ISA801", "semestre": "2026-1", "nota": 11},
        {"codigo": "ISA802", "semestre": "2026-1", "nota": 14}]},
    {"codigo": "20201005", "nombre": "Carlos Mamani", "cursos": [
        {"codigo": "ISA801", "semestre": "2026-1", "nota": 17}]},
    # 20201003 (Luis Huaman) NO tiene historial a proposito: caso de prueba 5
]


def crear_datos():
    db.historial.drop()
    db.historial.insert_many([dict(h) for h in HISTORIALES])
    db.historial.create_index("codigo", unique=True)


def historial(codigo_estudiante):
    return db.historial.find_one({"codigo": codigo_estudiante}, {"_id": 0})


def cursos_en(codigo_estudiante, semestre):
    h = historial(codigo_estudiante)
    if h is None:
        return None
    return [c["codigo"] for c in h["cursos"] if c["semestre"] == semestre]


# ---------- Prueba independiente: python bd_documental.py ----------
if __name__ == "__main__":
    crear_datos()
    print("Historial de 20201002:", historial("20201002"))
    print("Historial de 20201003:", historial("20201003"), "(no existe)")
    # Consulta sobre el arreglo incrustado ($elemMatch, como en el Lab 6)
    buenos = db.historial.find({"cursos": {"$elemMatch": {"codigo": "ISA801", "nota": {"$gte": 15}}}})
    print("ISA801 con nota >= 15:", [e["nombre"] for e in buenos])
    # Agregacion: promedio por curso (para comparar con SQL)
    pipeline = [{"$unwind": "$cursos"},
                {"$group": {"_id": "$cursos.codigo", "promedio": {"$avg": "$cursos.nota"}}},
                {"$sort": {"_id": 1}}]
    for fila in db.historial.aggregate(pipeline):
        print("Promedio", fila["_id"], "=", fila["promedio"])