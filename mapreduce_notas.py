# mapreduce_notas.py - Componente F: promedio de notas por curso con MapReduce (Practica 11)
# Las funciones deben estar al nivel del modulo: en Windows cada proceso hijo importa este archivo.
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from multiprocessing import Pool


def mapear(fragmento):
    """MAP: [(curso, nota), ...] -> [(curso, (nota, 1)), ...]"""
    return [(curso, (Decimal(nota), 1)) for curso, nota in fragmento]


def barajar(salidas_map):
    """SHUFFLE: agrupa todos los pares por clave (curso)."""
    grupos = defaultdict(list)
    for pares in salidas_map:
        for curso, valor in pares:
            grupos[curso].append(valor)
    return grupos


def reducir(item):
    """REDUCE: (curso, [(nota, 1), ...]) -> (curso, promedio)"""
    curso, valores = item
    suma = sum(n for n, _ in valores)
    cantidad = sum(c for _, c in valores)
    promedio = (suma / cantidad).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # igual que ROUND de MySQL
    return curso, str(promedio)


def dividir(filas, partes):
    """Reparte las filas en 'partes' fragmentos, uno por proceso mapper."""
    return [filas[i::partes] for i in range(partes)]


def promedios_mapreduce(filas, procesos=2):
    with Pool(processes=procesos) as pool:
        salidas_map = pool.map(mapear, dividir(filas, procesos))      # MAP en paralelo
        grupos = barajar(salidas_map)                                  # SHUFFLE
        resultado = pool.map(reducir, sorted(grupos.items()))          # REDUCE en paralelo
    return dict(resultado)


# ---------- Prueba independiente: python mapreduce_notas.py ----------
if __name__ == "__main__":
    import bd_relacional
    filas = bd_relacional.notas()
    print("Filas leidas de MySQL:", filas)
    print("MapReduce:", promedios_mapreduce(filas, 2))
    print("SQL      :", bd_relacional.promedios_sql())