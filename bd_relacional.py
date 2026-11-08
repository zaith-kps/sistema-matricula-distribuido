# bd_relacional.py - Componente C: base relacional MySQL 8 (se apoya en el Lab 6)
# Tablas: estudiante, curso y matricula, con claves foraneas y restricciones CHECK.
import pymysql
import config

ESQUEMA = [
    "DROP DATABASE IF EXISTS universidad_dist",
    "CREATE DATABASE universidad_dist CHARACTER SET utf8mb4",
    "USE universidad_dist",
    """CREATE TABLE estudiante (
        codigo  VARCHAR(10) PRIMARY KEY,
        nombre  VARCHAR(80) NOT NULL
    ) ENGINE=InnoDB""",
    """CREATE TABLE curso (
        codigo  VARCHAR(10) PRIMARY KEY,
        nombre  VARCHAR(80) NOT NULL,
        cupos   INT NOT NULL,
        CONSTRAINT chk_cupos CHECK (cupos >= 0)                     -- RF4: nunca negativos
    ) ENGINE=InnoDB""",
    """CREATE TABLE matricula (
        id                 INT AUTO_INCREMENT PRIMARY KEY,
        codigo_estudiante  VARCHAR(10) NOT NULL,
        codigo_curso       VARCHAR(10) NOT NULL,
        semestre           VARCHAR(7)  NOT NULL,
        nota               DECIMAL(4,1) NULL,                       -- NULL = curso en progreso
        CONSTRAINT chk_nota CHECK (nota BETWEEN 0 AND 20),          -- RF4: notas de 0 a 20
        CONSTRAINT uq_matricula UNIQUE (codigo_estudiante, codigo_curso, semestre),
        CONSTRAINT fk_mat_estudiante FOREIGN KEY (codigo_estudiante) REFERENCES estudiante(codigo),
        CONSTRAINT fk_mat_curso      FOREIGN KEY (codigo_curso)      REFERENCES curso(codigo)
    ) ENGINE=InnoDB""",
]

ESTUDIANTES = [
    ("20201001", "Juan Perez"),
    ("20201002", "Maria Quispe"),
    ("20201003", "Luis Huaman"),      # existe aqui y en LDAP, pero NO tiene historial (caso 5)
    ("20201004", "Rosa Condori"),
    ("20201005", "Carlos Mamani"),
]

CURSOS = [
    ("ISA801", "Base de Datos II", 0),
    ("ISA802", "Redes y Comunicaciones", 0),
    ("ISA902", "Sistemas Distribuidos", 3),   # tiene cupos (caso 3)
    ("ISA903", "Comercio Electronico", 0),    # sin cupos (caso 4)
]

# Notas del semestre anterior: alimentan el reporte MapReduce (caso 7)
NOTAS_2026_1 = [
    ("20201001", "ISA801", 15), ("20201001", "ISA802", 12),
    ("20201002", "ISA801", 18), ("20201002", "ISA802", 16),
    ("20201004", "ISA801", 11), ("20201004", "ISA802", 14),
    ("20201005", "ISA801", 17),
]


def conectar(con_bd=True):
    """Abre una conexion nueva. autocommit=False: nada se guarda sin COMMIT."""
    datos = dict(config.MYSQL)
    if not con_bd:
        datos.pop("database")
    return pymysql.connect(**datos, autocommit=False)


def crear_esquema_y_datos():
    """Borra y recrea la base con datos de prueba (para que la demo sea repetible)."""
    con = conectar(con_bd=False)
    with con.cursor() as cur:
        for sentencia in ESQUEMA:
            cur.execute(sentencia)
        cur.executemany("INSERT INTO estudiante VALUES (%s, %s)", ESTUDIANTES)
        cur.executemany("INSERT INTO curso VALUES (%s, %s, %s)", CURSOS)
        cur.executemany(
            "INSERT INTO matricula (codigo_estudiante, codigo_curso, semestre, nota) "
            "VALUES (%s, %s, '2026-1', %s)", NOTAS_2026_1)
    con.commit()
    con.close()


# ---------- Consultas de apoyo (para mostrar el estado antes/despues) ----------
def cupos(codigo_curso):
    con = conectar()
    with con.cursor() as cur:
        cur.execute("SELECT cupos FROM curso WHERE codigo = %s", (codigo_curso,))
        fila = cur.fetchone()
    con.close()
    return fila[0] if fila else None


def matriculas_de(codigo_estudiante, semestre):
    con = conectar()
    with con.cursor() as cur:
        cur.execute("SELECT codigo_curso FROM matricula WHERE codigo_estudiante = %s AND semestre = %s",
                    (codigo_estudiante, semestre))
        filas = [f[0] for f in cur.fetchall()]
    con.close()
    return filas


def notas():
    """Filas (curso, nota) con nota registrada: entrada del MapReduce."""
    con = conectar()
    with con.cursor() as cur:
        cur.execute("SELECT codigo_curso, nota FROM matricula WHERE nota IS NOT NULL")
        filas = cur.fetchall()
    con.close()
    return [(c, str(n)) for c, n in filas]   # str: el Decimal viaja exacto entre procesos


def promedios_sql():
    """El mismo promedio calculado por MySQL, para comparar con MapReduce (caso 7)."""
    con = conectar()
    with con.cursor() as cur:
        cur.execute("SELECT codigo_curso, ROUND(AVG(nota), 2) FROM matricula "
                    "WHERE nota IS NOT NULL GROUP BY codigo_curso ORDER BY codigo_curso")
        filas = cur.fetchall()
    con.close()
    return {c: str(p) for c, p in filas}


# ---------- Prueba independiente: python bd_relacional.py ----------
if __name__ == "__main__":
    crear_esquema_y_datos()
    print("Base 'universidad_dist' creada.")
    print("Cupos ISA902:", cupos("ISA902"), "| Cupos ISA903:", cupos("ISA903"))

    pruebas = [
        ("Cupo negativo", "UPDATE curso SET cupos = cupos - 1 WHERE codigo = 'ISA903'"),
        ("Nota 25",       "INSERT INTO matricula (codigo_estudiante, codigo_curso, semestre, nota) "
                          "VALUES ('20201003', 'ISA801', '2026-1', 25)"),
        ("Curso que no existe (FK)",
                          "INSERT INTO matricula (codigo_estudiante, codigo_curso, semestre) "
                          "VALUES ('20201001', 'XXX999', '2026-2')"),
    ]
    con = conectar()
    for titulo, sql in pruebas:
        try:
            with con.cursor() as cur:
                cur.execute(sql)
            print(f"[FALLO] {titulo}: la base lo acepto")
        except pymysql.MySQLError as e:
            print(f"[OK] {titulo}: rechazado -> error {e.args[0]}: {e.args[1]}")
        con.rollback()
    con.close()
    print("Promedios segun SQL:", promedios_sql())