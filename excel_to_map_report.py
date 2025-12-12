# %%
import pandas as pd
import folium
from pathlib import Path

# basic file names
DATA_FILE = "locations.csv"
ROUTES_FILE = "routes.csv"
MAP_FILE = "locations_map.html"
REPORT_FILE = "locations_report.html"


# %%
def load_data(path):
    df = pd.read_csv(path)
    required = ["name", "category", "latitude", "longitude"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    # drop rows without coordinates
    df = df.dropna(subset=["latitude", "longitude"])
    # make sure we have numeric coordinates
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    return df


def load_routes(path):
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()  # no routes
    df = pd.read_csv(path)

    required = ["route_name", "route_type", "latitude", "longitude"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"Routes file is missing required columns: {', '.join(missing)}"
        )

    df = df.dropna(subset=["latitude", "longitude"])
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])

    # optional seq column to order points along the route
    if "seq" in df.columns:
        df["seq"] = pd.to_numeric(df["seq"], errors="coerce")
    else:
        df["seq"] = 0

    return df


def create_map(
    df_points, df_routes):
    """Build an interactive map with point markers and optional routes."""
    # center on all points (both locations and routes if present)
    lat_values = [df_points["latitude"]]
    lon_values = [df_points["longitude"]]

    if df_routes is not None and not df_routes.empty:
        lat_values.append(df_routes["latitude"])
        lon_values.append(df_routes["longitude"])

    center_lat = pd.concat(lat_values).mean()
    center_lon = pd.concat(lon_values).mean()

    m = folium.Map(
        location=(center_lat, center_lon),
        zoom_start=13,
        tiles="CartoDB positron",
    )

    # 1) point markers
    for _, row in df_points.iterrows():
        popup_lines = [f"<b>{row['name']}</b>"]

        if isinstance(row.get("description"), str) and row["description"].strip():
            popup_lines.append(row["description"])

        popup_html = "<br>".join(popup_lines)

        folium.CircleMarker(
            location=(row["latitude"], row["longitude"]),
            radius=6,
            fill=True,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=row["name"],
        ).add_to(m)

    # 2) routes (each route_name gets one polyline)
    if df_routes is not None and not df_routes.empty:
        # simple colour mapping by route_type
        type_colors = {
            "tram": "blue",
            "bus": "red",
            "walk": "green",
            "bike": "purple",
        }
        default_color = "orange"

        for route_name, group in df_routes.groupby("route_name"):
            group = group.sort_values("seq")

            route_type = str(group["route_type"].iloc[0]).strip().lower()
            color = type_colors.get(route_type, default_color)

            points = list(zip(group["latitude"], group["longitude"]))

            folium.PolyLine(
                locations=points,
                color=color,
                weight=4,
                opacity=0.8,
                tooltip=f"{route_name} ({route_type})",
            ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


# quick test map if you run this cell in an editor
# %%
df_points = load_data(DATA_FILE)
df_routes = load_routes(ROUTES_FILE)
m = create_map(df_points, df_routes)
m.save("test.html")


# %%
def build_summary_table_html(df_points, df_routes):
    """HTML for point categories and route types."""
    parts: list[str] = []

    # points by category
    if "category" in df_points.columns:
        counts = df_points["category"].value_counts().reset_index()
        counts.columns = ["Category", "Locations"]
        cat_table = counts.to_html(
            index=False,
            border=0,
            classes="summary-table",
            justify="left",
        )
        parts.append(cat_table)
    else:
        parts.append("<p>No category column found for locations.</p>")

    # routes by type (optional)
    if not df_routes.empty and "route_type" in df_routes.columns:
        route_counts = (
            df_routes["route_type"]
            .dropna()
            .astype(str)
            .str.strip()
            .value_counts()
            .reset_index()
        )
        if not route_counts.empty:
            route_counts.columns = ["Route type", "Segments"]
            parts.append("<h3>Route segments by type</h3>")
            route_table = route_counts.to_html(
                index=False,
                border=0,
                classes="summary-table",
                justify="left",
            )
            parts.append(route_table)

    html_table = "\n".join(parts)
    return html_table

# %%
build_summary_table_html(df_points, df_routes)

# %%
REPORT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      padding: 0;
      background: #f7f7f7;
      color: #222;
    }}
    .page {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 2rem 1.5rem 3rem 1.5rem;
      background: #ffffff;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }}
    h1 {{
      margin-top: 0;
      font-size: 1.8rem;
    }}
    p.lead {{
      margin-top: 0.5rem;
      color: #555;
    }}
    .meta {{
      margin: 0.5rem 0 1.5rem 0;
      font-size: 0.9rem;
      color: #777;
    }}
    .map-wrapper {{
      margin: 1.5rem 0;
      border: 1px solid #ddd;
      height: 520px;
    }}
    .map-wrapper iframe {{
      width: 100%;
      height: 100%;
      border: 0;
    }}
    h2 {{
      margin-top: 2rem;
      font-size: 1.3rem;
    }}
    table.summary-table {{
      border-collapse: collapse;
      margin-top: 0.75rem;
      font-size: 0.9rem;
    }}
    table.summary-table th,
    table.summary-table td {{
      padding: 0.4rem 0.8rem;
      border-bottom: 1px solid #eee;
      text-align: left;
    }}
    table.summary-table th {{
      background: #f2f2f2;
      font-weight: 600;
    }}
    .note {{
      margin-top: 1.5rem;
      font-size: 0.85rem;
      color: #666;
    }}
  </style>
</head>
<body>
  <div class="page">
    <h1>{title}</h1>
    <p class="lead">Interactive map generated from a spreadsheet of locations.</p>
    <p class="meta">
      Total locations: <strong>{n_points}</strong>
    </p>

    <div class="map-wrapper">
      <iframe src="{map_filename}"></iframe>
    </div>

    <h2>Summary</h2>
    {summary_table}

    <p class="note">
      This HTML file and the map file live in the same folder.
      You can link to this page from an internal site or share it as a standalone report.
    </p>
  </div>
</body>
</html>
"""


def build_report(
    df_points, df_routes,
    map_filename, report_filename,
    title="Locations and routes from spreadsheet"):
    """Write an HTML report that embeds the map and summary tables."""
    summary_html = build_summary_table_html(df_points, df_routes)
    html = REPORT_TEMPLATE.format(
        title=title,
        map_filename=map_filename,
        n_points=len(df_points),
        summary_table=summary_html,
    )

    Path(report_filename).write_text(html, encoding="utf-8")


# %%
if __name__ == "__main__":
    df_points = load_data(DATA_FILE)
    df_routes = load_routes(ROUTES_FILE)

    m = create_map(df_points, df_routes)
    m.save(MAP_FILE)

    build_report(df_points, df_routes, MAP_FILE, REPORT_FILE)


# %%
