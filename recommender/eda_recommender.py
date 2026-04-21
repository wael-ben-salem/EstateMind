import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

plt.style.use("default")

os.makedirs("recommender/reports/figures", exist_ok=True)

df = pd.read_csv(
    "data_cleaned/tunisia_realestate_cleaned.csv",
    low_memory=False
)

# =========================
# 1) Contrats
# =========================
contract_counts = (
    df["contrat"]
    .dropna()
    .astype(str)
    .str.strip()
    .replace("", pd.NA)
    .dropna()
    .value_counts()
)

colors_contract = ["#F58400", "#2c2c2c", "#A0A0A0", "#D3D3D3", "#808080"]

plt.figure(figsize=(12, 7), facecolor="white")
bars = plt.bar(
    contract_counts.index,
    contract_counts.values,
    color=colors_contract[:len(contract_counts)]
)

for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{int(height):,}",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold"
    )

plt.title("Distribution des types de contrat", fontsize=16, fontweight="bold")
plt.xlabel("Type de contrat", fontsize=12)
plt.ylabel("Nombre d'annonces", fontsize=12)
plt.xticks(rotation=30)
plt.grid(axis="y", linestyle="--", alpha=0.3)

for spine in plt.gca().spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig("recommender/reports/figures/contrats_distribution_clean.png", dpi=300, bbox_inches="tight")
plt.close()

# =========================
# 2) Types de biens
# =========================
type_counts = (
    df["type"]
    .dropna()
    .astype(str)
    .str.strip()
    .replace("", pd.NA)
    .dropna()
    .value_counts()
    .head(12)
    .sort_values()
)

plt.figure(figsize=(12, 8), facecolor="white")
bars = plt.barh(
    type_counts.index,
    type_counts.values,
    color="#F58400"
)

for bar in bars:
    width = bar.get_width()
    plt.text(
        width + max(type_counts.values) * 0.01,
        bar.get_y() + bar.get_height() / 2,
        f"{int(width):,}",
        va="center",
        fontsize=10,
        fontweight="bold"
    )

plt.title("Top 12 des types de biens", fontsize=16, fontweight="bold")
plt.xlabel("Nombre d'annonces", fontsize=12)
plt.ylabel("Type de bien", fontsize=12)
plt.grid(axis="x", linestyle="--", alpha=0.3)

for spine in plt.gca().spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig("recommender/reports/figures/types_biens_top12.png", dpi=300, bbox_inches="tight")
plt.close()

print("Graphiques générés avec succès.")

import numpy as np

# =========================
# 3) Top villes (gradient)
# =========================
ville_counts = (
    df["ville"]
    .dropna()
    .astype(str)
    .str.strip()
    .replace("", pd.NA)
    .dropna()
    .value_counts()
    .head(15)
    .sort_values()
)

plt.figure(figsize=(12, 8), facecolor="white")

# Création gradient de couleurs
colors = plt.cm.Oranges(
    np.linspace(0.4, 1, len(ville_counts))
)

bars = plt.barh(
    ville_counts.index,
    ville_counts.values,
    color=colors
)

# Ajouter valeurs
for bar in bars:
    width = bar.get_width()
    plt.text(
        width + max(ville_counts.values) * 0.01,
        bar.get_y() + bar.get_height() / 2,
        f"{int(width):,}",
        va="center",
        fontsize=10,
        fontweight="bold"
    )

# Style
plt.title(
    "Top 15 des villes les plus représentées",
    fontsize=16,
    fontweight="bold"
)

plt.xlabel("Nombre d'annonces", fontsize=12)
plt.ylabel("Ville", fontsize=12)

plt.grid(axis="x", linestyle="--", alpha=0.3)

# Clean design
for spine in plt.gca().spines.values():
    spine.set_visible(False)

plt.tight_layout()

plt.savefig(
    "recommender/reports/figures/top_villes.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# =========================
# 4) Distribution des prix (log)
# =========================
prix_series = pd.to_numeric(df["prix"], errors="coerce").dropna()
prix_series = prix_series[prix_series > 0]

# On travaille sur log10(prix) pour rendre la distribution lisible
log_prix = np.log10(prix_series)

plt.figure(figsize=(12, 7), facecolor="white")

plt.hist(
    log_prix,
    bins=40,
    color="#F58400",
    edgecolor="white"
)

plt.title("Distribution logarithmique des prix", fontsize=16, fontweight="bold")
plt.xlabel("log10(Prix)", fontsize=12)
plt.ylabel("Nombre d'annonces", fontsize=12)
plt.grid(axis="y", linestyle="--", alpha=0.3)

for spine in plt.gca().spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig("recommender/reports/figures/distribution_prix_log.png", dpi=300, bbox_inches="tight")
plt.close()

# =========================
# 4) Prix par contrat (boxplot log)
# =========================
df_price = df.copy()

df_price["prix"] = pd.to_numeric(df_price["prix"], errors="coerce")
df_price["contrat"] = (
    df_price["contrat"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# Garder seulement vente et location
df_price = df_price[
    df_price["contrat"].isin(["vente", "location"])
].copy()

# Garder prix valides
df_price = df_price[df_price["prix"] > 0].copy()

# Transformation log
df_price["log_prix"] = np.log10(df_price["prix"])

plt.figure(figsize=(10, 7), facecolor="white")

data_to_plot = [
    df_price[df_price["contrat"] == "location"]["log_prix"],
    df_price[df_price["contrat"] == "vente"]["log_prix"]
]

box = plt.boxplot(
    data_to_plot,
    labels=["Location", "Vente"],
    patch_artist=True,
    widths=0.5
)

# Couleurs
box["boxes"][0].set(facecolor="#FDB863", edgecolor="#F58400", linewidth=1.5)
box["boxes"][1].set(facecolor="#5DA5DA", edgecolor="#2C3E50", linewidth=1.5)

for median in box["medians"]:
    median.set(color="#111111", linewidth=2)

for whisker in box["whiskers"]:
    whisker.set(color="#666666", linewidth=1.2)

for cap in box["caps"]:
    cap.set(color="#666666", linewidth=1.2)

for flier in box["fliers"]:
    flier.set(marker="o", alpha=0.15, markersize=3, markeredgecolor="#999999")

plt.title("Comparaison des prix par contrat (échelle logarithmique)", fontsize=16, fontweight="bold")
plt.ylabel("log10(Prix)", fontsize=12)
plt.grid(axis="y", linestyle="--", alpha=0.3)

for spine in plt.gca().spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig("recommender/reports/figures/prix_par_contrat_boxplot.png", dpi=300, bbox_inches="tight")
plt.close()