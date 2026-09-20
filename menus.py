"""
==============================================================================
Módulo: practica / menus.py
Tema: CRUD por consola, 100% orientado a objetos.
      Hierarquía: MenuBase (abstracta) -> MenuEquipos / MenuPreferencias
      y MenuPrincipal como compositor de navegación.
      El acceso a datos es directo contra los modelos Peewee.
==============================================================================
"""

from abc import ABC, abstractmethod

from peewee import IntegrityError

from dominio import (MotoGP, Piloto, PreferenciaUsuario,
                     AprobacionAutomatica)
from modelos import (EquipoModel, PilotoModel, PreferenciaModel, ImagenModel)


class MenuBase(ABC):
    'Clase base abstracta: define el contrato y helpers reutilizables'

    @abstractmethod
    def ejecutar(self) -> None:
        'Bucle principal del menú que debe implementar cada subclase'
        pass

    def _leer_int(self, mensaje: str, minimo: int | None = None,
                  maximo: int | None = None) -> int:
        'Lee un entero validado, repitiendo la pregunta si falla'
        while True:
            try:
                valor = int(input(mensaje).strip())
                if (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo):
                    raise ValueError
                return valor
            except ValueError:
                limite = f' [{minimo}-{maximo}]' if minimo is not None and maximo is not None else ''
                print(f'Ingresa un entero válido{limite}.')

    def _leer_float(self, mensaje: str, minimo: float | None = None) -> float:
        'Lee un número decimal validado'
        while True:
            try:
                valor = float(input(mensaje).strip())
                if minimo is not None and valor < minimo:
                    raise ValueError
                return valor
            except ValueError:
                print('Ingresa un número válido.')

    def _confirmar(self, mensaje: str) -> bool:
        'Convierte la respuesta del usuario en booleano'
        return input(f'{mensaje} [s/N]: ').strip().lower() in ('s', 'si', 'y', 'yes')

    def _pausar(self) -> None:
        'Congela la pantalla hasta pulsar ENTER'
        input('\nPulsa ENTER para continuar...')


class MenuEquipos(MenuBase):
    'CRUD de equipos MotoGP. Acceso directo a EquipoModel.'

    def ejecutar(self) -> None:
        opciones = {
            '1': self.crear,
            '2': self.listar_todos,
            '3': self.buscar,
            '4': self.actualizar,
            '5': self.eliminar,
        }
        while True:
            print('\n' + '=' * 50)
            print('   MENÚ DE EQUIPOS MotoGP')
            print('=' * 50)
            print(' 1) Crear equipo')
            print(' 2) Listar todos los equipos')
            print(' 3) Buscar equipo por nombre')
            print(' 4) Actualizar equipo')
            print(' 5) Eliminar equipo')
            print(' 0) Volver al menú principal')
            print('=' * 50)
            opcion = input('Selecciona una opción: ').strip()
            if opcion == '0':
                break
            accion = opciones.get(opcion)
            if accion:
                accion()
                self._pausar()
            else:
                print('Opción no válida.')

    def crear(self) -> None:
        'CREATE: valida con el dominio y guarda con el modelo'
        print('\n--- NUEVO EQUIPO ---')
        nombre = input('Nombre del equipo: ').strip()
        marca = input('Marca de moto: ').strip()
        ingeniero = input('Ingeniero jefe: ').strip()
        inversion = self._leer_float('Inversión (mín. $1.000.000): ', minimo=1000000)
        pilotos = self._leer_int('Nº de pilotos (1 o 2): ', minimo=1, maximo=2)
        completo = self._confirmar('¿Equipo completo (APROBADO)?')

        moto = MotoGP(nombre, marca, ingeniero, inversion, pilotos)
        moto.equipo_completo = completo

        try:
            EquipoModel.desde_dominio(moto).save()
            print(f'✔ Equipo "{nombre}" guardado en MySQL.')
        except IntegrityError:
            print(f'✖ El equipo "{nombre}" ya existe (nombre es único).')

    def listar_todos(self) -> None:
        'READ: todos los registros ordenados por nombre'
        if not EquipoModel.select().exists():
            print('No hay equipos registrados.')
            return
        for registro in EquipoModel.select().order_by(EquipoModel.nombre_equipo):
            print('\n' + str(registro.a_dominio()))

    def buscar(self) -> None:
        'READ: un registro filtrado por nombre exacto'
        nombre = input('Nombre del equipo a buscar: ').strip()
        registro = EquipoModel.get_or_none(nombre_equipo=nombre)
        if registro is None:
            print(f'No se encontró el equipo "{nombre}".')
        else:
            print('\n' + str(registro.a_dominio()))

    def actualizar(self) -> None:
        'UPDATE: modifica inversión y estado del equipo'
        nombre = input('Nombre del equipo a actualizar: ').strip()
        registro = EquipoModel.get_or_none(nombre_equipo=nombre)
        if registro is None:
            print(f'No se encontró el equipo "{nombre}".')
            return

        print('\nRegistro actual:')
        print(registro.a_dominio())

        inversion = registro.inversion_equipo
        respuesta = input('Nueva inversión (vacío = conservar): ').strip()
        if respuesta:
            inversion = self._leer_float('Nueva inversión (mín. $1.000.000): ', minimo=1000000)

        rotulo = input('¿Equipo completo? (s/n, vacío = conservar): ').strip().lower()
        if rotulo in ('s', 'si', 'y', 'yes'):
            completo = True
        elif rotulo in ('n', 'no'):
            completo = False
        else:
            completo = registro.equipo_completo

        registro.inversion_equipo = inversion
        registro.equipo_completo = completo
        registro.save()  # al tener id, save() = UPDATE
        print('✔ Equipo actualizado en MySQL.')

    def eliminar(self) -> None:
        'DELETE: borra por nombre con confirmación'
        nombre = input('Nombre del equipo a eliminar: ').strip()
        registro = EquipoModel.get_or_none(nombre_equipo=nombre)
        if registro is None:
            print(f'No se encontró el equipo "{nombre}".')
            return
        if self._confirmar(f'¿Eliminar el equipo "{nombre}"?'):
            registro.delete_instance()
            print('✔ Equipo eliminado de MySQL.')


