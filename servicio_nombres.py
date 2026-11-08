# servicio_nombres.py - Componente A: servicio de nombres TCP concurrente (Lab 7 ampliado)
# Comandos:
#   REGISTRAR <nombre> <host> <puerto>  -> OK registrado        (lo usan los servicios al arrancar)
#   BUSCAR <nombre>                     -> OK <host>:<puerto>   (lo usa el cliente, RF1)
#   LISTAR                              -> OK nombre1,nombre2,...
# Un nombre inexistente o un comando mal escrito devuelve ERROR sin caer el servidor (RF2).
import threading
import config
import red

_directorio = {}               # "paginas blancas": nombre -> (host, puerto)
_candado = threading.Lock()    # varios hilos leen/escriben el diccionario a la vez


def atender(peticion):
    partes = peticion.split()
    if not partes:
        return "ERROR comando vacio"
    comando = partes[0].upper()

    if comando == "REGISTRAR" and len(partes) == 4 and partes[3].isdigit():
        with _candado:
            _directorio[partes[1].lower()] = (partes[2], int(partes[3]))
        return f"OK registrado {partes[1].lower()}"

    if comando == "BUSCAR" and len(partes) == 2:
        with _candado:
            destino = _directorio.get(partes[1].lower())
        if destino is None:
            return "ERROR nombre no registrado"
        return f"OK {destino[0]}:{destino[1]}"

    if comando == "LISTAR" and len(partes) == 1:
        with _candado:
            return "OK " + ",".join(sorted(_directorio))

    return "ERROR comando invalido"


def iniciar():
    red.iniciar_servidor(config.HOST, config.NOMBRES_PUERTO, atender, "servicio-nombres")


# ---- Funciones de cliente: las usan los demas modulos ----
def registrar(nombre, host, puerto):
    return red.enviar(config.HOST, config.NOMBRES_PUERTO, f"REGISTRAR {nombre} {host} {puerto}")


def buscar(nombre):
    """Devuelve (host, puerto) o lanza LookupError si el nombre no existe."""
    respuesta = red.enviar(config.HOST, config.NOMBRES_PUERTO, f"BUSCAR {nombre}")
    if not respuesta.startswith("OK "):
        raise LookupError(f"'{nombre}': {respuesta}")
    host, puerto = respuesta[3:].rsplit(":", 1)
    return host, int(puerto)


# ---------- Prueba independiente: python servicio_nombres.py ----------
if __name__ == "__main__":
    iniciar()
    print(f"Servicio de nombres escuchando en {config.HOST}:{config.NOMBRES_PUERTO}")
    print(registrar("matricula", "127.0.0.1", 6002))
    print("BUSCAR matricula ->", buscar("matricula"))
    try:
        buscar("noexiste")
    except LookupError as e:
        print("BUSCAR noexiste  ->", e)
    print("Comando raro      ->", red.enviar(config.HOST, config.NOMBRES_PUERTO, "HOLA"))
    print("El servidor sigue vivo. Ctrl+C para salir.")
    import time
    try:
        while True:          # time.sleep si responde a Ctrl+C en Windows
            time.sleep(1)
    except KeyboardInterrupt:
        pass