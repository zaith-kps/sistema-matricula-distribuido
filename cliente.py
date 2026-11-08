# cliente.py - Cliente del sistema. Solo conoce la direccion del servicio de nombres
# (o la descubre por DNS, bono G); todo lo demas lo encuentra con BUSCAR.
#
# Uso en otra terminal, con main.py corriendo:
#   python cliente.py buscar matricula
#   python cliente.py login 20201001 juan123
#   python cliente.py matricular 20201001 juan123 ISA902
#   python cliente.py reporte
import json
import sys
import config
import red

servidor_nombres = (config.HOST, config.NOMBRES_PUERTO)


def descubrir_por_dns():
    """Bono G: pregunta al DNS local por el registro SRV _nombres._tcp.unamba.lab"""
    import dns.resolver
    r = dns.resolver.Resolver(configure=False)
    r.nameservers = [config.HOST]
    r.port = config.DNS_PUERTO
    r.lifetime = 2          # si no hay DNS, no esperar mas de 2 segundos
    srv = r.resolve("_nombres._tcp.unamba.lab", "SRV")[0]
    ip = r.resolve(str(srv.target), "A")[0].to_text()
    global servidor_nombres
    servidor_nombres = (ip, srv.port)
    return servidor_nombres


def buscar(nombre):
    return red.enviar(*servidor_nombres, f"BUSCAR {nombre}")


def _servicio(nombre):
    respuesta = buscar(nombre)
    if not respuesta.startswith("OK "):
        raise LookupError(f"servicio '{nombre}' no disponible: {respuesta}")
    host, puerto = respuesta[3:].rsplit(":", 1)
    return host, int(puerto)


def autenticar(codigo, clave):
    return red.enviar_json(*_servicio("ldap"), {"op": "AUTH", "codigo": codigo, "clave": clave})


def matricular(codigo, clave, curso):
    return red.enviar_json(*_servicio("matricula"),
                           {"op": "MATRICULAR", "codigo": codigo, "clave": clave, "curso": curso})


def reporte():
    return red.enviar_json(*_servicio("reportes"), {"op": "PROMEDIOS"}, timeout=60)


if __name__ == "__main__":
    args = sys.argv[1:]
    comandos = {"buscar": (buscar, 1), "login": (autenticar, 2),
                "matricular": (matricular, 3), "reporte": (reporte, 0)}
    if not args or args[0] not in comandos or len(args) - 1 != comandos[args[0]][1]:
        print("Comandos: buscar <nombre> | login <codigo> <clave> | "
              "matricular <codigo> <clave> <curso> | reporte")
        sys.exit(1)
    funcion, _ = comandos[args[0]]
    resultado = funcion(*args[1:])
    print(json.dumps(resultado, indent=2, ensure_ascii=False) if isinstance(resultado, dict) else resultado)