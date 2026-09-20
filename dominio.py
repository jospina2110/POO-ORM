"""
==============================================================================
Módulo: practica / dominio.py
Tema: Clases de dominio. Pura lógica de negocio, cero dependencias de base
      de datos. Aquí vive la responsabilidad de validar reglas del mundo MotoGP.
      Incluye el patrón OBSERVER (06_patrones_diseno/03_comportamiento.py):
      cuando un equipo alcanza sus 2 pilotos, los observadores suscritos se
      notifican automáticamente (p. ej. el aprobador emite el "APROBADO").
==============================================================================
"""

from abc import ABC, abstractmethod


class MotoGP:
    'representa el mundo del deporte motor categoría reina'

    def __init__(self, nombre_equipo: str, marca_moto: str, nombre_ing_jefe: str,
                 inversion_equipo: int = 1000000, num_pilotos: int = 2):
        'constructor de la clase. inicializa los atributos de la instancia'
        self.nombre_equipo = nombre_equipo
        self.marca_moto = marca_moto
        self.nombre_ing_jefe = nombre_ing_jefe
        self._inversion_equipo = max(1000000, min(100000000, inversion_equipo))
        self.__n_pilotos = max(1, min(2, num_pilotos))
        self.equipo_completo = False
        self._pilotos: list[Piloto] = []
        self._observadores: list[ObservadorEquipo] = []

    # ------------------------------------------------------------------ OBSERVER
    def suscribir_observador(self, observador: 'ObservadorEquipo') -> None:
        'Registra un observador interesado en cambios del equipo'
        if observador not in self._observadores:
            self._observadores.append(observador)

    def _notificar_observadores(self) -> None:
        'Difunde el cambio a todos los observadores suscritos (Observer)'
        for observador in self._observadores:
            observador.equipo_cambido(self)

    def anadir_piloto(self, piloto: 'Piloto') -> None:
        'Valida y añade un piloto (máx. 2), luego notifica a los observadores'
        if len(self._pilotos) >= 2:
            raise ValueError('Un equipo MotoGP ya tiene sus 2 pilotos')
        if piloto.equipo is not None and piloto.equipo is not self:
            raise ValueError(f'El piloto {piloto.nombre} ya pertenece a otro equipo')
        piloto.equipo = self
        self._pilotos.append(piloto)
        self.equipo_completo = len(self._pilotos) == 2
        self._notificar_observadores()

    def quitar_piloto(self, piloto: 'Piloto') -> None:
        'Quita un piloto del equipo y re-notifica (vuelve a INCOMPLETO)'
        if piloto in self._pilotos:
            self._pilotos.remove(piloto)
            piloto.equipo = None
            self.equipo_completo = len(self._pilotos) == 2
            self._notificar_observadores()

    @property
    def inversion_equipo(self) -> float:
        'Obtiene la inversión del equipo'
        return self._inversion_equipo

    @inversion_equipo.setter
    def inversion_equipo(self, nuevo_total_inversion: float) -> None:
        'Establece una nueva inversión del equipo'
        if not isinstance(nuevo_total_inversion, (int, float)):
            raise TypeError('La inversión debe ser un número')
        if nuevo_total_inversion < 1000000:
            raise ValueError('No tienes pasta para estar en esta categoría reina')
        self._inversion_equipo = float(nuevo_total_inversion)

    @property
    def num_pilotos(self) -> int:
        'getter: expone el atributo privado con name mangling __n_pilotos'
        return self.__n_pilotos

    @num_pilotos.setter
    def num_pilotos(self, nuevo_numero: int) -> None:
        'setter: valida que MotoGP admita solo 1 o 2 pilotos'
        if not isinstance(nuevo_numero, int):
            raise TypeError('El número de pilotos debe ser un entero')
        if not 1 <= nuevo_numero <= 2:
            raise ValueError('MotoGP permite entre 1 y 2 pilotos por equipo')
        self.__n_pilotos = nuevo_numero

    @property
    def estado(self) -> str:
        'Estado derivado: no se almacena, se calcula'
        return 'APROBADO' if self.equipo_completo else 'NO APROBADO'

    @property
    def porcentaje_aprobacion(self) -> str:
        'Porcentaje derivado para el recuadro'
        return '100' if self.equipo_completo else '50'

    def __str__(self) -> str:
        'Representación en string de la clase (toString)'
        pilotos = ', '.join(extraer_nombre(p) for p in self._pilotos) or '—'
        return (
            f"┌{'─' * 50}┐\n"
            f"│ EQUIPO: {self.nombre_equipo:<40}│\n"
            f"│ Moto: {self.marca_moto:<40}│\n"
            f"│ Ingeniero Jefe: {self.nombre_ing_jefe:<40}│\n"
            f"│ Pilotos: {pilotos:<40}│\n"
            f"│ Estado: {self.estado:<40}│\n"
            f"│ Inversión: ${self._inversion_equipo:<40}│\n"
            f"└{'─' * 50}┘"
        )


def extraer_nombre(piloto: object) -> str:
    'Polimorfismo: nombre salvo fallo (compatible con Piloto y otras entidades)'
    getattr_ok = getattr(piloto, 'nombre', None)
    return getattr_ok if getattr_ok is not None else str(piloto)


class Piloto:
    'POO pura: representa a un piloto de MotoGP sin conocer la base de datos'

    def __init__(self, nombre: str, dorsal: int, nacionalidad: str,
                 equipo: 'MotoGP | None' = None):
        if not nombre or not nombre.strip():
            raise ValueError('El nombre del piloto no puede estar vacío')
        if not isinstance(dorsal, int) or dorsal <= 0:
            raise ValueError('El dorsal debe ser un entero positivo')
        self.nombre = nombre.strip()
        self.dorsal = dorsal
        self.nacionalidad = nacionalidad
        self.equipo = equipo

    def __str__(self) -> str:
        return (f'{self.dorsal} · {self.nombre} '
                f'({self.nacionalidad})')


class ObservadorEquipo(ABC):
    'INTERFAZ Observer (06_patrones_diseno/03_comportamiento.py)'

    @abstractmethod
    def equipo_cambido(self, equipo: MotoGP) -> None:
        'Se ejecuta automáticamente cuando el equipo cambia de estado'
        pass


class AprobadorAutomatico(ObservadorEquipo):
    'Observer concreto: emite el "APROBADO" cuando el equipo se completa'

    def equipo_cambido(self, equipo: MotoGP) -> None:
        if equipo.equipo_completo:
            print(f'🛎 Observador: {equipo.nombre_equipo} queda APROBADO '
                  f'(2 pilotos).')


class PreferenciaUsuario:
    'Representa una preferencia configurable del usuario (clave/valor tipado)'

    TIPOS_SOPORTADOS = (str, int, float, bool)

    def __init__(self, usuario: str, clave: str, valor: object):
        if not isinstance(usuario, str) or not usuario.strip():
            raise ValueError('El usuario no puede estar vacío')
        if not isinstance(clave, str) or not clave.strip():
            raise ValueError('La clave de la preferencia no puede estar vacía')
        if not isinstance(valor, self.TIPOS_SOPORTADOS):
            tipos = ', '.join(t.__name__ for t in self.TIPOS_SOPORTADOS)
            raise TypeError(f'El valor debe ser de tipo: {tipos}')
        self._usuario = usuario
        self._clave = clave
        self.valor = valor

    @property
    def usuario(self) -> str:
        return self._usuario

    @property
    def clave(self) -> str:
        return self._clave

    def __str__(self) -> str:
        return f'[Preferencia] {self.usuario} → {self.clave} = {self.valor!r}'