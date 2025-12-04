#!/usr/bin/env python3
"""Interactive Dash app with scatter plot from CSV."""
from pathlib import Path

import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc


CSV_PATH = Path("pitching_advanced_20IPmin.csv")


def load_data(path: Path) -> pd.DataFrame:
    """Load CSV file."""
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path.resolve()}")
    return pd.read_csv(path)


def create_app(df: pd.DataFrame) -> Dash:
    """Create and return the Dash app."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    all_cols = df.columns.tolist()
    teams = sorted(df["Team"].unique()) if "Team" in df.columns else []

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dbc.Container(
        # layout with title, instructions, dropdowns, and graph
        [
            html.H2("2025 Minor League Pitching Interactive Scatter Plot"),
            html.H4("This app allows you to create scatter plots from minor league pitching data."),
            # create list of intrustions
            html.Ul(
                [
                    html.Li("Select X and Y axes from the dropdowns."),
                    html.Li("Optionally select color and size dimensions."),
                    html.Li("Filter data by team or parameter values."),
                    html.Li("Select additional columns to display on hover."),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("X axis"),
                            dcc.Dropdown(
                                id="x-col",
                                options=[{"label": c, "value": c} for c in numeric_cols],
                                value=numeric_cols[0] if numeric_cols else None,
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Y axis"),
                            dcc.Dropdown(
                                id="y-col",
                                options=[{"label": c, "value": c} for c in numeric_cols],
                                value=numeric_cols[1] if len(numeric_cols) > 1 else None,
                            ),
                        ],
                        md=6,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Color by (optional)"),
                            dcc.Dropdown(
                                id="color-col",
                                options=[{"label": c, "value": c} for c in all_cols],
                                value=None,
                                clearable=True,
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Size by (optional)"),
                            dcc.Dropdown(
                                id="size-col",
                                options=[{"label": c, "value": c} for c in numeric_cols],
                                value=None,
                                clearable=True,
                            ),
                        ],
                        md=6,
                    ),
                ],
                style={"marginTop": "12px"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Filter by Team (optional)"),
                            dcc.Dropdown(
                                id="team-filter",
                                options=[{"label": t, "value": t} for t in teams],
                                value=[],
                                multi=True,
                            ),
                        ],
                        md=12,
                    ),
                ],
                style={"marginTop": "12px"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Hover Info (optional)"),
                            dcc.Dropdown(
                                id="hover-cols",
                                options=[{"label": c, "value": c} for c in all_cols],
                                value=[],
                                multi=True,
                            ),
                        ],
                        md=12,
                    ),
                ],
                style={"marginTop": "12px"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Parameter Filter (optional)"),
                            dcc.Dropdown(
                                id="param-col",
                                options=[{"label": c, "value": c} for c in numeric_cols],
                                value=None,
                                clearable=True,
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Operator"),
                            dcc.Dropdown(
                                id="param-op",
                                options=[
                                    {"label": ">", "value": ">"},
                                    {"label": ">=", "value": ">="},
                                    {"label": "<", "value": "<"},
                                    {"label": "<=", "value": "<="},
                                    {"label": "=", "value": "="},
                                ],
                                value=">",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Value"),
                            dcc.Input(
                                id="param-value",
                                type="number",
                                placeholder="Enter value",
                                style={"width": "100%", "padding": "5px"},
                            ),
                        ],
                        md=4,
                    ),
                ],
                style={"marginTop": "12px"},
            ),
            html.Hr(),
            dcc.Loading(dcc.Graph(id="scatter", style={"height": "70vh"})),
        ],
        fluid=True,
    )

    @app.callback(
        Output("scatter", "figure"),
        [
            Input("x-col", "value"),
            Input("y-col", "value"),
            Input("color-col", "value"),
            Input("size-col", "value"),
            Input("team-filter", "value"),
            Input("hover-cols", "value"),
            Input("param-col", "value"),
            Input("param-op", "value"),
            Input("param-value", "value"),
        ],
    )
    def update_scatter(x_col, y_col, color_col, size_col, selected_teams, hover_cols, param_col, param_op, param_value):
        """Update scatter plot based on selected columns and filters."""
        if not x_col or not y_col:
            return {"data": [], "layout": {"title": "Select X and Y columns"}}

        # Filter by selected teams
        filtered_df = df[df["Team"].isin(selected_teams)] if selected_teams else df

        # Filter by parameter if specified
        if param_col and param_value is not None:
            if param_op == ">":
                filtered_df = filtered_df[filtered_df[param_col] > param_value]
            elif param_op == ">=":
                filtered_df = filtered_df[filtered_df[param_col] >= param_value]
            elif param_op == "<":
                filtered_df = filtered_df[filtered_df[param_col] < param_value]
            elif param_op == "<=":
                filtered_df = filtered_df[filtered_df[param_col] <= param_value]
            elif param_op == "=":
                filtered_df = filtered_df[filtered_df[param_col] == param_value]

        # Build hover data list from valid columns
        # Always include 'Name' by default (if present) and then any user-selected columns
        default_hover = ["Name"] if "Name" in filtered_df.columns else []
        selected_hover = [col for col in (hover_cols or []) if col in filtered_df.columns and col != "Name"]
        hover_list = default_hover + selected_hover
        hover_data = hover_list if hover_list else False

        fig = px.scatter(
            filtered_df,
            x=x_col,
            y=y_col,
            color=color_col if color_col in filtered_df.columns else None,
            size=size_col if size_col in filtered_df.columns else None,
            hover_data=hover_data,
            title=f"{x_col} vs {y_col}",
            template="plotly_white",
        )
        return fig

    return app


# Load data and create app for deployment
df = load_data(CSV_PATH)
app = create_app(df)
server = app.server  # Expose Flask server for gunicorn


def run():
    """Load data and run the Dash app."""
    app.run(debug=True, host="127.0.0.1", port=8053)


if __name__ == "__main__":
    run()