class MenuPreferencias(MenuBase):
    'CRUD de preferencias de usuario. Upsert sobre clave compuesta usuario+clave.'

    def ejecutar(self) -> None:
        opciones = {
            '1': self.guardar,
            '2': self.listar_todas,
            '3': self.buscar,
            '4': self.eliminar,
        }
        while True:
            print('\n' + '=' * 50)
            print('   MENÚ DE PREFERENCIAS')
            print('=' * 50)
            print(' 1) Guardar/actualizar preferencia')
            print(' 2) Listar todas las preferencias')
            print(' 3) Buscar preferencia')
            print(' 4) Eliminar preferencia')
            print(' 0) Volver al menú principal')
            print('=' * 50)
            opcion = input('Selecciona una opción: ').strip()
            if opcion == '0':
                break
            accion = opciones.get(opcion)
            if accion:
                accion()
                self._pausar()
            else:
                print('Opción no válida.')

    def guardar(self) -> None:
        'UPSERT: actualiza si existe la (usuario, clave) o inserta en caso contrario'
        print('\n--- PREFERENCIA ---')
        usuario = input('Usuario: ').strip()
        clave = input('Clave (p. ej. tema_oscuro, idioma, piloto_favorito): ').strip()
        texto_valor = input('Valor: ').strip()
        tipo = input('Tipo [str/int/float/bool] (vacío = str): ').strip() or 'str'

        try:
            valor = self._convertir_valor(texto_valor, tipo)
        except ValueError as error:
            print(f'✖ {error}')
            return

        preferencia = PreferenciaUsuario(usuario, clave, valor)
        insertado = PreferenciaModel.guardar_upsert(preferencia)
        mensaje = ('✔ Preferencia "{}" guardada para {}.'
                   if insertado else '✔ Preferencia "{}" actualizada (upsert).')
        print(mensaje.format(clave, usuario))

    @staticmethod
    def _convertir_valor(texto: str, tipo: str) -> object:
        'Convierte el texto del usuario al tipo Python indicado'
        if tipo == 'int':
            return int(texto)
        if tipo == 'float':
            return float(texto)
        if tipo == 'bool':
            return texto.strip().lower() in ('true', '1', 'si', 's', 'y', 'yes')
        if tipo == 'str':
            return texto
        raise ValueError('Tipo no soportado. Usa str, int, float o bool.')

    def listar_todas(self) -> None:
        'READ: todas las preferencias ordenadas por usuario y clave'
        if not PreferenciaModel.select().exists():
            print('No hay preferencias registradas.')
            return
        for registro in PreferenciaModel.select().order_by(
                PreferenciaModel.usuario, PreferenciaModel.clave):
            print(registro.a_dominio())

    def buscar(self) -> None:
        'READ: busca por la clave primaria compuesta (usuario + clave)'
        usuario = input('Usuario: ').strip()
        clave = input('Clave: ').strip()
        registro = PreferenciaModel.get_or_none(usuario=usuario, clave=clave)
        if registro is None:
            print(f'No se encontró la preferencia "{clave}" de {usuario}.')
        else:
            print(registro.a_dominio())

    def eliminar(self) -> None:
        'DELETE: elimina una preferencia por usuario + clave'
        usuario = input('Usuario: ').strip()
        clave = input('Clave: ').strip()
        registro = PreferenciaModel.get_or_none(usuario=usuario, clave=clave)
        if registro is None:
            print(f'No se encontró la preferencia "{clave}" de {usuario}.')
            return
        if self._confirmar(f'¿Eliminar la preferencia "{clave}" de {usuario}?'):
            registro.delete_instance()
            print('✔ Preferencia eliminada.')


