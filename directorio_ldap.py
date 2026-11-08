# directorio_ldap.py - Componente B: directorio LDAP de estudiantes (se apoya en la Practica 7)
# Usa el servidor simulado de ldap3. Para OpenLDAP real vea la Practica 7, paso 6.
from ldap3 import Server, Connection, MOCK_SYNC, OFFLINE_SLAPD_2_4
from ldap3.core.exceptions import LDAPException
import config

_servidor = Server("dir.unamba.lab", get_info=OFFLINE_SLAPD_2_4)

ESTUDIANTES = [  # (codigo = uid, nombre, apellido, clave)
    ("20201001", "Juan Perez", "Perez", "juan123"),
    ("20201002", "Maria Quispe", "Quispe", "maria123"),
    ("20201003", "Luis Huaman", "Huaman", "luis123"),
    ("20201004", "Rosa Condori", "Condori", "rosa123"),
    ("20201005", "Carlos Mamani", "Mamani", "carlos123"),
]


def dn_estudiante(codigo):
    return f"uid={codigo},{config.LDAP_ESTUDIANTES}"


def crear_directorio():
    """Construye el arbol (DIT): dc=unamba,dc=lab > ou=EPIIS > ou=Docentes / ou=Estudiantes."""
    admin = Connection(_servidor, user=config.LDAP_ADMIN_DN, password=config.LDAP_ADMIN_PW,
                       client_strategy=MOCK_SYNC)
    # En el simulador hay que crear la cuenta admin (en OpenLDAP real ya existe)
    admin.strategy.add_entry(config.LDAP_ADMIN_DN, {"objectClass": "inetOrgPerson", "cn": "admin",
                                                    "sn": "admin", "userPassword": config.LDAP_ADMIN_PW})
    admin.bind()
    base = config.LDAP_BASE
    admin.add(base, ["dcObject", "organization"], {"o": "UNAMBA", "dc": "unamba"})
    admin.add("ou=EPIIS," + base, ["organizationalUnit"], {"ou": "EPIIS"})
    admin.add("ou=Docentes,ou=EPIIS," + base, ["organizationalUnit"], {"ou": "Docentes"})
    admin.add(config.LDAP_ESTUDIANTES, ["organizationalUnit"], {"ou": "Estudiantes"})
    for codigo, nombre, apellido, clave in ESTUDIANTES:
        admin.add(dn_estudiante(codigo), ["inetOrgPerson"],
                  {"uid": codigo, "cn": nombre, "sn": apellido,
                   "mail": f"{codigo}@unamba.lab", "userPassword": clave})
    admin.unbind()


def autenticar(codigo, clave):
    """RF3: intenta un BIND con el DN del estudiante. Si LDAP lo acepta, la clave es correcta.
    La aplicacion nunca compara claves: lo decide el directorio."""
    if not codigo or not clave:
        return False, "datos incompletos"
    try:
        con = Connection(_servidor, user=dn_estudiante(codigo), password=clave,
                         client_strategy=MOCK_SYNC)
        if con.bind():
            con.unbind()
            return True, "acceso concedido"
        return False, "acceso denegado (" + con.result["description"] + ")"
    except LDAPException as e:
        return False, f"acceso denegado ({e})"


def listar_estudiantes():
    con = Connection(_servidor, user=config.LDAP_ADMIN_DN, password=config.LDAP_ADMIN_PW,
                     client_strategy=MOCK_SYNC)
    con.bind()
    con.search(config.LDAP_ESTUDIANTES, "(objectClass=inetOrgPerson)", attributes=["uid", "cn"])
    return sorted((e.entry_dn, e.cn.value) for e in con.entries)


# ---------- Prueba independiente: python directorio_ldap.py ----------
if __name__ == "__main__":
    crear_directorio()
    for dn, nombre in listar_estudiantes():
        print(" ", dn, "->", nombre)
    print("Clave correcta    :", autenticar("20201001", "juan123"))
    print("Clave incorrecta  :", autenticar("20201001", "otra"))
    print("Usuario inexistente:", autenticar("99999999", "x"))