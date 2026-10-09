"""Pruebas de las fases 1 a 3.

Leen los archivos de data/processed/. Si se borran, hay que regenerarlos con
perfiles.py, agrupamiento.py y analisis.py antes de correr pytest.
"""
import pandas as pd

from agrupamiento import comparar, jerarquico, kmeans
from analisis import MANANA, TARDE, proporcion
from perfiles import calcular_perfiles

PERFILES = pd.read_csv("data/processed/perfiles.csv", dtype={"codigo": str}, index_col="codigo")
GRUPOS = pd.read_csv("data/processed/grupos.csv", dtype={"codigo": str}, index_col="codigo")


def test_perfiles_tienen_forma_y_suman_1():
    assert PERFILES.shape == (121, 68)
    assert (PERFILES.sum(axis=1) - 1).abs().max() < 1e-9


def test_solo_dias_habiles_no_festivos():
    # Se multiplican por 100 las validaciones de los festivos (7 y 17 de agosto)
    # y de los fines de semana. Si el filtro funciona, los perfiles no cambian.
    datos = pd.read_csv("data/dataset_demanda.csv", dtype={"codigo": str})
    alterados = datos.copy()
    excluidos = alterados["fecha"].isin(["2026-08-07", "2026-08-17"]) | (alterados["dia_semana"] >= 5)
    alterados.loc[excluidos, "validaciones"] *= 100
    pd.testing.assert_frame_equal(calcular_perfiles(datos), calcular_perfiles(alterados))


def test_kmeans_es_reproducible():
    assert list(kmeans(PERFILES)) == list(kmeans(PERFILES))


def test_cada_estacion_en_un_solo_grupo():
    assert sorted(GRUPOS.index) == sorted(PERFILES.index)
    assert GRUPOS["grupo"].notna().all()
    assert GRUPOS["grupo"].nunique() == 3


def test_kmeans_y_ward_coinciden():
    assert comparar(kmeans(PERFILES), jerarquico(PERFILES)) > 0.8


def test_nombres_de_grupos_tienen_sentido():
    curvas = PERFILES.groupby(GRUPOS["nombre_grupo"]).mean()
    manana = proporcion(curvas, MANANA)
    tarde = proporcion(curvas, TARDE)
    assert manana["Origen"] > tarde["Origen"]
    assert tarde["Destino"] > manana["Destino"]
