# Practica POO + ORM (Python / MySQL / Peewee) - MotoGP

Autor: jospina2110  |  Repo: https://github.com/jospina2110/POO-ORM.git

## Que es
Sistema de gestion de un campeonato ficticio **MotoGP** que demuestra
**Programacion Orientada a Objetos** en Python aplicada a un caso real,
persistido con **ORM Peewee sobre MySQL (docker)**. La misma logica de
dominio se presenta con DOS interfaces:

1. `main.py`  : menu de **texto por consola** (menus.py)
2. `main_tk.py` : **GUI Tkinter/ttk** (interfaz_tk.py, ttk.Notebook)

Ambas reutilizan el MISMO nucleo: dominio, modelos, base de datos.
Nada se escribe dos veces.

## Stack
- Python 3.10+ (type hints, dataclasses).
- Peewee 3.x (ORM) + PyMySQL (driver).
- MySQL 8 en docker (docker-compose.yml).
- Tkinter/ttk (solo para la GUI; libreria estandar).

## Patrones de diseno aplicados (practica POO)
- **Singleton** : `DatabaseManager` (database.py) - una sola conexion/gestor
  compartida por consola y GUI.
- **Composite** : `MenuPrincipal` (menus.py) agrupa submenus; la GUI usa el
  mismo arbol con `ttk.Notebook` + 4 pestanas (`InterfazMotoTk`).
- **Observer** : `MotoGP` es el Sujeto (dominio.py); notifica a
  `AprobadorAutomatico` (regla de negocio: 2 pilotos = EQUIPO APROBADO).
  La GUI agrega OTRO observador (`ObservadorToast`) sobre el mismo sujeto:
  un solo evento, multiples reacciones (consola + barra de estado).
- **Dominio puro** : dominio.py no conoce Peewee ni Tkinter (regla de
  negocio aislada); modelos.py/dominio.py hacen el mapeo 1:1.
- **PK compuesta** : PreferenciaModel usa CompositeKey(usuario, clave).

## Arquitectura / archivos
| Archivo            | Responsabilidad                          |
|--------------------|------------------------------------------|
| database.py        | Singleton: conexion MySQL + crear tablas |
| dominio.py         | Clases puras: MotoGP, Piloto, Observer   |
| modelos.py         | Modelos Peewee (Equipo/Piloto/Preferencia/Imagen) |
| menus.py           | Menu de consola (reutiliza el nucleo)    |
| interfaz_tk.py     | GUI Tkinter (Notebook + pestanas CRUD)   |
| main.py / main_tk.py | Puntos de entrada (consola / GUI)     |
| docker-compose.yml | Levanta MySQL 8 para la practica         |
| requirements.txt   | peewee, pymysql                          |

## Tablas (MySQL via Peewee)
| Tabla              | Clave | Campos principales                          |
|--------------------|-------|---------------------------------------------|
| equipo            | id    | nombre_equipo, marca_moto, nombre_ing_jefe, inversion_equipo (Float), num_pilotos, equipo_completo (Bool) |
| piloto            | dorsal| nombre, nacionalidad, equipo (FK -> equipo)  |
| preferencia_usuario | (usuario, clave) CompositeKey | tipo, valor |
| imagen            | id    | recurso, nombre, imagen_data (Blob)          |

## Como ejecutar
# 1) Levantar MySQL (docker)
docker compose up -d

# 2) Opcion A: consola (texto)
python main.py

# 2) Opcion B: GUI (Tkinter)
python main_tk.py

# Verificacion de tipos en Windows (opcional)
python -m py_compile main.py main_tk.py interfaz_tk.py menus.py

## Requisitos
pip install peewee pymysql

(En Windows: se requiere Tkinter, incluido con el instalador base de Python.)

## Notas de la practica
- `actividad_1.py` NO se sube al repo (ejercicio suelto, innecesario).
- `.gitignore` excluye `__pycache__/`, entornos virtuales y archivos
  locales temporales.
- credenciales MySQL por defecto (ver docker-compose.yml / database.py).

## Base de datos (docker + MySQL 8)
Iniciar el contenedor (misma config que la practica base):

    docker compose up -d         # (o: docker-compose up -d)
    docker ps                     # verificar que "mysql_motogp" este UP

Credenciales (contenedor): usuario `motogp` / clave `motogp123` / base
`motogp_db` (ver docker-compose.yml). Puerto 3306.

> Si cambias credenciales, ajusta `database.py` (DatabaseManager) y
> docker-compose.yml en el MISMO punto: la practica no duplica valores.

## Ejecutar
Consola (menu de texto - menus.py):
    python main.py

GUI Tkinter (composite + observer en pantalla - interfaz_tk.py):
    python main_tk.py

La primera vez ambas crean las tablas automaticamente (DatabaseManager
es Singleton y reutiliza la misma conexion).

## Que demuestra cada pestana (GUI)
| Pestana            | Patron / concepto                      | Accion de fondo        |
|--------------------|----------------------------------------|------------------------|
| Equipos 1:1        | CRUD contra tabla equipo               | INSERT / UPDATE / DELETE / SELECT |
| Pilotos 1:N        | Observer real (AprobadorAutomatico)    | anadir/eliminar piloto -> dominio MotoGP reuso |
| Preferencias       | PK compuesta (usuario+clave)           | INSERT con IntegrityError controlado |
| Reportes           | SQL agregado (COUNT/SUM/AVG/GROUP BY)  | fn.COUNT(peewee)      |

## Evaluacion / criterios de la practica
1. POO: 3 clases con estado propio (MotoGP, Piloto, PreferenciaUsuario).
2. Relaciones: 1:1 (equipo), 1:N (pilotos->equipo), N:M via preferencias.
3. ORM Peewee: modelos + consultas SQL crudas cuando aportan.
4. Patrones: Singleton (DB), Composite (menus/Notebook), Observer (aprobado).
5. GUI: Tkinter/ttk reutilizando el 100% del nucleo de dominio.