# import seaborn as sns
import plotly.express as px
from faicons import icon_svg
import re

from shared import app_dir, df

from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import output_widget, render_widget

import matplotlib.pyplot as plt


def plot_bar_chart(df, x, y, hue=None):
    # Paleta de colores suaves
    pastel_colors = [
        "#D1BAFF",   # Pastel Lavender
        "#FFDFBA",  # Pastel Orange
        "#BAFFC9",  # Pastel Green
        "#FFFFBA",  # Pastel Yellow
        "#BAE1FF",  # Pastel Blue
        "#E1BAFF",  # Pastel Purple
        "#FFC9DE",  # Pastel Pink
        "#C9FFD5",  # Pastel Mint
        "#FFD1DC",  # Pastel Peach
        "#FFB3BA"  # Pastel Red
    ]
    hover_data = {x: True, y: True}
    if "Polymer Types" in df.columns:
        hover_data["Polymer Types"] = True
    if hue is not None:
        hover_data[hue] = True
        df.sort_values(by=hue)

    fig = px.bar(
        df,
        x=x,
        y=y,
        color=hue,
        hover_data=hover_data,
        color_discrete_sequence=pastel_colors
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis=dict(showticklabels=False),
        yaxis=dict(range=[0, df[y].max() * 0.1]),  # Limita la extensión del eje Y
        template='plotly_white'
    )
    return fig

ui.page_opts(title="Additives dashboard", fillable=True)

with ui.sidebar(title="Filter controls"):
    ui.input_checkbox_group(
        "polymer",
        "Polymer Type",
        ["PP", "PE", "PS", "Polyester", "PVC", "Nylon", "PET", "PA", "PUR"],
        selected=["PP", "PE", "PS", "Polyester", "PVC", "Nylon", "PET", "PA", "PUR"]
    )

    ui.input_radio_buttons(
        "compartment",
        "Compartment",
        ["Sediment", "Seawater", "Biota"],
        selected="Sediment",
    )

with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("atom")):
        "Number of additives"

        @render.text
        def count():
            list_of_additives = list(set(filtered_df()["Additive"]))
            return len(list_of_additives)

    with ui.value_box(showcase=icon_svg("file")):
        "Number of references"

        @render.text
        def count_ref():
            list_of_papers = list(set(filtered_df()["Reference"]))
            return len(list_of_papers)


with ui.layout_columns(col_widths=[12, 12]):
    with ui.card(full_screen=True):
        ui.card_header("Additives concentrarion in Plastic")

        @render_widget
        def plot_concentrations_in_plastic():
            df_temp = filtered_df()[(filtered_df()["Compartment"]=="Plastic") & (~filtered_df()["Common Additives"].isna())]
            df = df_temp.sort_values("Additive Abbrev").reset_index(drop=True)
            df = df.groupby('Additive Abbrev').agg({"Concentration(ug/g)":"median","Polymer Types":"max", "Polymers Number":"max"}).reset_index()
            
            return plot_bar_chart(df, x="Additive Abbrev", y="Concentration(ug/g)", hue="Polymers Number")

    with ui.card(full_screen=True):
        ui.card_header("Additives concentrarion selected compartment")

        @render_widget
        def plot_concentrations_in_other_compartment():
            df_temp = filtered_df()[(filtered_df()["Compartment"]!="Plastic") & (~filtered_df()["Common Additives"].isna())]
            df = df_temp.sort_values("Additive Abbrev").reset_index(drop=True)
            df = df.groupby('Additive Abbrev').agg({"Concentration(ug/g)":"median","Polymer Types":"max", "Polymers Number":"max"}).reset_index()
            return plot_bar_chart(df, x="Additive Abbrev", y="Concentration(ug/g)", hue="Polymers Number")


ui.include_css(app_dir / "styles.css")


@reactive.calc
def filtered_df():
    compartments_to_plot = ["Plastic", input.compartment()]
    filt_df = df[df["Compartment"].isin(compartments_to_plot)].copy()

    # Crear un patrón de regex para los polímeros seleccionados
    selected_polymers = input.polymer()
    pattern = '|'.join(selected_polymers)

    # Asegurarse de que no haya valores nulos en la columna 'Polymer Type'
    filt_df['Polymer Types'] = filt_df['Polymer Types'].fillna('')
    
    # Filtrar el DataFrame donde la columna 'Polymer Type' contiene alguno de los polímeros seleccionados
    filt_df = filt_df[filt_df["Polymer Types"].str.contains(pattern, flags=re.IGNORECASE, regex=True)]

    return filt_df

