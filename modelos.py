"""
==============================================================================
Módulo: practica / modelos.py
Tema: Modelos Peewee (ORM). Cada clase = una tabla en MySQL.
      "Modelo Peewee directo": este archivo es el único punto de contacto
      con la base de datos; el menú lo usa sin capas intermedias.
      AHORA CON RELACIONES 1:N (ForeignKeyField) y BLOB (BlobField).
==============================================================================
"""

from peewee import (
    Model,
    Proxy,
    CharField,
    FloatField,
    IntegerField,
    BooleanField,
    ForeignKeyField,
    BlobField,
    CompositeKey,
)

from dominio import MotoGP, Piloto, PreferenciaUsuario

# Proxy: "enchufe" que aún no sabe a qué base de datos apunta.
# DatabaseManager lo rellena al arrancar (evita importaciones circulares).
database_proxy = Proxy()


class BaseModel(Model):
    'Clase base: todos nuestros modelos heredan la conexión del Proxy'

    class Meta:
        database = database_proxy


class EquipoModel(BaseModel):
    'Tabla equipos_motogp. Campo por cada atributo del dominio.'

    nombre_equipo = CharField(max_length=50, unique=True)
    marca_moto = CharField(max_length=50)
    nombre_ing_jefe = CharField(max_length=50)
    inversion_equipo = FloatField()
    num_pilotos = IntegerField()
    equipo_completo = BooleanField(default=False)

    class Meta:
        table_name = 'equipos_motogp'

    @classmethod
    def desde_dominio(cls, moto: MotoGP) -> 'EquipoModel':
        'Traductor dominio → modelo (factory). No toca la base todavía.'
        return cls(
            nombre_equipo=moto.nombre_equipo,
            marca_moto=moto.marca_moto,
            nombre_ing_jefe=moto.nombre_ing_jefe,
            inversion_equipo=moto.inversion_equipo,
            num_pilotos=moto.num_pilotos,
            equipo_completo=moto.equipo_completo,
        )

    def a_dominio(self) -> MotoGP:
        'Traductor modelo → dominio. Reconstruye el objeto POO puro.'
        moto = MotoGP(
            nombre_equipo=self.nombre_equipo,
            marca_moto=self.marca_moto,
            nombre_ing_jefe=self.nombre_ing_jefe,
            inversion_equipo=self.inversion_equipo,
            num_pilotos=self.num_pilotos,
        )
        moto.equipo_completo = self.equipo_completo
        return moto


class PilotoModel(BaseModel):
    'Tabla pilotos. Relación 1:N: cada piloto pertenece a UN equipo (FK).'

    dorsal = IntegerField(unique=True)
    nombre = CharField(max_length=50)
    nacionalidad = CharField(max_length=50)
    equipo = ForeignKeyField(EquipoModel, backref='pilotos',
                             on_delete='CASCADE', on_update='CASCADE',
                             null=True)

    class Meta:
        table_name = 'pilotos'

    @classmethod
    def desde_dominio(cls, piloto: Piloto) -> 'PilotoModel':
        'Traductor dominio → modelo. El FK se asigna por el nombre del equipo.'
        equipo = (EquipoModel.get_or_none(nombre_equipo=piloto.equipo.nombre_equipo)
                  if piloto.equipo else None)
        return cls(dorsal=piloto.dorsal, nombre=piloto.nombre,
                   nacionalidad=piloto.nacionalidad, equipo=equipo)

    def a_dominio(self) -> Piloto:
        'Traductor modelo → dominio.'
        equipo = self.equipo.a_dominio() if self.equipo else None
        return Piloto(dorsal=self.dorsal, nombre=self.nombre,
                      nacionalidad=self.nacionalidad, equipo=equipo)

    @classmethod
    def guardar_upsert(cls, piloto: Piloto) -> bool:
        'Upsert por dorsal único. Devuelve True si fue INSERT, False si UPDATE.'
        nuevo = cls.desde_dominio(piloto)
        existente = cls.get_or_none(dorsal=piloto.dorsal)
        if existente is None:
            cls.insert(dorsal=nuevo.dorsal, nombre=nuevo.nombre,
                       nacionalidad=nuevo.nacionalidad,
                       equipo=nuevo.equipo).execute()
            return True
        existente.nombre = nuevo.nombre
        existente.nacionalidad = nuevo.nacionalidad
        existente.equipo = nuevo.equipo
        existente.save()
        return False


