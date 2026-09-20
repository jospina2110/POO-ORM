"""
==============================================================================
Módulo: practica / main.py
Tema: Punto de entrada del sistema. Orquesta:
      1. Consola en UTF-8 (recuadros unicode del __str__).
      2. Singleton de base de datos -> conectar + crear tablas.
      3. Menú principal interactivo.
      4. Cierre seguro de la conexión.
==============================================================================
"""

import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from database import DatabaseManager
from menus import MenuPrincipal


def principal() -> None:
    gestor = DatabaseManager()   # metaclass Singleton: misma instancia siempre
    gestor.conectar()
    gestor.crear_tablas()
    MenuPrincipal().ejecutar()
    gestor.cerrar()


if __name__ == '__main__':
    principal()