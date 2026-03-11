import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Output, Input

df = pd.read_csv("Meteorite_Landings.csv")
print("loaded", len(df), "rows")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df = df.rename(columns={"reclat": "lat", "reclong": "lon", "mass_(g)": "mass_g"})
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["mass_g"] = pd.to_numeric(df["mass_g"], errors="coerce")
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df = df.dropna(subset=["lat", "lon", "mass_g", "year"])
df = df[(df["year"] >= 1800) & (df["year"] <= 2013) & (df["mass_g"] > 0)]
df["broad_class"] = df["recclass"].str.extract(r"^([A-Za-z]+)")[0].fillna("Unknown")

top_classes = df["broad_class"].value_counts().head(15).index.tolist()

#App

app = Dash(__name__, title="Meteorite Explorer")
server = app.server

app.layout = html.Div(style={"fontFamily": "sans-serif", "maxWidth": "1100px", "margin": "0 auto", "padding": "20px"}, children=[

    html.H1("NASA Meteorite Landings Explorer", style={"marginBottom": "4px"}),
    html.P("Filter all meteorite records using the controls below. All charts update live.",
           style={"color": "gray", "marginTop": "0"}),

    html.Div(style={"display": "flex", "gap": "30px", "flexWrap": "wrap", "marginBottom": "24px",
                    "padding": "16px", "background": "#f8f8f8", "borderRadius": "8px"}, children=[

        html.Div([
            html.Label("Meteorite Class", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="class-dd",
                options=[{"label": c, "value": c} for c in sorted(top_classes)],
                multi=True, placeholder="All classes…",
                style={"minWidth": "200px"},
            ),
        ]),

        html.Div([
            html.Label("Fall Type", style={"fontWeight": "bold"}),
            dcc.RadioItems(
                id="fall-radio",
                options=[{"label": " All", "value": "All"},
                         {"label": " Fell", "value": "Fell"},
                         {"label": " Found", "value": "Found"}],
                value="All",
                labelStyle={"display": "block"},
            ),
        ]),

        html.Div([
            html.Label("Year Range", style={"fontWeight": "bold"}),
            dcc.RangeSlider(
                id="year-slider",
                min=1800, max=2025,
                value=[1800, 2025],
                marks={1800: "1800", 1850: "1850", 1900: "1900",
                       1950: "1950", 2000: "2000", 2025: "2025"},
                tooltip={"placement": "bottom", "always_visible": True},
            ),
        ], style={"minWidth": "280px"}),

        html.Div([
            html.Label("Min Mass (g)", style={"fontWeight": "bold"}),
            dcc.Input(id="mass-input", type="number", value=0, min=0,
                      style={"width": "100px", "display": "block", "marginTop": "4px"}),
        ]),
        html.Div([
            html.Label("Max Mass (g)", style={"fontWeight": "bold"}),
            dcc.Input(id="max-mass-input", type="number", value=1000000, min=0,
                      style={"width": "100px", "display": "block", "marginTop": "4px"}),
        ]),

    ]),

    dcc.Graph(id="map-fig"),
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"}, children=[
        dcc.Graph(id="timeline-fig"),
        dcc.Graph(id="mass-fig"),
    ]),
    dcc.Graph(id="class-fig"),

])

#Callback

@app.callback(
    Output("map-fig", "figure"),
    Output("timeline-fig", "figure"),
    Output("mass-fig", "figure"),
    Output("class-fig", "figure"),
    Input("class-dd", "value"),
    Input("fall-radio", "value"),
    Input("year-slider", "value"),
    Input("mass-input", "value"),
    Input("max-mass-input", "value"),
)
def update(classes, fall, year_range, min_mass, max_mass):
    print(f"update called: year={year_range}, min={min_mass}, max={max_mass}, classes={classes}, fall={fall}")
    fdf = df.copy()
    if classes:
        fdf = fdf[fdf["broad_class"].isin(classes)]
    if fall != "All":
        fdf = fdf[fdf["fall"] == fall]
    if year_range:
        fdf = fdf[(fdf["year"] >= year_range[0]) & (fdf["year"] <= year_range[1])]
    if min_mass is not None and max_mass is not None:
        fdf = fdf[fdf["mass_g"].between(min_mass or 0, max_mass or 1000000)]

    map_fig = px.scatter_geo(
        fdf.sample(min(len(fdf), 8000), random_state=42),
        lat="lat", lon="lon", color="fall",
        size="mass_g", size_max=20,
        hover_name="name", hover_data={"year": True, "mass_g": True, "recclass": True},
        projection="natural earth",
        title=f"Global Distribution — {len(fdf):,} meteorites",
    )

    timeline_fig = px.histogram(
        fdf, x="year", color="fall", nbins=50,
        title="Landings Per Year",
        labels={"year": "Year", "count": "Count"},
    )

    mass_fig = px.histogram(
        fdf, x="mass_g", color="fall", nbins=60, title="Mass Distribution",
        labels={"mass_g": "Mass (g)"},
    )

    class_counts = fdf["broad_class"].value_counts().head(12).reset_index()
    class_counts.columns = ["class", "count"]
    class_fig = px.bar(
        class_counts, x="class", y="count",
        title="Top 12 Meteorite Classes",
        labels={"class": "Class", "count": "Count"},
    )

    return map_fig, timeline_fig, mass_fig, class_fig


if __name__ == "__main__":
    app.run(debug=True, port=8052)
