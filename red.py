# red.py - Utilidades de red compartidas (sockets TCP, como en el Lab 7).
# Protocolo: el cliente envia UNA linea de texto terminada en "\n" y recibe UNA linea de respuesta.
import json
import socket
import threading


def iniciar_servidor(host, puerto, atender, nombre="servidor"):
    """Crea un servidor TCP concurrente: un hilo por conexion.
    'atender' es una funcion que recibe la linea pedida (str) y devuelve la respuesta (str).
    El bind se hace aqui mismo, asi que al volver el puerto ya esta escuchando."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, puerto))
    srv.listen(20)

    def atender_conexion(conn):
        with conn:
            try:
                peticion = _leer_linea(conn)
                respuesta = atender(peticion)
            except Exception as e:                      # RF2: un error nunca tumba el servidor
                respuesta = f"ERROR interno: {e}"
            conn.sendall((respuesta + "\n").encode("utf-8"))

    def bucle():
        while True:
            conn, _ = srv.accept()
            threading.Thread(target=atender_conexion, args=(conn,), daemon=True).start()

    threading.Thread(target=bucle, name=nombre, daemon=True).start()
    return srv


def enviar(host, puerto, linea, timeout=10):
    """Envia una linea de texto y devuelve la linea de respuesta."""
    with socket.create_connection((host, puerto), timeout=timeout) as s:
        s.sendall((linea + "\n").encode("utf-8"))
        return _leer_linea(s)


def enviar_json(host, puerto, mensaje, timeout=30):
    """Igual que enviar(), pero con diccionarios (JSON) en ambos sentidos."""
    return json.loads(enviar(host, puerto, json.dumps(mensaje), timeout))


def _leer_linea(conn):
    datos = b""
    while not datos.endswith(b"\n"):
        trozo = conn.recv(4096)
        if not trozo:
            break
        datos += trozo
    return datos.decode("utf-8").strip()