# -*- coding: utf-8 -*-
"""
===============================================================================
Modulo  : practica / interfaz_tk.py
Tema    : GUI Tkinter/ttk que REUTILIZA la practica completa POO + ORM
          (MySQL/Peewee) sin volver a escribir la capa de datos ni el dominio:
          exactamente igual que menus.py pero con presentacion grafica.

      * Composite  => ttk.Notebook con 4 pestanas (Equipos / Pilotos /
                      Preferencias / Reportes SQL).
      * Observer   => se REUTILIZA el ABC ObservadorEquipo y el concreto
                      AprobadorAutomatico del dominio (dominio.py) tal cual:
                      al completar un equipo (2do piloto) el dominio dispara
                      'EQUIPO APROBADO'. La GUI ademas agrega SU PROPIO
                      observador (ObservadorToast) que pinta el aviso en la
                      barra de estado -> demuestra el patron Observer de la
                      practica (1 notificacion, N observadores).
      * CRUD 1:1    => PestanaEquipos -> EquipoModel (INSERT/UPDATE/DELETE/
                      SELECT con filtro por inversion minima).
      * CRUD 1:N    => PestanaPilotos -> PilotoModel (FK -> EquipoModel) con
                      restauracion del MotoGP del dominio y Observer.
      * Preferencias=> CRUD contra PreferenciaModel (clave/valor/tipo).
      * Reportes    => SQL agregado (COUNT/SUM/AVG/GROUP BY) identico a
                      MenuReportes (fn.SUM, fn.COUNT, fn.AVG...).

Ejecutar : python main_tk.py        (punto de entrada con la GUI)
           python interfaz_tk.py    (directo)
Requiere : MySQL en docker (docker-compose.yml) como main.py.
===============================================================================
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from peewee import fn as peewee_fn, IntegrityError

from database import DatabaseManager            # Singleton MySQL/Peewee
from dominio import MotoGP, Piloto          # dominio puro (dominio.py)
from dominio import ObservadorEquipo, AprobadorAutomatico
from modelos import EquipoModel, PilotoModel, PreferenciaModel

OBSERVABLE = 'OBSERVABLE'


# =============================================================================
# Observer propio de la presentacion (GUI) - mismo ABC del dominio
# =============================================================================
class ObservadorToast(ObservadorEquipo):
    """Observador concreto SOBRE LA GUI: en lugar de solo print, refresca la
    barra de estado. Mismo contrato que AprobadorAutomatico (equipo_cambido)
    -> se demuestra el patron Observer con 2 observadores distintos del mismo
    sujeto (1 del dominio, 1 de la presentacion)."""

    def __init__(self, app: 'InterfazMotoTk') -> None:
        super().__init__()
        self._app = app

        color = '#0a7d0a' if equipo.equipo_completo else '#606060'
        estado = ("EQUIPO APROBADO (2 pilotos, AprobadorAutomatico)"
                  if equipo.equipo_completo
                  else "aun INCOMPLETO (falta 1 piloto)")
        self._app._barra_estado.config(
            text=(f"OBSERVER: {equipo.nombre_equipo} -> {estado}"),
            foreground=color)

# =============================================================================
# Pestana 1 - Equipos (CRUD 1:1 contra EquipoModel)
# =============================================================================
class PestanaEquipos(ttk.Frame):
    def __init__(self, maestro: ttk.Notebook,
                 app: 'InterfazMotoTk') -> None:
        super().__init__(maestro)
        self._app = app

        columnas = ("id", "nombre_equipo", "marca_moto", "nombre_ing_jefe",
                    "inversion_equipo", "num_pilotos", "equipo_completo")
        self._tree = ttk.Treeview(self, columns=columnas, show="headings",
                                  height=14)
        anchos = {"id": 40, "nombre_equipo": 165, "marca_moto": 115,
                  "nombre_ing_jefe": 140, "inversion_equipo": 110,
                  "num_pilotos": 90, "equipo_completo": 100}
        for c in columnas:
            self._tree.heading(c, text=c)
            self._tree.column(c, width=anchos[c], anchor="center")
        self._tree.pack(fill="both", expand=True, padx=8, pady=4)

        # ---- formulario ----
        frm = ttk.LabelFrame(self, text="Datos del equipo (INSERT/UPDATE)")
        frm.pack(fill="x", padx=8, pady=4)
        self._var_nombre = tk.StringVar()
        self._var_marca = tk.StringVar()
        self._var_jefe = tk.StringVar()
        self._var_inv = tk.StringVar()
        self._var_num = tk.StringVar()
        frm.columnconfigure(1, weight=1)
        ttk.Label(frm, text="Nombre equipo").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self._var_nombre, width=24
                  ).grid(row=0, column=1, sticky="we", padx=4, pady=2)
        ttk.Label(frm, text="Marca moto").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self._var_marca, width=24
                  ).grid(row=1, column=1, sticky="we", padx=4, pady=2)
        ttk.Label(frm, text="Ingeniero jefe").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self._var_jefe, width=24
                  ).grid(row=2, column=1, sticky="we", padx=4, pady=2)
        ttk.Label(frm, text="Inversion").grid(row=3, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self._var_inv, width=24
                  ).grid(row=3, column=1, sticky="we", padx=4, pady=2)
        ttk.Label(frm, text="Num. pilotos").grid(row=4, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self._var_num, width=24
                  ).grid(row=4, column=1, sticky="we", padx=4, pady=2)
        # filtro por inversion minima
        ttk.Label(frm, text="Inversion minima (filtro)").grid(
            row=5, column=0, sticky="w")
        self._var_min_inv = tk.StringVar()
        ttk.Entry(frm, textvariable=self._var_min_inv, width=24
                  ).grid(row=5, column=1, sticky="we", padx=4, pady=2)

        bot = ttk.Frame(self)
        bot.pack(fill="x", padx=8, pady=4)
        for t, c in (("Crear", self._crear), ("Actualizar", self._actualizar),
                     ("Eliminar", self._eliminar), ("Recargar", self._recargar)):
            ttk.Button(bot, text=t, command=c, width=11).pack(side="left", padx=3)

        self._recargar()

    # ---- helpers ----
    def _datos(self) -> dict | None:
        try:
            inv = float(self._var_inv.get().strip() or "0")
            num = int(self._var_num.get().strip() or "1")
        except ValueError:
            messagebox.showerror("Datos", "Inversion debe ser numerica y "
                                          "Num. pilotos entero.")
            return None
        return {"nombre_equipo": self._var_nombre.get().strip(),
                "marca_moto": self._var_marca.get().strip(),
                "nombre_ing_jefe": self._var_jefe.get().strip(),
                "inversion_equipo": inv,
                "num_pilotos": num}

    def _recargar(self) -> None:
        self._tree.delete(*self._tree.get_children())
        minimo = None
        try:
            minimo = float(self._var_min_inv.get())
        except ValueError:
            pass
        consulta = EquipoModel.select()
        if minimo is not None:
            consulta = consulta.where(
                EquipoModel.inversion_equipo >= minimo)
        for eq in consulta:
            self._tree.insert(
                "", "end",
                values=(eq.id, eq.nombre_equipo, eq.marca_moto,
                        eq.nombre_ing_jefe, eq.inversion_equipo,
                        eq.num_pilotos,
                        "SI" if eq.equipo_completo else "NO"))

    def _crear(self) -> None:
        d = self._datos()
        if d is None:
            return
        if not d["nombre_equipo"]:
            messagebox.showerror("Datos", "El nombre del equipo es "
                                          "obligatorio (PK/UNIQUE).")
            return
        if EquipoModel.get_or_none(
                EquipoModel.nombre_equipo == d["nombre_equipo"]):
            messagebox.showerror("Unicidad",
                                 f"Ya existe el equipo {d['nombre_equipo']}.")
            return
        EquipoModel.create(equipo_completo=False, **d)
        self._app._mensaje(f"Equipo {d['nombre_equipo']} creado (INSERT).")
        self._recargar()

    def _fila(self) -> EquipoModel | None:
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Seleccion", "Selecciona un equipo.")
            return None
        eq_id = int(self._tree.item(sel[0], "values")[0])
        return EquipoModel.get_or_none(EquipoModel.id == eq_id)

    def _actualizar(self) -> None:
        fila = self._fila()
        if fila is None:
            return
        d = self._datos()
        if d is None:
            return
        if EquipoModel.get_or_none(
                (EquipoModel.nombre_equipo == d["nombre_equipo"])
                & (EquipoModel.id != fila.id)):
            messagebox.showerror("Unicidad",
                                 f"El nombre {d['nombre_equipo']} ya lo tiene "
                                 f"otro equipo.")
            return
        EquipoModel.update(**d).where(EquipoModel.id == fila.id).execute()
        self._app._mensaje(f"Equipo {d['nombre_equipo']} actualizado "
                           f"(UPDATE).")
        self._recargar()

    def _eliminar(self) -> None:
        fila = self._fila()
        if fila is None:
            return
        if PilotoModel.select().where(
                PilotoModel.equipo == fila.id).exists():
            messagebox.showerror("Integridad FK (1:N)",
                                 f"{fila.nombre_equipo} tiene pilotos "
                                 f"asociados; eliminalos antes (IntegrityError "
                                 f"de la FK).")
            return
        nombre = fila.nombre_equipo
        fila.delete_instance()
        self._app._mensaje(f"Equipo {nombre} eliminado (DELETE).")
        self._recargar()


# =============================================================================
# Pestana 2: PILOTOS  (CRUD 1:N con FK -> EquipoModel + OBSERVER del dominio.
#  Esta pestana REUTILIZA el patron Observer EXACTAMENTE como lo hace
#  menus.py PestanaPilotos._crear: restaura el MotoGP del domino puro
#  (dominio.py), suscribe un AprobadorAutomatico, y llama anadir_piloto().
#  Cuando el equipo queda con sus 2 pilotos, el dominio NOTIFICA a su
#  AprobadorAutomatico (print "APROBADO...", identico a menus.py) y la GUI
#  ademas lo refleja pintando la fila del equipo en VERDE en PestanaEquipos
#  (segunda fuente del Observer, sin tocar menus ni dominio).
# =============================================================================
class PestanaPilotos(ttk.Frame):
    CAMPOS = ("dorsal", "nombre", "nacionalidad", "equipo_nombre")

    def __init__(self, maestro: ttk.Notebook, app: 'InterfazApp') -> None:
        super().__init__(maestro)
        self._app = app
        self._vars = {c: tk.StringVar()
                      for c in ("dorsal", "nombre", "nacionalidad",
                                "equipo_nombre")}
        self._tree = ttk.Treeview(self, columns=("id",) + self.CAMPOS,
                                  show="headings")
        for c in ("id",) + self.CAMPOS:
            self._tree.heading(c, text=c)
            self._tree.column(c, width=80 if c == "dorsal" else 130,
                              anchor="w" if c in ("nombre", "nacionalidad")
                              else "center")
        self._tree.pack(fill="both", expand=True, padx=8, pady=4)

        form = ttk.LabelFrame(self, text="Piloto (FK -> EquipoModel, 1:N)")
        form.pack(fill="x", padx=8, pady=4)
        for i, c in enumerate(self.CAMPOS):
            ttk.Label(form, text=c).grid(row=i, column=0, sticky="w", padx=4)
            ttk.Entry(form, textvariable=self._vars[c], width=24
                      ).grid(row=i, column=1, sticky="we", padx=4, pady=2)
        for t, cmd in (("Crear", self._crear), ("Eliminar",
                        self._eliminar)):
            ttk.Button(self, text=t, command=cmd, width=13
                       ).pack(side="left", padx=6, pady=4)
        self._recargar()

    def _fila(self) -> 'PilotoModel' | None:
        sel = self._tree.selection()
        if not sel:
            return None
        return PilotoModel.get_or_none(
            PilotoModel.dorsal == int(self._tree.item(
                sel[0], "values")[1]))

    def _crear(self) -> None:
        try:
            dorsal = int(self._vars["dorsal"].get().strip())
        except ValueError:
            messagebox.showerror("Dorsal", "El dorsal (PK unica de "
                                           "PilotoModel) debe ser entero.")
            return
        nombre = self._vars["nombre"].get().strip()
        nacionalidad = self._vars["nacionalidad"].get().strip()
        nom_equipo = self._vars["equipo_nombre"].get().strip()

        if PilotoModel.get_or_none(PilotoModel.dorsal == dorsal):
            messagebox.showerror("Unicidad", f"Ya existe un piloto con "
                                             f"dorsal {dorsal}: es la clave "
                                             f"unica de la tabla "
                                             f"(PilotoModel.dorsal unique).")
            return
        equipo_orm = None
        if nom_equipo:
            equipo_orm = EquipoModel.get_or_none(
                EquipoModel.nombre_equipo == nom_equipo)
            if equipo_orm is None:
                messagebox.showerror("FK 1:N", f"No existe el equipo "
                                               f"{nom_equipo}; la FK "
                                               f"fallaria (IntegrityError).")
                return

        try:
            reg = PilotoModel.create(
                dorsal=dorsal, nombre=nombre,
                nacionalidad=nacionalidad, equipo=equipo_orm)
        except IntegrityError:
            messagebox.showerror("IntegrityError",
                                 "La BD rechazo el INSERT: dorsal repetido "
                                 "o FK inexistente.")
            self._recargar()
            return

        # ---- Restaura MotoGP del dominio + Observer (identico menus.py) ----
        if equipo_orm is not None:
            equipo_dom = MotoGP(
                nombre_equipo=equipo_orm.nombre_equipo,
                marca_moto=equipo_orm.marca_moto,
                nombre_ing_jefe=equipo_orm.nombre_ing_jefe,
                inversion_equipo=equipo_orm.inversion_equipo,
                num_pilotos=equipo_orm.num_pilotos,
            )
            observador = AprobadorAutomatico()
            equipo_dom.suscribir_observador(observador)
            piloto_dom = Piloto(nombre=nombre, dorsal=dorsal,
                                nacionalidad=nacionalidad,
                                equipo=equipo_dom)
            equipo_dom.anadir_piloto(piloto_dom)
            if equipo_dom.equipo_completo:
                # El dominio ya imprimio "APROBADO"; la GUI lo refleja.
                equipo_orm.equipo_completo = True
                equipo_orm.num_pilotos = PilotoModel.select().where(
                    PilotoModel.equipo == equipo_orm).count()
                equipo_orm.save()
                messagebox.showinfo(
                    "OBSERVER (dominio)",
                    f"{equipo_orm.nombre_equipo} quedo COMPLETO con "
                    f"{equipo_orm.num_pilotos} pilotos -> el dominio "
                    f"disparo 'APROBADO'. Fila en verde en Equipos.")
        self._app.refrescar_equipos()
        self._recargar()
        self._app._estado.config(
            text=f"Piloto dorsal {dorsal} insertado (INSERT 1:N + "
                 f"Observer).", foreground="#0a5a0a")

    def _eliminar(self) -> None:
        reg = self._fila()
        if reg is None:
            return
        dorsal = reg.dorsal
        reg.delete_instance()
        self._app.refrescar_equipos()
        self._recargar()
        self._app._estado.config(
            text=f"Piloto dorsal {dorsal} eliminado (DELETE 1:N).",
            foreground="#444444")

    def _recargar(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for p in PilotoModel.select().order_by(PilotoModel.dorsal):
            eq = p.equipo.nombre_equipo if p.equipo else "(sin equipo)"
            self._tree.insert("", "end", values=(
                p.id, p.dorsal, p.nombre, p.nacionalidad, eq))

# =============================================================================
# Pestana 3: PREFERENCIAS  (CRUD 1:1 contra PreferenciaModel, PK compuesta
# (usuario, clave) -> la MISMA que valida la BD: IntegrityError si se repite)
# =============================================================================
class PestanaPreferencias(ttk.Frame):
    COLUMNAS = ("usuario", "clave", "tipo", "valor")

    def __init__(self, maestro: ttk.Notebook, app: 'InterfazMotoTK') -> None:
        super().__init__(maestro)
        self._app = app
        self._vars = {c: tk.StringVar() for c in
                      ("usuario", "clave", "tipo", "valor")}

        self._tree = ttk.Treeview(self, columns=self.COLUMNAS,
                                  show="headings", height=12)
        for c in self.COLUMNAS:
            self._tree.heading(c, text=c)
            self._tree.column(c, width=140 if c in ("usuario", "clave")
                              else 90, anchor="w" if c in ("usuario",
                              "clave", "valor") else "center")
        self._tree.pack(fill="both", expand=True, padx=8, pady=4)

        form = ttk.LabelFrame(self, text="Preferencia (PK compuesta "
                                         "usuario+clave)")
        form.pack(fill="x", padx=8, pady=3)
        for i, c in enumerate(("usuario", "clave", "tipo", "valor")):
            ttk.Label(form, text=c).grid(row=i, column=0, sticky="w")
            ttk.Entry(form, textvariable=self._vars[c], width=26
                      ).grid(row=i, column=1, padx=4, pady=2)

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=3)
        for txt, cmd in (("Crear", self._crear), ("Eliminar", self._eliminar),
                         ("Recargar", self._recargar)):
            ttk.Button(bar, text=txt, command=cmd, width=12
                       ).pack(side="left", padx=3)
        self._recargar()

    def _fila(self) -> tuple | None:
        sel = self._tree.selection()
        if not sel:
            return None
        v = self._tree.item(sel[0], "values")
        return tuple(v[0:2])

    def _crear(self) -> None:
        u = self._vars["usuario"].get().strip()
        c = self._vars["clave"].get().strip()
        t = self._vars["tipo"].get().strip() or "str"
        v = self._vars["valor"].get().strip()
        if not u or not c:
            messagebox.showerror("PK compuesta",
                                 "usuario y clave forman la PK: ambos son "
                                 "obligatorios (IntegrityError si no).")
            return
        if PreferenciaModel.get_or_none(
                (PreferenciaModel.usuario == u)
                & (PreferenciaModel.clave == c)):
            messagebox.showerror("IntegrityError",
                                 f"La PK compuesta ({u}, {c}) ya existe: "
                                 f"Peewee/MySQL la rechazan (unicidad de la "
                                 f"clave primaria).")
            return
        try:
            PreferenciaModel.create(usuario=u, clave=c, tipo=t, valor=v)
        except IntegrityError:
            messagebox.showerror("IntegrityError",
                                 f"No se pudo insertar ({u}, {c}): PK "
                                 f"compuesta duplicada.")
            return
        self._app._estado.config(
            text=f"Preferencia ({u}, {c}) creada (INSERT, PK compuesta).",
            foreground="#0a5a0a")
        self._recargar()

    def _eliminar(self) -> None:
        f = self._fila()
        if f is None:
            messagebox.showwarning("Seleccion", "Selecciona una "
                                               "preferencia.")
            return
        PreferenciaModel.delete().where(
            (PreferenciaModel.usuario == f[0])
            & (PreferenciaModel.clave == f[1])).execute()
        self._app._estado.config(
            text=f"Preferencia ({f[0]}, {f[1]}) eliminada (DELETE).",
            foreground="#444444")
        self._recargar()

    def _recargar(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for p in PreferenciaModel.select().order_by(PreferenciaModel.usuario,
                                                    PreferenciaModel.clave):
            self._tree.insert("", "end", values=(
                p.usuario, p.clave, p.tipo, p.valor))

# =============================================================================
# Pestana 4: REPORTES SQL (agregados IDENTICOS a MenuReportes / ReporteModel
# escalar). Se usa la MISMA consulta peewee (fn.COUNT/fn.SUM/fn.AVG + GROUP
# BY) que ya muestra menus.py; no se recablea nada, solo se re-ejecuta desde
# la GUI con el mismo DatabaseManager Singleton.
# =============================================================================
class PestanaReportes(ttk.Frame):
    COLUMNAS = ("titulo", "valor")

    def __init__(self, app: 'InterfazMotoTk') -> None:
        super().__init__(maestro)
        self._app = app
        self._tree = ttk.Treeview(self, columns=self.COLUMNAS,
                                  show="headings", height=18)
        self._tree.heading("titulo", text="Reporte (SQL agregado)")
        self._tree.heading("valor", text="Valor")
        self._tree.column("titulo", width=430, anchor="w")
        self._tree.column("valor", width=120, anchor="e")
        self._tree.pack(fill="both", expand=True, padx=8, pady=4)

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=3)
        ttk.Button(bar, text="Ejecutar reportes SQL",
                   command=self._recargar, width=22).pack(side="left", padx=3)
        ttk.Button(bar, text="Exportar CSV",
                   command=self._exportar, width=16).pack(side="left", padx=3)
        self._recargar()

    def _recargar(self) -> None:
        self._tree.delete(*self._tree.get_children())
        equipo = EquipoModel.get_or_none(EquipoModel.id == 1)
        if equipo is None:
            return

        moto = MotoGP(nombre_equipo=equipo.nombre_equipo,
                      marca_moto=equipo.marca_moto,
                      nombre_ing_jefe=equipo.nombre_ing_jefe,
                      inversion_equipo=equipo.inversion_equipo,
                      num_pilotos=equipo.num_pilotos)
        listo = "SI" if moto.equipo_completo else "NO"
        self._filas(("Equipo (dominio MotoGP restaurado)", 
                     moto.nombre_equipo))
        self._filas(("num_pilotos (propiedad dominio)", moto.num_pilotos))
        self._filas(("inversion_equipo (Float columna)", 
                     f"{moto.inversion_equipo:,.2f}"))
        self._filas(("equipo_completo (Bool)", listo))

        total_equipos = EquipoModel.select(
            peewee_fn.COUNT(EquipoModel.id)).scalar() or 0
        self._filas(("COUNT(*) equipos", str(total_equipos)))

        total_pilotos = PilotoModel.select(
            peewee_fn.COUNT(PilotoModel.id)).scalar() or 0
        self._filas(("COUNT(*) pilotos", str(total_pilotos)))

        inversion_total = EquipoModel.select(
            peewee_fn.SUM(EquipoModel.inversion_equipo)).scalar() or 0
        self._filas(("SUM(inversion_equipo)", f"{inversion_total:,.2f}"))

        inversion_promedio = EquipoModel.select(
            peewee_fn.AVG(EquipoModel.inversion_equipo)).scalar() or 0
        self._filas(("AVG(inversion_equipo)", 
                     f"{inversion_promedio:,.2f}"))

    def _filas(self, fila: tuple) -> None:
        self._tree.insert("", "end", values=fila)

    def _exportar(self) -> None:
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfile="reportes_motogp.csv")
        if not ruta:
            return
        with open(ruta, "w", newline="", encoding="utf-8") as archivo:
            w = csv.writer(archivo)
            w.writerow(self.COLUMNAS)
            for hijo in self._tree.get_children():
                w.writerow(self._tree.item(hijo, "values"))
        self._app._estado.config(
            text=f"Reportes exportados a CSV (utf-8): {ruta}",
            foreground="#0a5a0a")

# =============================================================================
# InterfazMotoTk : COMPOSITE raiz de la GUI - el ttk.Notebook es el nodo
# contenedor y cada Pestana es un hijo hoja (SAME patron Composite que
# MenuPrincipal en menus.py con sus submenus). Ademas reutilia el OBSERVER:
# el dominio MotoGP restaurado desde la DB recibe AprobadorAutomatico
# (metodo equipo_cambido -> "EQUIPO APROBADO" print) y la GUI se suscribe
# como OBSERVADOR adicional con ObservadorToast (cambia barra de estado).
# =============================================================================
class InterfazMotoTk(ttk.Frame):
    def __init__(self, maestro: tk.Tk, gestor: DatabaseManager) -> None:
        super().__init__(maestro)
        self._gestor = gestor
        self.pack(fill="both", expand=True)

        self._barra_estado = tk.Label(
            self, text="MotoTk listo (POO + ORM Peewee/MySQL).",
            anchor="w", fg="#0a5a0a", bg="#eaffea", padx=8, pady=3)
        self._barra_estado.pack(fill="x", side="bottom")

        self._libro = ttk.Notebook(self)
        self._libro.pack(fill="both", expand=True, padx=8, pady=8)

        self._pestanas = (
            PestanaEquipos(self._libro, self),
            PestanaPilotos(self._libro, self),
            PestanaPreferencias(self._libro, self),
            PestanaReportes(self._libro, self),
        )
        nombres = ("Equipos (1:1)", "Pilotos (1:N con Observer)",
                   "Preferencias (PK compuesta)",
                   "Reportes (SQL agregado)")
        for p, n in zip(self._pestanas, nombres):
            self._libro.add(p, text=n)

        self._observer_toast = ObservadorToast(self)
        self._suscribir_dominio()

    def _suscribir_dominio(self) -> None:
        eq = EquipoModel.get_or_none(EquipoModel.id == 1)
        if eq is None:
            return
        moto = MotoGP(nombre_equipo=eq.nombre_equipo,
                      marca_moto=eq.marca_moto,
                      nombre_ing_jefe=eq.nombre_ing_jefe,
                      inversion_equipo=eq.inversion_equipo,
                      num_pilotos=eq.num_pilotos)
        aprobador = AprobadorAutomatico()
        moto.suscribir_observador(aprobador)
        moto.suscribir_observador(self._observer_toast)


def _main() -> None:
    raiz = tk.Tk()
    raiz.title("MotoGP - Practica POO + ORM (Tkinter Composite + "
               "Observer)")
    raiz.geometry("1000x640")
    gestor = DatabaseManager()
    gestor.conectar()
    gestor.crear_tablas()
    InterfazMotoTk(raiz, gestor)
    raiz.mainloop()


if __name__ == "__main__":
    _main()
