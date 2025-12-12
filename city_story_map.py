# %%
import sys
import folium
from folium.plugins import HeatMap

# Example city centre: Portland, Oregon
CITY_CENTER = (45.515, -122.679)
ZOOM_START = 13


# %%

def create_base_map():
    """Base folium map."""
    m = folium.Map(
        location=CITY_CENTER,
        zoom_start=ZOOM_START,
        tiles=None
    )

    # Manually add the tile layer(s) with a custom 'name' and 'attr'
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="City Map", # Custom name for the LayerControl
        # attr="attribution text"
    ).add_to(m)
    return m
# tiles options
'''
'OpenStreetMap': A standard global street map suitable for general use.
'CartoDB Positron': A light, minimalist map designed for data overlays.
'CartoDB DarkMatter': A dark background that makes colored data stand out.
'''

def get_routes_data():
    # routes near the city centre
    tram_line = {
        "name": "Tram Line",
        "color": "blue",
        "points": [
            (45.523, -122.676),
            (45.521, -122.681),
            (45.518, -122.683),
            (45.515, -122.682),
            (45.511, -122.678),
        ],
    }

    bus_route = {
        "name": "Bus Route",
        "color": "red",
        "points": [
            (45.528, -122.675),
            (45.525, -122.672),
            (45.521, -122.670),
            (45.517, -122.673),
            (45.514, -122.677),
        ],
    }

    return [tram_line, bus_route]


def get_landmarks_data():
    """Basic landmarks: name, type, coordinates."""
    return [
        {
            "name": "City Library",
            "kind": "library",
            "lat": 45.518,
            "lon": -122.678,
        },
        {
            "name": "Central Park",
            "kind": "park",
            "lat": 45.521,
            "lon": -122.685,
        },
        {
            "name": "Art Museum",
            "kind": "museum",
            "lat": 45.522,
            "lon": -122.680,
        },
        {
            "name": "Historic Square",
            "kind": "square",
            "lat": 45.516,
            "lon": -122.676,
        },
        {
            "name": "Riverside Market",
            "kind": "market",
            "lat": 45.513,
            "lon": -122.671,
        },
    ]


def get_heatmap_points():
    """Sample points for a heatmap layer."""
    # For the video we just generate synthetic activity around the centre.
    import random

    lat0, lon0 = CITY_CENTER
    points = []

    # Cluster near the centre
    for _ in range(60):
        lat = lat0 + random.uniform(-0.01, 0.01)
        lon = lon0 + random.uniform(-0.01, 0.01)
        weight = random.uniform(0.5, 1.0)
        points.append((lat, lon, weight))

    # Smaller cluster near the park area
    for _ in range(30):
        lat = 45.521 + random.uniform(-0.005, 0.005)
        lon = -122.685 + random.uniform(-0.005, 0.005)
        weight = random.uniform(0, 0.5)
        points.append((lat, lon, weight))

    return points


def add_routes(m, routes):
    """Add each route as its own toggleable layer."""
    for route in routes:
        fg = folium.FeatureGroup(name=route["name"])

        folium.PolyLine(
            locations=route["points"],
            color=route["color"],
            weight=4,
            opacity=0.8,
        ).add_to(fg)

        # Simple marker at route start
        start_lat, start_lon = route["points"][0]
        folium.Marker(
            location=(start_lat, start_lon),
            popup=f"{route['name']} start",
            icon=folium.Icon(color="gray", icon="bus", prefix="fa"),
        ).add_to(fg)

        fg.add_to(m)


def add_landmarks(m, landmarks):
    """Add landmark markers, grouped by type."""
    groups = {}

    for lm in landmarks:
        kind = lm["kind"]
        if kind not in groups:
            groups[kind] = folium.FeatureGroup(name=f"Landmarks: {kind.title()}")

        folium.Marker(
            location=(lm["lat"], lm["lon"]),
            popup=f"{lm['name']} ({lm['kind']})",
            tooltip=lm["name"],
        ).add_to(groups[kind])

    for fg in groups.values():
        fg.add_to(m)


def add_heatmap_layer(m, points):
    """Add a heatmap layer for intensity."""
    heat_data = [[lat, lon, weight] for (lat, lon, weight) in points]

    HeatMap(
        heat_data,
        name="Activity heatmap",
        radius=18,
        blur=15,
        max_zoom=16,
    ).add_to(m)


# %%
def build_map(mode="full"):
    """
    Build the map for a given mode.
    """
    m = create_base_map()

    if mode in {"routes", "full"}:
        routes = get_routes_data()
        add_routes(m, routes)

    if mode in {"landmarks", "full"}:
        landmarks = get_landmarks_data()
        add_landmarks(m, landmarks)

    if mode in {"heatmap", "full"}:
        heat_points = get_heatmap_points()
        add_heatmap_layer(m, heat_points)

    # Toggle layers on and off in the final map.
    folium.LayerControl(collapsed=False).add_to(m)

    output_name = f"city_story_map_{mode}.html"
    m.save(output_name)
    print(f"Saved {output_name}")


# %%
if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "base"

    valid_modes = {"base", "routes", "landmarks", "heatmap", "full"}
    if mode not in valid_modes:
        mode = "full"

    # %%
    build_map(mode)

# %%
