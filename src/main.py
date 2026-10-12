"""Fase 4: programa de consulta de los grupos de estaciones.

Muestra el resumen de los grupos o, para una estación buscada por parte de su
nombre, su grupo, su franja pico y cómo se compara con el promedio de su grupo.
Si todavía no existen los resultados de perfiles.py, agrupamiento.py y analisis.py,
los genera primero.

Uso: python src/main.py
"""
import runpy
import unicodedata
from pathlib import Path

import pandas as pd

from analisis import MANANA, TARDE, proporcion, resumen


def normalizar(texto):
    """Quita tildes y mayúsculas, para que "portal americas" encuentre "Portal Américas"."""
    # NFD separa cada letra de su tilde (á -> a + ´); al pasar a ASCII la tilde se descarta.
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def cargar():
    """Lee perfiles.csv y grupos.csv; si falta algún resultado, ejecuta antes las fases 1 a 3."""
    perfiles_csv = Path("data/processed/perfiles.csv")
    grupos_csv = Path("data/processed/grupos.csv")
    # grupos.csv solo está completo cuando analisis.py le agregó la columna nombre_grupo.
    completo = (perfiles_csv.exists() and grupos_csv.exists()
                and "nombre_grupo" in pd.read_csv(grupos_csv, nrows=0).columns)
    if not completo:
        print("Faltan resultados: se ejecutan las fases 1 a 3 (tarda unos segundos).")
        for script in ["perfiles.py", "agrupamiento.py", "analisis.py"]:
            # Ejecuta el script igual que "python src/<script>" desde la terminal.
            runpy.run_path(f"src/{script}", run_name="__main__")
    perfiles = pd.read_csv(perfiles_csv, dtype={"codigo": str}, index_col="codigo")
    grupos = pd.read_csv(grupos_csv, dtype={"codigo": str}, index_col="codigo")
    return perfiles, grupos


def elegir_estacion(grupos):
    """Pide parte del nombre y devuelve el código de la estación, o None si no se encontró."""
    texto = normalizar(input("Escriba parte del nombre de la estación: ").strip())
    if not texto:
        print("No escribió nada.")
        return None
    # regex=False: el texto se busca tal cual, así que un "(" o un "." no rompen la búsqueda.
    encontradas = grupos[grupos["nombre"].map(normalizar).str.contains(texto, regex=False)]
    if encontradas.empty:
        print("No hay ninguna estación con ese nombre.")
        return None
    if len(encontradas) == 1:
        return encontradas.index[0]

    # Varias coincidencias (por ejemplo, "portal"): se elige por número.
    for i, nombre in enumerate(encontradas["nombre"], start=1):
        print(f"  {i}. {nombre}")
    opcion = input("Número de la estación: ").strip()
    if not (opcion.isdigit() and 1 <= int(opcion) <= len(encontradas)):
        print("Número inválido.")
        return None
    return encontradas.index[int(opcion) - 1]


def mostrar_estacion(codigo, perfiles, grupos):
    """Imprime el grupo y la franja pico de la estación, y compara sus proporciones con las de su grupo."""
    estacion = grupos.loc[codigo]
    companeras = grupos[grupos["grupo"] == estacion["grupo"]].index
    manana = proporcion(perfiles, MANANA)
    tarde = proporcion(perfiles, TARDE)

    print(f"\n{estacion['nombre']} ({estacion['troncal']})")
    print(f"  Grupo: {estacion['nombre_grupo']}")
    print(f"  Franja pico: {perfiles.loc[codigo].idxmax()}")
    print(f"  Mañana (05:00-08:45): {manana[codigo]:.0%}  (promedio del grupo: {manana[companeras].mean():.0%})")
    print(f"  Tarde  (16:00-19:45): {tarde[codigo]:.0%}  (promedio del grupo: {tarde[companeras].mean():.0%})")
    otras = grupos.loc[companeras.drop(codigo), "nombre"].head(8)
    print(f"  Otras estaciones del grupo: {', '.join(otras)}")


def main():
    perfiles, grupos = cargar()
    while True:
        print("\n1. Ver el resumen de los grupos\n2. Consultar una estación\n3. Salir")
        opcion = input("Opción: ").strip()
        if opcion == "1":
            resumen(perfiles, grupos)
        elif opcion == "2":
            codigo = elegir_estacion(grupos)
            if codigo is not None:
                mostrar_estacion(codigo, perfiles, grupos)
        elif opcion == "3":
            break
        else:
            print("Opción inválida: escriba 1, 2 o 3.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C o fin de la entrada: se sale sin mostrar el error de Python.
        print()
