"""Fase 1: perfil de demanda de cada estación en un día hábil.

Lee data/dataset_demanda.csv y guarda data/processed/perfiles.csv, una tabla de
121 estaciones por 68 franjas de 15 minutos en la que cada fila suma 1.

Uso: python src/perfiles.py
"""
from pathlib import Path

import pandas as pd


def calcular_perfiles(datos):
    """Devuelve la curva de demanda normalizada de cada estación (una fila por estación)."""
    # Los fines de semana y los festivos tienen otra forma de demanda; si se
    # mezclan con los días hábiles, los picos de la mañana y de la tarde se suavizan.
    habiles = datos[(datos["dia_semana"] <= 4) & (datos["es_festivo"] == 0)]

    # Promedio de validaciones de cada estación en cada franja, sobre todos los días hábiles.
    tabla = habiles.pivot_table(index="codigo", columns="intervalo",
                                values="validaciones", aggfunc="mean")

    # Portal Tunal Cable solo tiene registros en 14 franjas y en las demás la
    # tabla queda en NaN. Se asume que sin registro no hubo validaciones y se
    # rellena con 0. Tibanica - Primavera trae todas sus franjas, algunas en 0.
    tabla = tabla.fillna(0)

    # Cada fila se divide entre su suma. Sin este paso, la distancia entre dos
    # estaciones dependería sobre todo de cuántas validaciones tiene cada una, y
    # K-means juntaría las grandes con las grandes. Normalizadas, quedan en el mismo
    # grupo las estaciones cuya gente entra a las mismas horas, sea cual sea su tamaño.
    return tabla.div(tabla.sum(axis=1), axis=0)


if __name__ == "__main__":
    datos = pd.read_csv("data/dataset_demanda.csv", dtype={"codigo": str})
    perfiles = calcular_perfiles(datos)
    Path("data/processed").mkdir(exist_ok=True)
    perfiles.to_csv("data/processed/perfiles.csv")

    sumas = perfiles.sum(axis=1)
    print(f"Estaciones: {perfiles.shape[0]}")
    print(f"Franjas de 15 minutos: {perfiles.shape[1]} ({perfiles.columns[0]} a {perfiles.columns[-1]})")
    print(f"Todas las filas suman 1: {(sumas - 1).abs().max() < 1e-9}")
    print("Guardado en data/processed/perfiles.csv")
