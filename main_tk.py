# -*- coding: utf-8 -*-
"""
=============================== main_tk.py ===============================
Punto de entrada de la GUI Tkinter (mismo patron que main.py pero
arrancando InterfazMotoTk en lugar de MenuPrincipal).

Flujo identico a main.py:
    1) DatabaseManager()   (Singleton - database.py)
    2) gestor.conectar()   (MySQL/Peewee)
    3) gestor.crear_tablas() (Peewee CREATE TABLE IF NOT EXISTS)
    4) InterfazMotoTk(raiz, gestor).mainloop()

La GUI REUTILIZA el 100% de la practica: dominio.py (Composite + Observer
MotoGP/AprobadorAutomatico), modelos.py (EquipoModel, PilotoModel,
PreferenciaModel, ImagenModel), database.py (Singleton) y menus.py
(MenuPrincipal con sus Menu*: no se toca, se reutiliza tal cual).

Ejecutar :  python main_tk.py
Requiere :  MySQL en docker (docker-compose.yml) exactamente igual que
            main.py. Las tablas son las MISMAS (Peewee las crea si no
            existen; no se reescribe nada de la capa de datos).
============================================================================
"""

from database import DatabaseManager
from interfaz_tk import InterfazMotoTk


def _main() -> None:
    gestor = DatabaseManager()
    gestor.conectar()
    gestor.crear_tablas()
    inter = InterfazMotoTk(gestor)
    inter.ejecutar()


if __name__ == "__main__":
    _main()