class MenuPilotos(MenuBase):
    # CRUD de PilotoModel (1:N con equipos, FK) + OBSERVER (AprobacionAutomatica)

    def ejecutar(self) -> None:
        opciones = {
            "1": self.crear,
            "2": self.listar,
            "3": self.buscar,
            "4": self.actualizar,
            "5": self.eliminar,
        }
        while True:
            print("\n" + "=" * 52)
            print("  PILOTOS MotoGP  (1:N con Equipos + OBSERVER)")
            print("=" * 52)
            print(" 1) Crear piloto")
            print(" 2) Listar pilotos")
            print(" 3) Buscar piloto por dorsal")
            print(" 4) Actualizar piloto")
            print(" 5) Eliminar piloto")
            print(" 0) Volver")
            print("=" * 52)
            opcion = input("Opcion: ").strip()
            if opcion == "0":
                break
            accion = opciones.get(opcion)
            if accion:
                accion()
                self._pausar()
            else:
                print("Opcion no valida.")

    def crear(self) -> None:
        from peewee import IntegrityError
        from dominio import MotoGP, Piloto, AprobadorAutomatico
        from modelos import EquipoModel, PilotoModel

        print("\n--- NUEVO PILOTO ---")
        dorsal = self._leer_int("Dorsal (unico): ", minimo=1)
        nombre = input("Nombre: ").strip()
        nacionalidad = input("Nacionalidad: ").strip()
        nombre_equipo = input("Nombre del equipo (existe o vacio): ").strip()

        modelo_equipo = None
        equipo = None
        if nombre_equipo:
            from modelos import EquipoModel
            modelo_equipo = EquipoModel.get_or_none(nombre_equipo=nombre_equipo)
            if modelo_equipo is None:
                print("El equipo no existe. La FK debe apuntar a un equipo real.")
                return
            equipo = Equipo(
                nombre_equipo=modelo_equipo.nombre_equipo,
                inversion_equipo=modelo_equipo.inversion_equipo,
            )

        try:
            piloto = Piloto(nombre, dorsal, nacionalidad, equipo)
        except (ValueError, TypeError) as error:
            print(f"Dato no valido: {error}")
            return

        try:
            from modelos import PilotoModel
            PilotoModel.create(
                dorsal=dorsal,
                nombre=nombre,
                nacionalidad=nacionalidad,
                equipo=modelo_equipo,
            )
        except IntegrityError:
            print(f"El dorsal {dorsal} ya existe (clave unica).")
            return

        print(f"Piloto {nombre} (dorsal {dorsal}) guardado. FK -> equipo {nombre_equipo or '(ninguno)'}.")

        if equipo is not None:
            observador = AprobadorAutomatico()
            equipo.suscribir_observador(observador)
            if not equipo.equipo_completo:
                print("El equipo esta INCOMPLETO: falta el 2do piloto para APROBAR.")

    def listar(self) -> None:
        from modelos import PilotoModel
        print("\n--- PILOTOS REGISTRADOS ---")
        if not PilotoModel.select().exists():
            print("No hay pilotos.")
            return
        for registro in PilotoModel.select().order_by(PilotoModel.dorsal):
            equipo = registro.equipo.nombre_equipo if registro.equipo else "(sin equipo)"
            print(f"  #{registro.dorsal} {registro.nombre} ({registro.nacionalidad}) -> {equipo}")

    def buscar(self) -> None:
        from modelos import PilotoModel
        dorsal = self._leer_int("Dorsal a buscar: ", minimo=1)
        registro = PilotoModel.get_or_none(dorsal=dorsal)
        if registro is None:
            print(f"No existe piloto con dorsal {dorsal}.")
        else:
            equipo = registro.equipo.nombre_equipo if registro.equipo else "(sin equipo)"
            print(f"  #{registro.dorsal} {registro.nombre} ({registro.nacionalidad}) -> {equipo}")

    def actualizar(self) -> None:
        from modelos import PilotoModel, EquipoModel
        dorsal = self._leer_int("Dorsal a actualizar: ", minimo=1)
        registro = PilotoModel.get_or_none(dorsal=dorsal)
        if registro is None:
            print(f"No existe piloto con dorsal {dorsal}.")
            return
        nombre = input(f"Nuevo nombre [{registro.nombre}] (vacio = conservar): ").strip()
        nacionalidad = input(f"Nueva nacionalidad [{registro.nacionalidad}] (vacio = conservar): ").strip()
        if nombre:
            registro.nombre = nombre
        if nacionalidad:
            registro.nacionalidad = nacionalidad
        nuevo_equipo = input("Nuevo equipo (nombre o vacio): ").strip()
        if nuevo_equipo:
            eqm = EquipoModel.get_or_none(nombre_equipo=nuevo_equipo)
            if eqm is None:
                print(f"El equipo {nuevo_equipo} no existe.")
            else:
                registro.equipo = eqm
        registro.save()
        print("Piloto actualizado.")

    def eliminar(self) -> None:
        from modelos import PilotoModel
        dorsal = self._leer_int("Dorsal a eliminar: ", minimo=1)
        registro = PilotoModel.get_or_none(dorsal=dorsal)
        if registro is None:
            print(f"No existe piloto con dorsal {dorsal}.")
            return
        print(f"Se eliminara a {registro.nombre} (dorsal {dorsal}).")
        if input("Confirmar (s/n): ").strip().lower() == "s":
            registro.delete_instance()
            print("Piloto eliminado.")


