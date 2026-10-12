"""Fase 3: nombrar los grupos, describirlos y dibujar las figuras.

Lee perfiles.csv y grupos.csv de data/processed/, agrega a grupos.csv la columna
nombre_grupo (Origen, Destino o Mixto), imprime un resumen de cada grupo y guarda
tres figuras en docs/figuras/.

Uso: python src/analisis.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage

from agrupamiento import elegir_k

# Cada etiqueta marca el inicio de un intervalo de 15 minutos: "08:45" va hasta
# las 09:00, así que MANANA cubre de 05:00 a 09:00 y TARDE de 16:00 a 20:00.
MANANA = ("05:00", "08:45")
TARDE = ("16:00", "19:45")


def proporcion(perfiles, franja):
    """Parte de la demanda diaria de cada fila que cae dentro de la franja."""
    # Como cada perfil suma 1, basta con sumar las columnas de la franja. Las
    # columnas son texto "HH:MM" con ceros a la izquierda, así que el orden
    # alfabético coincide con el de las horas.
    desde, hasta = franja
    columnas = [c for c in perfiles.columns if desde <= c <= hasta]
    return perfiles[columnas].sum(axis=1)


def nombrar_grupos(perfiles, grupo):
    """Devuelve un diccionario {número de grupo: nombre}.

    Los números que asigna K-means son arbitrarios, así que cada grupo se nombra
    por su curva promedio. Las validaciones son entradas al sistema: el grupo con
    más entradas en la mañana es "Origen" (la gente sale de ahí hacia el trabajo
    o el estudio) y el que tiene más en la tarde es "Destino" (la gente regresa
    desde ahí). El grupo restante es "Mixto".
    """
    curvas = perfiles.groupby(grupo).mean()
    origen = proporcion(curvas, MANANA).idxmax()
    # Se excluye el Origen para que un mismo grupo no reciba los dos nombres.
    destino = proporcion(curvas, TARDE).drop(origen).idxmax()
    nombres = {g: "Mixto" for g in curvas.index}
    nombres[origen] = "Origen"
    nombres[destino] = "Destino"
    return nombres


def resumen(perfiles, grupos):
    """Imprime el tamaño, las proporciones, la franja pico y ejemplos de cada grupo."""
    manana = proporcion(perfiles, MANANA)
    tarde = proporcion(perfiles, TARDE)
    for nombre, estaciones in grupos.groupby("nombre_grupo"):
        curva = perfiles.loc[estaciones.index].mean()
        # El archivo está ordenado por código, que agrupa las estaciones por troncal;
        # una muestra aleatoria da ejemplos de varias troncales.
        ejemplos = estaciones["nombre"].sample(5, random_state=42)
        print(f"\n{nombre}: {len(estaciones)} estaciones")
        print(f"  Mañana (05:00-08:45): {manana[estaciones.index].mean():.0%}"
              f"   Tarde (16:00-19:45): {tarde[estaciones.index].mean():.0%}")
        print(f"  Franja pico: {curva.idxmax()}")
        print(f"  Portales: {estaciones['es_portal'].sum()}   Transbordos: {estaciones['es_transbordo'].sum()}")
        print(f"  Ejemplos: {', '.join(ejemplos)}")


def figura_perfiles(perfiles, grupos):
    """Figura principal: la curva promedio de cada grupo a lo largo del día."""
    curvas = perfiles.groupby(grupos["nombre_grupo"]).mean()
    fig, ax = plt.subplots(figsize=(10, 5))
    # .T deja las franjas como filas y los grupos como columnas; pandas dibuja
    # una línea por columna y usa su nombre en la leyenda.
    curvas.T.plot(ax=ax, linewidth=2)
    ax.set(xlabel="Hora del día", ylabel="Proporción de la demanda diaria",
           title="Curva promedio de cada grupo en un día hábil")
    ax.grid(alpha=0.3)
    ax.legend(title="Grupo")
    fig.savefig("docs/figuras/perfiles_grupos.png", dpi=150, bbox_inches="tight")


def figura_codo_silueta(tabla):
    """Inercia y silueta contra k, a partir de la tabla de elegir_k."""
    # Van en dos gráficos porque la inercia y la silueta tienen escalas distintas.
    fig, (izq, der) = plt.subplots(1, 2, figsize=(10, 4))
    izq.plot(tabla.index, tabla["inercia"], marker="o")
    izq.set(xlabel="k (número de grupos)", ylabel="Inercia", title="Método del codo")
    der.plot(tabla.index, tabla["silueta"], marker="o")
    der.set(xlabel="k (número de grupos)", ylabel="Silueta", title="Coeficiente de silueta")
    for ax in (izq, der):
        ax.axvline(3, color="gray", linestyle="--")  # k elegido
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("docs/figuras/codo_silueta.png", dpi=150)


def figura_dendrograma(perfiles):
    """Dendrograma de Ward, truncado a las 30 ramas superiores."""
    uniones = linkage(perfiles, method="ward")
    fig, ax = plt.subplots(figsize=(10, 5))
    # Con las 121 estaciones las etiquetas se enciman, por eso se trunca. Una hoja
    # con número entre paréntesis es una rama con esa cantidad de estaciones; sin
    # paréntesis es una sola estación (su posición en perfiles.csv).
    # uniones[-2, 2] es la altura de la penúltima unión: cortar ahí deja 3 grupos,
    # y cada uno se pinta de un color.
    dendrogram(uniones, truncate_mode="lastp", p=30, color_threshold=uniones[-2, 2], ax=ax)
    ax.set(xlabel="Ramas (entre paréntesis, cuántas estaciones agrupa)", ylabel="Distancia de Ward",
           title="Agrupamiento jerárquico (Ward)")
    fig.savefig("docs/figuras/dendrograma.png", dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    perfiles = pd.read_csv("data/processed/perfiles.csv", dtype={"codigo": str}, index_col="codigo")
    grupos = pd.read_csv("data/processed/grupos.csv", dtype={"codigo": str}, index_col="codigo")

    grupos["nombre_grupo"] = grupos["grupo"].map(nombrar_grupos(perfiles, grupos["grupo"]))
    grupos.to_csv("data/processed/grupos.csv")
    resumen(perfiles, grupos)

    Path("docs/figuras").mkdir(parents=True, exist_ok=True)
    figura_perfiles(perfiles, grupos)
    figura_codo_silueta(elegir_k(perfiles))
    figura_dendrograma(perfiles)
    print("\nFiguras guardadas en docs/figuras/")
