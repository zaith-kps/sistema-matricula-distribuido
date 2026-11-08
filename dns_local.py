# dns_local.py - Componente G (opcional, bono): zona DNS local unamba.lab (Practica 8 y Lab 10)
# El cliente encuentra al servicio de nombres con un registro SRV, igual que los equipos
# Windows encuentran al controlador de dominio de Active Directory.
from dnslib import RR, QTYPE, A, SRV, TXT, RCODE
from dnslib.server import DNSServer, BaseResolver, DNSLogger
import config

Z = config.DNS_ZONA   # "unamba.lab."
ZONA = {
    ("nombres." + Z, QTYPE.A): A(config.HOST),
    ("_nombres._tcp." + Z, QTYPE.SRV): SRV(priority=0, weight=0, port=config.NOMBRES_PUERTO,
                                           target="nombres." + Z),
    (Z, QTYPE.TXT): TXT("Sistema de matricula distribuido ISA902"),
}
NOMBRES_EXISTENTES = {nombre for nombre, _ in ZONA}


class Resolver(BaseResolver):
    def resolve(self, request, handler):
        reply = request.reply()
        nombre, tipo = str(request.q.qname).lower(), request.q.qtype
        if (nombre, tipo) in ZONA:
            reply.add_answer(RR(request.q.qname, tipo, rdata=ZONA[(nombre, tipo)], ttl=300))
        elif nombre not in NOMBRES_EXISTENTES:
            reply.header.rcode = RCODE.NXDOMAIN   # el nombre no existe
        # si el nombre existe pero no tiene ese tipo: NOERROR sin respuestas (como un DNS real)
        return reply


def iniciar():
    silencioso = DNSLogger(log="-request,-reply,-truncated,-error,-recv,-send,-data")
    srv = DNSServer(Resolver(), port=config.DNS_PUERTO, address=config.HOST, logger=silencioso)
    srv.start_thread()
    return srv


if __name__ == "__main__":
    import time
    iniciar()
    print(f"DNS escuchando en {config.HOST}:{config.DNS_PUERTO} (UDP). Ctrl+C para salir.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass