from data_loader import load_raw_data, load_clean_data
import matplotlib.pyplot as plt
import pandas as pd
import os

# Dossier de sortie
os.makedirs("recommender/reports/figures", exist_ok=True)

# Charger données
df_raw = load_raw_data()
df_clean = load_clean_data()

# Préparer quelques stats
raw_shape = df_raw.shape
clean_shape = df_clean.shape

contract_counts = df_clean["contrat"].value_counts().head(5)
type_counts = df_clean["type"].value_counts().head(5)

sample_df = df_clean[["prix", "ville", "type", "contrat"]].head(8).copy()
sample_df["prix"] = sample_df["prix"].round(0).astype(int)

# Création de la figure dashboard
fig = plt.figure(figsize=(16, 10), facecolor="white")

# Titre global
fig.suptitle("Dataset Overview - Recommender Module", fontsize=20, fontweight="bold")

# ---------------------------
# Bloc 1 : Shapes
# ---------------------------
ax1 = plt.subplot2grid((2, 2), (0, 0))
ax1.axis("off")

shape_text = (
    f"Dataset brut   : {raw_shape[0]:,} lignes × {raw_shape[1]} colonnes\n"
    f"Dataset clean  : {clean_shape[0]:,} lignes × {clean_shape[1]} colonnes\n"
    f"Lignes filtrées: {raw_shape[0] - clean_shape[0]:,}"
)

ax1.text(
    0.02, 0.7,
    shape_text,
    fontsize=15,
    va="top",
    ha="left",
    bbox=dict(boxstyle="round,pad=0.6", facecolor="#FFF3E8", edgecolor="#F58400", linewidth=2)
)
ax1.set_title("Vue d'ensemble", fontsize=16, fontweight="bold")

# ---------------------------
# Bloc 2 : Contrats
# ---------------------------
ax2 = plt.subplot2grid((2, 2), (0, 1))
bars1 = ax2.bar(contract_counts.index, contract_counts.values, color=["#F58400", "#FDB863", "#FDD49E", "#FEE8C8", "#FFEFD5"])
ax2.set_title("Top contrats", fontsize=16, fontweight="bold")
ax2.grid(axis="y", linestyle="--", alpha=0.3)
for spine in ax2.spines.values():
    spine.set_visible(False)
for bar in bars1:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h, f"{int(h):,}", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax2.tick_params(axis="x", rotation=20)

# ---------------------------
# Bloc 3 : Types
# ---------------------------
ax3 = plt.subplot2grid((2, 2), (1, 0))
bars2 = ax3.barh(type_counts.index[::-1], type_counts.values[::-1], color="#F58400")
ax3.set_title("Top types de biens", fontsize=16, fontweight="bold")
ax3.grid(axis="x", linestyle="--", alpha=0.3)
for spine in ax3.spines.values():
    spine.set_visible(False)
for bar in bars2:
    w = bar.get_width()
    ax3.text(w + max(type_counts.values)*0.01, bar.get_y() + bar.get_height()/2, f"{int(w):,}", va="center", fontsize=10, fontweight="bold")

# ---------------------------
# Bloc 4 : Aperçu data
# ---------------------------
ax4 = plt.subplot2grid((2, 2), (1, 1))
ax4.axis("off")
ax4.set_title("Extrait des données clean", fontsize=16, fontweight="bold")

table = ax4.table(
    cellText=sample_df.values,
    colLabels=sample_df.columns,
    loc="center",
    cellLoc="center"
)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.1, 1.6)

# Styliser le header
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_text_props(weight="bold", color="white")
        cell.set_facecolor("#F58400")
    else:
        cell.set_facecolor("#FFF8F2")

plt.tight_layout(rect=[0, 0, 1, 0.95])

output_path = "recommender/reports/figures/dataset_overview_dashboard.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"Dashboard sauvegardé : {output_path}")