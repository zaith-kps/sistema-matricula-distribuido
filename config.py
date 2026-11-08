# config.py - Configuracion central del sistema de matricula distribuido.
# Si algo cambia de lugar (puerto, clave de MySQL...), se cambia SOLO aqui.

HOST = "127.0.0.1"

# A. Servicio de nombres (Lab 7): es la unica direccion "fija" del sistema.
NOMBRES_PUERTO = 5050

# Puertos en los que escucha cada servicio. El cliente NO los conoce:
# los descubre preguntando al servicio de nombres (RF1).
PUERTOS_SERVICIOS = {
    "ldap": 6001,
    "matricula": 6002,
    "reportes": 6003,
}

# C. Base relacional MySQL 8 (Lab 6). Cambie la clave por la suya.
MYSQL = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "matricula",
    "password": "matricula123",
    "database": "universidad_dist",
}

# B. Directorio LDAP (Practica 7)
LDAP_BASE = "dc=unamba,dc=lab"
LDAP_ESTUDIANTES = "ou=Estudiantes,ou=EPIIS," + LDAP_BASE
LDAP_ADMIN_DN = "cn=admin," + LDAP_BASE
LDAP_ADMIN_PW = "admin123"

# E. Registro (log) del coordinador 2PC (Lab 9)
LOG_COORDINADOR = "coordinador.log"

# Semestre en curso para las nuevas matriculas
SEMESTRE_ACTUAL = "2026-2"

# F. Numero de procesos para MapReduce (minimo 2, RF8)
PROCESOS_MAPREDUCE = 2

# G. DNS local (bono). Puerto 5354: el 5353 lo usa mDNS en Windows.
DNS_PUERTO = 5354
DNS_ZONA = "unamba.lab."