class PreferenciaModel(BaseModel):
    'Tabla preferencias_usuario. Usuario+clave forman la clave primaria compuesta.'

    usuario = CharField(max_length=50)
    clave = CharField(max_length=50)
    tipo = CharField(max_length=10)    # str, int, float o bool
    valor = CharField(max_length=255)  # representación en texto del valor

    class Meta:
        table_name = 'preferencias_usuario'
        primary_key = CompositeKey('usuario', 'clave')

    @classmethod
    def desde_dominio(cls, preferencia: PreferenciaUsuario) -> 'PreferenciaModel':
        'Serializa el objeto de dominio en columnas texto + tipo'
        return cls(
            usuario=preferencia.usuario,
            clave=preferencia.clave,
            tipo=type(preferencia.valor).__name__,
            valor=str(preferencia.valor),
        )

    def a_dominio(self) -> PreferenciaUsuario:
        'Deserializa: usa la columna "tipo" para reconstruir el tipo Python'
        valor: object = self.valor
        if self.tipo == 'int':
            valor = int(self.valor)
        elif self.tipo == 'float':
            valor = float(self.valor)
        elif self.tipo == 'bool':
            valor = self.valor.lower() in ('true', '1', 'si', 's')
        return PreferenciaUsuario(usuario=self.usuario, clave=self.clave, valor=valor)

    @classmethod
    def guardar_upsert(cls, preferencia: PreferenciaUsuario) -> bool:
        'Inserta si no existe (usuario+clave) o actualiza en caso contrario.'
        nuevo = cls.desde_dominio(preferencia)
        existente = cls.get_or_none(
            usuario=preferencia.usuario, clave=preferencia.clave)
        if existente is not None:
            existente.tipo = nuevo.tipo
            existente.valor = nuevo.valor
            existente.save()
            return False
        cls.insert(
            usuario=nuevo.usuario,
            clave=nuevo.clave,
            tipo=nuevo.tipo,
            valor=nuevo.valor,
        ).execute()
        return True


class ImagenModel(BaseModel):
    'Tabla imagenes_motogp. Guarda PNG generados con Pillow como BLOB.'

    recurso = CharField(max_length=20)     # moto, casco o escudo
    nombre = CharField(max_length=50)      # clave del objeto al que pertenece
    imagen_data = BlobField()              # LONGBLOB en MySQL: bytes del PNG

    class Meta:
        table_name = 'imagenes_motogp'
        primary_key = CompositeKey('recurso', 'nombre')

    @classmethod
    def guardar_imagen(cls, recurso: str, nombre: str, datos: bytes) -> None:
        'Upsert de la imagen por (recurso, nombre).'
        existente = cls.get_or_none(recurso=recurso, nombre=nombre)
        if existente is None:
            cls.insert(recurso=recurso, nombre=nombre,
                       imagen_data=datos).execute()
        else:
            existente.imagen_data = datos
            existente.save()

    @classmethod
    def obtener_imagen(cls, recurso: str, nombre: str) -> bytes | None:
        'Devuelve los bytes del PNG o None si no existe.'
        registro = cls.get_or_none(recurso=recurso, nombre=nombre)
        return registro.imagen_data if registro else None

    def __str__(self) -> str:
        return (f'[Imagen] {self.recurso} · {self.nombre} '
                f'({len(self.imagen_data)} bytes)')