class MenuReportes(MenuBase):
    # REPORTES SQL: SUM, AVG, COUNT, GROUP BY sobre MySQL (PilotoModel/EquipoModel)

    def ejecutar(self) -> None:
        from peewee import fn
        from modelos import EquipoModel, PilotoModel
        print("\n" + "=" * 52)
        print("  REPORTES SQL  (SUM / AVG / COUNT / GROUP BY)")
        print("=" * 52)

        total_equipos = EquipoModel.select(fn.COUNT(EquipoModel.id)).scalar() or 0
        print(f"  COUNT(*) equipos registrados: {total_equipos}")

        inversion_total = EquipoModel.select(fn.SUM(EquipoModel.inversion_equipo)).scalar() or 0
        inversion_media = EquipoModel.select(fn.AVG(EquipoModel.inversion_equipo)).scalar() or 0
        print(f"  SUM(inversion): {inversion_total:,.2f}")
        print(f"  AVG(inversion): {inversion_media:,.2f}")

        total_pilotos = PilotoModel.select(fn.COUNT(PilotoModel.id)).scalar() or 0
        print(f"  COUNT(*) pilotos registrados: {total_pilotos}")

        filas = (EquipoModel
                 .select(EquipoModel.nombre_equipo,
                         fn.COUNT(PilotoModel.id).alias("n_pilotos"))
                 .join(PilotoModel, on=(PilotoModel.equipo == EquipoModel.id))
                 .group_by(EquipoModel.id))
        print("  COUNT + GROUP BY (pilotos por equipo):")
        if not filas:
            print("    (sin datos)")
        for fila in filas:
            print(f"    - {fila.nombre_equipo}: {fila.n_pilotos} piloto(s)")

        self._pausar()


class MenuPrincipal(MenuBase):
    # Compositor: delegar ejecucion a los submenus (Composite + Facade)

    def ejecutar(self) -> None:
        opciones = {
            "1": MenuEquipos().ejecutar,
            "2": MenuPreferencias().ejecutar,
            "3": MenuPilotos().ejecutar,
            "4": MenuReportes().ejecutar,
        }
        while True:
            print("\n" + "#" * 56)
            print("#    PRACTICA FINAL POO - MySQL + Peewee (Composite)")
            print("#" * 56)
            print(" 1) Equipos (CRUD 1:1 + FK)")
            print(" 2) Preferencias de usuario")
            print(" 3) Pilotos (CRUD 1:N + OBSERVER)")
            print(" 4) Reportes SQL (SUM/AVG/COUNT/GROUP BY)")
            print(" 0) Salir")
            print("#" * 56)
            opcion = input("Opcion: ").strip()
            if opcion == "0":
                break
            accion = opciones.get(opcion)
            if accion:
                accion()
            else:
                print("Opcion no valida.")
