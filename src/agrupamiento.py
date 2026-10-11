"""Fase 2: agrupar las estaciones por la forma de su curva de demanda.

Lee data/processed/perfiles.csv, compara K-means con el agrupamiento jerárquico
de Ward y guarda data/processed/grupos.csv con el grupo de cada estación.

Uso: python src/agrupamiento.py
"""
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score


def elegir_k(perfiles):
    """Entrena K-means con k de 2 a 7 y devuelve la inercia, la silueta y el tamaño de los grupos.

    La inercia siempre baja al aumentar k; con el método del codo se busca el k
    a partir del cual deja de bajar mucho. La silueta va de -1 a 1 y es mayor
    cuando los grupos están compactos y bien separados entre sí.
    """
    filas = []
    for k in range(2, 8):
        modelo = KMeans(n_clusters=k, n_init=10, random_state=42).fit(perfiles)
        filas.append({
            "k": k,
            "inercia": modelo.inertia_,
            "silueta": silhouette_score(perfiles, modelo.labels_),
            "tamanos": pd.Series(modelo.labels_).value_counts().tolist(),
        })
    return pd.DataFrame(filas).set_index("k")


def kmeans(perfiles, k=3):
    """Agrupa con K-means y devuelve el número de grupo de cada estación."""
    # El resultado de K-means depende de los centros iniciales: con n_init=10 se
    # entrena 10 veces y se queda con la solución de menor inercia.
    return KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(perfiles)


def jerarquico(perfiles, k=3):
    """Agrupamiento jerárquico aglomerativo con el criterio de Ward.

    En cada paso Ward une los dos grupos que menos aumentan la varianza interna,
    que es lo mismo que minimiza K-means. Por eso sirve para comprobar si
    K-means encontró una estructura estable.
    """
    return AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(perfiles)


def comparar(etiquetas_a, etiquetas_b):
    """Índice de Rand ajustado entre dos agrupamientos.

    Vale 1 si los dos forman exactamente los mismos grupos y 0 si coinciden lo
    que se esperaría por azar. Solo mira qué estaciones quedan juntas, así que no
    importa que el grupo 0 de K-means corresponda al grupo 2 del jerárquico.
    """
    return adjusted_rand_score(etiquetas_a, etiquetas_b)


if __name__ == "__main__":
    perfiles = pd.read_csv("data/processed/perfiles.csv", dtype={"codigo": str}, index_col="codigo")

    print("Elección de k:")
    print(elegir_k(perfiles).round(3).to_string())

    # Se usa k = 3. Con k = 2 la silueta es mayor, pero las estaciones con dos
    # picos se reparten entre los otros dos grupos. Con k = 4 los tres grupos se
    # mantienen y solo se aparta Portal Tunal Cable, que tiene datos en 14 franjas.
    etiquetas = kmeans(perfiles)
    print(f"\nÍndice de Rand ajustado K-means vs. Ward (k=3): {comparar(etiquetas, jerarquico(perfiles)):.3f}")

    estaciones = pd.read_csv("data/estaciones.csv", dtype={"codigo": str}, index_col="codigo")
    grupos = estaciones.loc[perfiles.index, ["nombre", "troncal", "es_portal", "es_transbordo"]]
    grupos["grupo"] = etiquetas
    grupos.to_csv("data/processed/grupos.csv")
    print("Guardado en data/processed/grupos.csv")
