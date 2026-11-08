# main.py - Punto de entrada unico:  python main.py
# 1) prepara los datos  2) levanta todos los servicios  3) ejecuta los 7 casos de prueba
# 4) deja los servicios activos para usar cliente.py desde otra terminal (Ctrl+C para salir)
#
# Opciones:  --pausa  espera Enter entre casos (util en la sustentacion)
#            --salir  termina al acabar los casos
import os
import sys
import threading
import time
import config
import bd_relacional
import bd_documental
import directorio_ldap
import servicio_nombres
import servicios
import cliente

PAUSA = "--pausa" in sys.argv


def titulo(n, texto):
    if PAUSA and n > 1:
        input("\n[Enter] para continuar...")
    print("\n" + "=" * 70 + f"\nCASO {n}: {texto}\n" + "=" * 70)


def estado(estudiante, curso):
    """Foto del estado en AMBAS bases, para comparar antes y despues."""
    return {"cupos": bd_relacional.cupos(curso),
            "mysql": bd_relacional.matriculas_de(estudiante, config.SEMESTRE_ACTUAL),
            "historial": bd_documental.cursos_en(estudiante, config.SEMESTRE_ACTUAL)}


def caso_matricula(n, texto, codigo, clave, curso):
    titulo(n, texto)
    antes = estado(codigo, curso)
    r = cliente.matricular(codigo, clave, curso)
    despues = estado(codigo, curso)
    print(f"Matricular {codigo} en {curso} -> {r['decision']} ({r.get('tx', '-')})")
    for v in r.get("votos", []):
        print(f"   {v['participante']:9} vota {v['voto']:2} - {v['motivo']}")
    print(f"   Cupos {curso}        : {antes['cupos']} -> {despues['cupos']}")
    print(f"   Matriculas MySQL {config.SEMESTRE_ACTUAL}: {antes['mysql']} -> {despues['mysql']}")
    print(f"   Historial {config.SEMESTRE_ACTUAL}     : {antes['historial']} -> {despues['historial']}")


def demo():
    titulo(1, "Buscar servicios en el servicio de nombres")
    try:
        print("DNS (bono): servicio de nombres en", cliente.descubrir_por_dns(), "via registro SRV")
    except Exception:
        print("DNS (bono) no activo: se usa la direccion de config.py", cliente.servidor_nombres)
    print("BUSCAR matricula ->", cliente.buscar("matricula"))
    print("BUSCAR noexiste  ->", cliente.buscar("noexiste"))
    print("LISTAR           ->", servicio_nombres.red.enviar(*cliente.servidor_nombres, "LISTAR"))
    respuestas = []
    hilos = [threading.Thread(target=lambda n=n: respuestas.append((n, cliente.buscar(n))))
             for n in ["ldap", "matricula", "reportes", "noexiste", "ldap"]]
    for h in hilos: h.start()
    for h in hilos: h.join()
    print(f"Concurrencia: {len(respuestas)} clientes simultaneos atendidos ->", respuestas)

    titulo(2, "Autenticacion con LDAP")
    print("20201001 / juan123 (correcta)  ->", cliente.autenticar("20201001", "juan123"))
    print("20201001 / otra    (erronea)   ->", cliente.autenticar("20201001", "otra"))
    print("99999999 / x       (no existe) ->", cliente.autenticar("99999999", "x"))
    r = cliente.matricular("20201001", "otra", "ISA902")
    print("Matricular con clave erronea   ->", r["decision"], "-", r["motivo"])

    caso_matricula(3, "Matricula en un curso con cupos", "20201001", "juan123", "ISA902")
    caso_matricula(4, "Matricula en un curso SIN cupos", "20201002", "maria123", "ISA903")
    caso_matricula(5, "Estudiante SIN historial documental", "20201003", "luis123", "ISA902")

    titulo(6, f"Registro del coordinador ({config.LOG_COORDINADOR})")
    print(open(config.LOG_COORDINADOR, encoding="utf-8").read().rstrip())

    titulo(7, "Reporte de promedios con MapReduce vs SQL")
    r = cliente.reporte()
    print(f"Filas: {r['filas']} | procesos: {r['procesos']}")
    print(f"{'Curso':8} {'MapReduce':>10} {'SQL':>8}")
    for curso in sorted(r["sql"]):
        print(f"{curso:8} {r['mapreduce'].get(curso, '-'):>10} {r['sql'][curso]:>8}")
    print("Coinciden:", "SI" if r["coinciden"] else "NO")


def main():
    print("Preparando datos (MySQL, historial, LDAP)...")
    bd_relacional.crear_esquema_y_datos()
    bd_documental.crear_datos()
    directorio_ldap.crear_directorio()
    if os.path.exists(config.LOG_COORDINADOR):
        os.remove(config.LOG_COORDINADOR)

    print("Levantando servicios...")
    servicio_nombres.iniciar()
    print(f"  [nombres] escuchando en {config.HOST}:{config.NOMBRES_PUERTO}")
    try:
        import dns_local
        dns_local.iniciar()
        print(f"  [dns] zona unamba.lab en {config.HOST}:{config.DNS_PUERTO}/UDP (bono)")
    except Exception as e:
        print("  [dns] no se inicio (es opcional):", e)
    servicios.iniciar_servicios()

    demo()

    if "--salir" not in sys.argv:
        print("\nServicios activos. Pruebe en otra terminal:  python cliente.py matricular 20201002 maria123 ISA902")
        print("Ctrl+C para terminar.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Fin.")


if __name__ == "__main__":   # obligatorio en Windows por multiprocessing (MapReduce)
    main()