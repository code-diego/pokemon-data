"""
Helper de machine learning: clustering K-means + PCA.
Usado por pages/5_Clusters_ML.py y reutilizable desde notebooks.
"""
import pandas as pd
import numpy as np

try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    _SKLEARN_OK = True
except ImportError:
    _SKLEARN_OK = False


ARCHETYPE_NAMES = {
    0: "Grupo A", 1: "Grupo B", 2: "Grupo C",
    3: "Grupo D", 4: "Grupo E", 5: "Grupo F",
}

ARCHETYPE_COLORS = [
    "#636EFA","#EF553B","#00CC96","#AB63FA",
    "#FFA15A","#19D3F3","#FF6692","#B6E880",
]


def sklearn_available() -> bool:
    return _SKLEARN_OK


def cluster_pokemon(
    df: pd.DataFrame,
    k: int = 5,
    features: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    """
    Ajusta K-means con k clusters sobre las features indicadas (estandarizadas).
    Solo usa filas donde todas las features son no-nulas.

    Retorna:
        df_out   — df con columnas 'cluster', 'pca_x', 'pca_y' añadidas
        profiles — DataFrame con el centroide promedio (en escala original) por cluster
        inertia  — array de inercias para k=2..k+4 (para gráfica de codo)
    """
    if not _SKLEARN_OK:
        raise ImportError("Instala scikit-learn: pip install scikit-learn")

    if features is None:
        from data import STAT_COLS
        features = STAT_COLS

    df_clean = df.dropna(subset=features).copy()
    X = df_clean[features].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # K-means
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    df_clean["cluster"] = labels

    # PCA 2D para visualización
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_scaled)
    df_clean["pca_x"] = coords[:, 0]
    df_clean["pca_y"] = coords[:, 1]

    # Perfil de clusters (media en escala original)
    profiles = df_clean.groupby("cluster")[features].mean().round(1)

    # Inercias k=2..k+4 para gráfica de codo
    k_range = range(2, max(k + 5, 10))
    inertias = np.array([
        KMeans(n_clusters=ki, random_state=42, n_init=10).fit(X_scaled).inertia_
        for ki in k_range
    ])

    return df_clean, profiles, inertias


def label_archetype(profiles: pd.DataFrame, features: list[str] | None = None) -> dict[int, str]:
    """
    Heurística simple para etiquetar clusters por su stat dominante.
    Retorna {cluster_id: etiqueta}.
    """
    if features is None:
        try:
            from data import STAT_COLS
            features = STAT_COLS
        except ImportError:
            features = list(profiles.columns)

    stat_names = {
        "hp": "Tanque (HP)", "attack": "Atacante Físico", "defense": "Bastión Defensivo",
        "special-attack": "Atacante Especial", "special-defense": "Muro Especial",
        "speed": "Velocista",
    }
    labels = {}
    bst = profiles[features].sum(axis=1)

    for cid, row in profiles.iterrows():
        if bst[cid] >= bst.quantile(0.75):
            labels[cid] = "Poderoso (BST alto)"
        else:
            dominant = row[features].idxmax()
            labels[cid] = stat_names.get(dominant, f"Grupo {cid}")
    return labels
