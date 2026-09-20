"""
==============================================================================
Módulo: practica / database.py
Tema: Singleton responsable de la conexión a MySQL mediante Peewee.
      - Metaclass "registradora" -> una sola instancia en todo el programa.
      - Lee credenciales de variables de entorno (con defaults = docker-compose).
      - Conecta, crea las tablas y cierra la conexión.
==============================================================================
"""

import os

import pymysql

# Peewee por defecto importa MySQLdb (mysqlclient); con esto lo "suplantamos"
# con PyMySQL y no hace falta compilar el driver C de MySQL.
pymysql.install_as_MySQLdb()

from peewee import MySQLDatabase

from modelos import (database_proxy, BaseModel, EquipoModel, PilotoModel,
                     PreferenciaModel, ImagenModel)


class _MetaSingleton(type):
    'Metaclase que solo crea la instancia la primera vez (patrón Singleton)'

    _instancias = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instancias:
            cls._instancias[cls] = super().__call__(*args, **kwargs)
        return cls._instancias[cls]


class DatabaseManager(metaclass=_MetaSingleton):
    'Centraliza la conexión: abrir, crear tablas y cerrar'

    def __init__(self, host: str = '127.0.0.1', puerto: int = 3306):
        self.base_datos = MySQLDatabase(
            os.getenv('MYSQL_DATABASE', 'motogp_db'),
            host=host,
            port=puerto,
            user=os.getenv('MYSQL_USER', 'motogp_user'),
            password=os.getenv('MYSQL_PASSWORD', 'motogp_pass'),
            charset='utf8mb4',
        )
        # Enchufa el Proxy de los modelos a ESTA conexión real.
        # Sin esto, los modelos no saben a qué MySQL pertenecen.
        database_proxy.initialize(self.base_datos)
        self._conectado = False

    def conectar(self) -> 'DatabaseManager':
        'Abre la conexión solo si aún no está abierta (idempotente)'
        if not self._conectado:
            self.base_datos.connect()
            self._conectado = True
        return self

    def crear_tablas(self) -> None:
        'Crea las tablas si no existen (CREATE TABLE IF NOT EXISTS)'
        # Orden importa: el FK de PilotoModel apunta a EquipoModel (padre antes).
        self.base_datos.create_tables([EquipoModel, PilotoModel,
                                       PreferenciaModel, ImagenModel])

    def cerrar(self) -> None:
        'Cierra la conexión de forma segura'
        if self._conectado:
            self.base_datos.close()
            self._conectado = False