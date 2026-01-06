import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


# ======================================================
# 1. Indlæs Excel
# ======================================================


st.title("Jordprofiler")

uploaded_file = st.file_uploader(
    "Upload geologi.xlsx",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("Upload an Excel file to continue")
    st.stop()

raw = pd.read_excel(uploaded_file, header=0)
raw = raw.map(lambda x: x.strip() if isinstance(x, str) else x)


# ======================================================
# 2. Stationskolonner (B → J)
# ======================================================
station_cols = raw.columns[1:10]  # justér hvis nødvendigt

station_names = station_cols

station_koter = pd.to_numeric(
    raw.loc[raw.index[0], station_cols], errors="coerce"
)

station_positions = pd.to_numeric(
    raw.loc[raw.index[1], station_cols], errors="coerce"
)

vandspejl = pd.to_numeric(
    raw.loc[raw.index[2], station_cols], errors="coerce"
)

valid = (
    station_positions.notna()
    & station_koter.notna()
)

station_cols = station_cols[valid]
station_names = station_names[valid]
station_positions = station_positions[valid].values
station_koter = station_koter[valid].values
vandspejl = vandspejl[valid].values

# ======================================================
# 3. Dybder og jorddata (starter nu fra række 5)
# ======================================================
df = raw.iloc[3:, :].reset_index(drop=True)

depths = pd.to_numeric(df.iloc[:, 0], errors="coerce")

mask_depth = depths.notna()
depths = depths[mask_depth].reset_index(drop=True)
df = df.loc[mask_depth].reset_index(drop=True)

# ======================================================
# 4. Jordtyper & farver
# ======================================================
soil_color_map = {
    "Mangler": "#FFFFFF",
    "Muldlag": "#000000",
    "Groft grus og fint grus": "#BDBDBD",
    "Grovkornet sand (500-2000 µm)": "#E08E45",
    "Uomsat tørv (ikke humificeret tørv)": "#3B2412",
    "Svagt omsat tørv (svagt humificeret tørv)": "#4A2E18",
    "Mellemkornet sand (125-500 µm)": "#FCE5B9",
    "Mellemkornet sand med indslag af moderat omsat tørv": "#99835D",
    "Finkornet sand (63-125 µm)": "#F7E3A1",
    "Moderat omsat tørv": "#6B4423",
    "Gytjeholdigt sand": "#B7C8A0",
    "Stærkt omsat tørv": "#7A5A3A",
    "Silt": "#D6D2C4",
    "Ler": "#8FA6B3",
    "Kalkgytje": "#C8D6C8",
    "Fuldstændig omsat tørv": "#4E4A44"
}

# ======================================================
# 5. Terrænlinje (K = afstand, L = kote)
# ======================================================
terrain_x = pd.to_numeric(raw.iloc[1:, 10], errors="coerce")
terrain_y = pd.to_numeric(raw.iloc[1:, 11], errors="coerce")

mask_terrain = terrain_x.notna() & terrain_y.notna()
terrain_x = terrain_x[mask_terrain]
terrain_y = terrain_y[mask_terrain]

# ======================================================
# 6. Plot-opsætning
# ======================================================
plt.close("all")
fig, ax = plt.subplots(figsize=(15, 6))

bar_width = (
    np.min(np.diff(station_positions))
    if len(station_positions) > 1
    else 0.25

)

y_label = max(
    np.max(station_koter),
    np.nanmax(terrain_y),
    np.nanmax(vandspejl)
) + 0.3

# ======================================================
# 7. Plot profiler
# ======================================================
for col, x, label, kote in zip(
    station_cols, station_positions, station_names, station_koter
):
    column = df[col]

    for i in range(len(depths) - 1):
        soil = column.iloc[i]
        if not isinstance(soil, str):
            continue

        d_top = depths.iloc[i]
        d_bottom = depths.iloc[i + 1]

        top_kote = kote - d_top
        bottom_kote = kote - d_bottom

        top_kote = min(top_kote, kote)
        if bottom_kote >= kote:
            continue

        height = top_kote - bottom_kote
        if height <= 0:
            continue

        ax.bar(
            x=x,
            height=height,
            bottom=bottom_kote,
            width=bar_width,
            color=soil_color_map.get(soil, "#CCCCCC"),
            edgecolor="black",
            align="center"
        )

    ax.text(
        x,
        y_label,
        label,
        ha="center",
        va="bottom",
        rotation=90,
        fontsize=9
    )

# ======================================================
# 8. Terræn- og vandspejlslinjer
# ======================================================
ax.plot(
    terrain_x,
    terrain_y,
    color="black",
    linewidth=2,
    label="Terræn"
)

ax.plot(
    station_positions,
    vandspejl,
    color="blue",
    linewidth=2,
    linestyle="--",
    marker="o",
    label="Vandspejl"
)

# ======================================================
# 9. Akser
# ======================================================
ax.set_xlabel("Stationering / afstand (m)")
ax.set_ylabel("Kote (m)")
ax.set_xticks(station_positions)
ax.set_xticklabels([f"{x:.0f}" for x in station_positions])

# ======================================================
# 10. Signatur
# ======================================================
handles = [
    plt.Rectangle((0, 0), 1, 1,
                  color=soil_color_map[s],
                  label=s)
    for s in soil_color_map
]

handles += [
    plt.Line2D([0], [0], color="black", linewidth=2, label="Terræn"),
    plt.Line2D([0], [0], color="blue", linestyle="--", linewidth=2, label="Vandspejl")
]

ax.legend(
    handles=handles,
    title="Forklaring",
    bbox_to_anchor=(1.05, 1),
    loc="upper left"
)

plt.tight_layout()
st.pyplot(fig)
