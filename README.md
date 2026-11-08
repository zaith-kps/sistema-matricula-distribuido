# Sistema de Matrícula Distribuido — Proyecto Final Unidad II (ISA902)

Prototipo de matrícula que integra servicio de nombres, LDAP, MySQL, base documental,
confirmación en dos fases (2PC) y MapReduce. Corre en una sola PC, con cada servicio en
su propio hilo y comunicándose por TCP como si estuvieran en máquinas distintas.

## Requisitos
- Python 3.10 o superior
- MySQL 8 (Workbench para ejecutar el script de usuario)

## Instalación (Windows, PowerShell)
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
En MySQL Workbench, conectado como `root`, ejecute una vez `00_crear_usuario.sql`.
Si cambia la clave, actualícela en `config.py`.

## Ejecución (un solo comando)
```powershell
python main.py            # prepara datos, levanta servicios y ejecuta los 7 casos
python main.py --pausa    # espera Enter entre casos (sustentación)
```
Con `main.py` corriendo, en otra terminal:
```powershell
python cliente.py buscar matricula
python cliente.py login 20201001 juan123
python cliente.py matricular 20201002 maria123 ISA902
python cliente.py reporte
```

## Componentes
| Componente | Archivo | Laboratorio base |
|---|---|---|
| A. Servicio de nombres TCP | `servicio_nombres.py`, `red.py` | Lab 7 |
| B. Directorio LDAP | `directorio_ldap.py` | Práctica 7 |
| C. Base relacional | `bd_relacional.py` | Lab 6 |
| D. Base documental | `bd_documental.py` | Lab 6, Práctica 10 |
| E. Transacción 2PC + registro | `participantes.py`, `coordinador.py` | Lab 8, Práctica 9, Lab 9 |
| F. Reporte MapReduce | `mapreduce_notas.py` | Práctica 11 |
| G. DNS (bono) | `dns_local.py` | Práctica 8, Lab 10 |
| Servicios de red y demo | `servicios.py`, `cliente.py`, `main.py` | — |

## Datos de prueba
| Código | Clave | Nota |
|---|---|---|
| 20201001 | juan123 | Matrícula exitosa (caso 3) |
| 20201002 | maria123 | Curso sin cupos ISA903 (caso 4) |
| 20201003 | luis123 | Sin historial documental (caso 5) |
| 20201004 | rosa123 | — |
| 20201005 | carlos123 | — |

Cursos: ISA902 (3 cupos), ISA903 (0 cupos), ISA801 e ISA802 (con notas de 2026-1).

## Decisiones de diseño
- **Participante MySQL**: en la fase 1 abre una transacción, descuenta el cupo e inserta la matrícula
  sin confirmar; vota NO si el `CHECK (cupos >= 0)` falla. En la fase 2 hace COMMIT o ROLLBACK.
- **Participante documental**: mongomock no tiene transacciones; en la fase 1 solo valida y deja el
  `$push` pendiente en memoria; lo aplica en la fase 2.
- **Registro del coordinador**: la decisión se escribe con `fsync` en `coordinador.log` antes de ordenarla.
- **Puerto DNS 5354**: el 5353 lo usa mDNS en Windows.
- **Validación de `rowcount`**: un `UPDATE` sobre un curso inexistente no da error en MySQL (afecta 0 filas);
  el participante lo detecta y vota NO.

## Limitaciones conocidas
- Todos los servicios corren como hilos de un mismo proceso: si el proceso cae, caen todos.
- Si el coordinador cae, no hay recuperación automática a partir de `coordinador.log`. Una mejora sería usar
  transacciones XA de MySQL (`XA PREPARE`), que conservan el estado "preparado" tras un reinicio.
- El servicio de nombres es un punto único de falla (no está replicado).
- mongomock y el LDAP simulado guardan los datos en memoria: se recrean en cada ejecución.