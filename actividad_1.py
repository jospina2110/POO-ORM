

class MotoGP:
    'representa el mundo del deporte motor categoria reina'
    def __init__(self, nombre_equipo:str, marca_moto:str,nombre_ing_jefe:str,inversion_equipo:int=1000000, num_pilotos: int =2):
        'constructor de la clase. inicializa los atributos de la instancia'
        self.nombre_equipo = nombre_equipo
        self.marca_moto = marca_moto
        self.nombre_ing_jefe = nombre_ing_jefe
        self._inversion_equipo = max(1000000,min(100000000,inversion_equipo))
        self.__n_pilotos = max(1,min(2,num_pilotos))
        self.equipo_completo = False

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

    def __str__(self) -> str:
        '''Representación en string de la clase (toString)'''
        estado = 'APROBADO' if self.equipo_completo else 'NO APROBADO'
        porcentaje = '100' if self.equipo_completo else '50'
        return (
            f"┌{'─' * 50}┐\n"
            f"│ EQUIPO: {self.nombre_equipo:<40}│\n"
            f"│ Moto: {self.marca_moto:<40}│\n"
            f"│ Ingeniero Jefe: {self.nombre_ing_jefe:<40}│\n"
            f"│ Pilotos: {self.__n_pilotos:<40}│\n"
            f"│ Estado: {estado:<40}({porcentaje}%)│\n"
            f"│ Inversión: ${self._inversion_equipo:<40}│\n"
            f"└{'─' * 50}┘"
        )

#metodos propios

#instanciar objetos
# Objeto 1
equipo1 = MotoGP("Red Bull Racing", "KTM", "Juan Pérez", 75000000, 2)
print("\n--- EQUIPO 1 ---")
print(equipo1) 

# Objeto 2
equipo2 = MotoGP("Ducati Team", "Ducati", "María García", 50000000, 1)
print("\n--- EQUIPO 2 ---")
print(equipo2)
    
# Objeto 3
equipo3 = MotoGP("CF Moto Team", "CF MOTO", "valentino rossi", 110000000, 1)
print("\n--- EQUIPO 3 ---")
print(equipo3)

# Objeto 4
equipo4 = MotoGP("Yamaha Team", "Yamaha", "David Alonso", 23000000, 2)
print("\n--- EQUIPO 4 ---")
print(equipo4)
    