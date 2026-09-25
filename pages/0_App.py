from src.schemas import HousingInput
from src.model_loader import load_model_bundle

from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox

import folium
import streamlit as st
import pandas as pd
import json

from urllib.request import Request, urlopen
from urllib.parse import urlencode
from pathlib import Path
from src.database import init_database, log_prediction

init_database()

st.write("Klicka på kartan eller använd sökrutan för att välja adress.")

# =========================
# SÖKVÄGAR
# =========================

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = ROOT / "data" / "SwedenHousingPrices.csv"
MODELS_DIR = ROOT / "models"


# =========================
# KOMMUNER
# =========================

@st.cache_data
def get_municipalities() -> list[str]:
    """
    Läser in alla kommuner från datasetet.
    """

    df = pd.read_csv(
        DATA_PATH,
        encoding="utf-8-sig"
    )

    return sorted(
        df["location"]
        .str.split(", ")
        .str[1]
        .dropna()
        .unique()
    )


# =========================
# ADRESSÖKNING MED PHOTON
# =========================

@st.cache_data(ttl=3600)
def search_address(address: str) -> list[dict]:
    """
    Söker efter adresser i Sverige med Photon.
    """

    if not isinstance(address, str):
        return []

    if not address.strip():
        return []

    params = urlencode({
        "q": address,
        "countrycode": "SE",
        "limit": 5,
    })

    url = f"https://photon.komoot.io/api/?{params}"

    request = Request(
        url,
        headers={
            "User-Agent": "boprisindikatorn/1.0"
        }
    )

    try:

        with urlopen(
            request,
            timeout=5
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        results = []

        for feature in data.get(
            "features",
            []
        ):

            properties = feature.get(
                "properties",
                {}
            )

            coordinates = feature.get(
                "geometry",
                {}
            ).get(
                "coordinates",
                []
            )

            if len(coordinates) != 2:
                continue

            longitude, latitude = coordinates

            results.append({
                "name": properties.get(
                    "name",
                    ""
                ),

                "street": properties.get(
                    "street",
                    ""
                ),

                "housenumber": properties.get(
                    "housenumber",
                    ""
                ),

                "postcode": properties.get(
                    "postcode",
                    ""
                ),

                "city": properties.get(
                    "city",
                    ""
                ),

                "latitude": latitude,
                "longitude": longitude,
            })

        return results

    except Exception as error:

        st.error(
            f"Fel vid adressökning: {error}"
        )

        return []


# =========================
# REVERSE GEOCODING
# KOMMUN
# =========================

@st.cache_data(ttl=86400)
def get_municipality_from_coordinates(
    latitude: float,
    longitude: float
) -> str | None:
    """
    Hämtar kommunen från koordinater
    med hjälp av Nominatim.
    """

    params = urlencode({
        "lat": latitude,
        "lon": longitude,
        "format": "jsonv2",
        "addressdetails": 1,
        "accept-language": "sv",
        "zoom": 10,
    })

    url = (
        "https://nominatim.openstreetmap.org/"
        f"reverse?{params}"
    )

    request = Request(
        url,
        headers={
            "User-Agent": "Boprisindikatorn/1.0"
        }
    )

    try:

        with urlopen(
            request,
            timeout=5
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        address = data.get(
            "address",
            {}
        )

        municipality = address.get(
            "municipality"
        )

        if municipality:
            return municipality

        return (
            address.get("city")
            or address.get("town")
            or address.get("village")
        )

    except Exception:

        return None


# =========================
# REVERSE GEOCODING
# ADRESS
# =========================

@st.cache_data(ttl=86400)
def get_address_from_coordinates(
    latitude: float,
    longitude: float
) -> str | None:
    """
    Hämtar en adress från koordinater
    med hjälp av Nominatim.
    """

    params = urlencode({
        "lat": latitude,
        "lon": longitude,
        "format": "jsonv2",
        "addressdetails": 1,
        "accept-language": "sv",
        "zoom": 18,
    })

    url = (
        "https://nominatim.openstreetmap.org/"
        f"reverse?{params}"
    )

    request = Request(
        url,
        headers={
            "User-Agent": "boprisindikatorn/1.0"
        }
    )

    try:

        with urlopen(
            request,
            timeout=5
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        address = data.get(
            "address",
            {}
        )

        road = address.get(
            "road",
            ""
        )

        house_number = address.get(
            "house_number",
            ""
        )

        postcode = address.get(
            "postcode",
            ""
        )

        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or ""
        )

        parts = [
            road,
            house_number,
            postcode,
            city,
        ]

        result = " ".join(
            part
            for part in parts
            if part
        )

        return result or None

    except Exception:

        return None


# =========================
# MATCHA KOMMUN
# =========================

def match_municipality(
    geocoded_municipality: str | None,
    municipalities: list[str]
) -> str | None:
    """
    Matchar kommunen från geocoding-resultatet
    mot kommunerna som finns i datasetet.
    """

    if not geocoded_municipality:
        return None

    # Exakt match
    if geocoded_municipality in municipalities:
        return geocoded_municipality

    # Normalisera kommunnamnet
    geocoded_normalized = (
        geocoded_municipality
        .lower()
        .replace(" kommun", "")
        .replace(" stad", "")
        .strip()
    )

    for municipality in municipalities:

        municipality_normalized = (
            municipality
            .lower()
            .replace(" kommun", "")
            .replace(" stad", "")
            .strip()
        )

        if (
            municipality_normalized
            == geocoded_normalized
        ):
            return municipality

    return None


# =========================
# MODELLER
# =========================

@st.cache_resource
def load_bundle(path: Path) -> dict:
    """
    Laddar en modellbundle och cachar den.
    """

    return load_model_bundle(path)


model_paths = {

    "APARTMENT":
        MODELS_DIR / "apartment_model.joblib",

    "HOUSE":
        MODELS_DIR / "global_model.joblib",

    "ROW_HOUSE":
        MODELS_DIR / "global_model.joblib",
}


# =========================
# STANDARDKOORDINATER
# =========================

if "latitude" not in st.session_state:

    st.session_state.latitude = 55.610181


if "longitude" not in st.session_state:

    st.session_state.longitude = 12.977890


# =========================
# KARTANS CENTRUM
# =========================

if "map_center_latitude" not in st.session_state:

    st.session_state.map_center_latitude = 55.610181


if "map_center_longitude" not in st.session_state:

    st.session_state.map_center_longitude = 12.977890


# =========================
# ADRESS SEARCHBOX STATE
# =========================

if "address_search_version" not in st.session_state:

    st.session_state.address_search_version = 0


if "map_address" not in st.session_state:

    st.session_state.map_address = ""


# streamlit-folium kan returnera samma last_clicked igen efter en rerun.
# Spara därför senast hanterade klick så att ett gammalt klick inte skapar
# en rerun-loop och hindrar adressfältet från att uppdateras.
if "last_handled_map_click" not in st.session_state:

    st.session_state.last_handled_map_click = None


# =========================
# KOMMUNER
# =========================

municipalities = get_municipalities()


if "selected_municipality" not in st.session_state:

    st.session_state.selected_municipality = (
        municipalities[0]
    )


# =========================
# KOLUMN-LAYOUT
# =========================

form_column, map_column = st.columns(
    [1, 1]
)


# =========================
# FORMULÄR
# =========================

with form_column:

    # =========================
    # ADRESSÖKNING
    # =========================

    def address_search_function(
        searchterm: str
    ) -> list[tuple[str, dict]]:
        """
        Funktion som används av st_searchbox.

        Returnerar:
            (text som visas, data som returneras)
        """

        if not isinstance(
            searchterm,
            str
        ):
            return []

        if (
            not searchterm
            or len(searchterm.strip()) < 3
        ):
            return []

        results = search_address(
            searchterm
        )

        suggestions = []

        for result in results:

            parts = [
                result["street"],
                result["housenumber"],
                result["postcode"],
                result["city"],
            ]

            label = " ".join(
                part
                for part in parts
                if part
            )

            if label:

                suggestions.append(
                    (
                        label,
                        {
                            "latitude":
                                result["latitude"],

                            "longitude":
                                result["longitude"],
                            "address": label,
                        }
                    )
                )

        return suggestions

    # =========================
    # ADRESS SEARCHBOX
    # =========================

    address_search_key = (
        f"address_search_"
        f"{st.session_state.address_search_version}"
    )

    address = st_searchbox(
        address_search_function,

        placeholder="Skriv en adress...",

        label="Adress",

        key=address_search_key,

        debounce=300,

        default=(
            st.session_state.map_address
            or None
        ),

        default_searchterm=(
            st.session_state.map_address
        ),

        default_use_searchterm=True,

        edit_after_submit="current",

        style_overrides={
            "searchbox": {
                "optionEmpty": "hidden",
            },
        },
    )

    # =========================
    # VALD ADRESS
    # =========================

    if isinstance(address, dict):

        new_latitude = address[
            "latitude"
        ]

        new_longitude = address[
            "longitude"
        ]

        position_changed = (
            st.session_state.latitude
            != new_latitude
            or
            st.session_state.longitude
            != new_longitude
        )

        if position_changed:

            st.session_state.pop("prediction_result", None)

            # Uppdatera pinnens position.

            st.session_state.latitude = (
                new_latitude
            )

            st.session_state.longitude = (
                new_longitude
            )

            # =========================
            # FLYTTA KARTANS CENTRUM
            # VID ADRESSÖKNING
            # =========================

            st.session_state.map_center_latitude = (
                new_latitude
            )

            st.session_state.map_center_longitude = (
                new_longitude
            )

            # =========================
            # HÄMTA KOMMUN
            # =========================

            geocoded_municipality = (
                get_municipality_from_coordinates(
                    new_latitude,
                    new_longitude
                )
            )

            matched_municipality = (
                match_municipality(
                    geocoded_municipality,
                    municipalities
                )
            )

            if matched_municipality:

                st.session_state.selected_municipality = (
                    matched_municipality
                )

            # Nollställ eventuell
            # gammal kartadress.

            st.session_state.map_address = ""

            st.rerun()

    # =========================
    # PREDIKTIONSFORMULÄR
    # =========================

    with st.form(
        "prediction_form"
    ):

        typology_labels = {

            "APARTMENT":
                "Lägenhet",

            "HOUSE":
                "Villa",

            "ROW_HOUSE":
                "Radhus",
        }

        # =========================
        # BOSTADSTYP
        # =========================

        typology = st.selectbox(

            "Bostadstyp",

            list(
                typology_labels.keys()
            ),

            format_func=lambda x:
                typology_labels[x]
        )

        # =========================
        # BOAREA
        # =========================

        living_area = st.number_input(

            "Boarea (m²)",

            min_value=1,

            value=80,

            step=1
        )

        # =========================
        # TOMTAREA
        # =========================

        land_area = st.number_input(

            "Tomtarea (m²)",

            min_value=0,

            value=0,

            step=10
        )

        # =========================
        # ANTAL RUM
        # =========================

        number_rooms = st.number_input(

            "Antal rum",

            min_value=1,

            value=3,

            step=1
        )

        # =========================
        # BERÄKNA PRIS
        # =========================

        submitted = st.form_submit_button(
            "Beräkna pris"
        )


# =========================
# KARTA
# =========================

with map_column:

    # Kartan använder sitt eget centrum.
    #
    # Det betyder att ett kartklick
    # inte flyttar kartans vy.

    m = folium.Map(

        location=[
            st.session_state.map_center_latitude,
            st.session_state.map_center_longitude
        ],

        # zoom_start=10,

        # min_zoom=4,

        # max_bounds=True,

        # max_bounds_viscosity=1.0
    )

    # =========================
    # MARKÖR
    # =========================

    folium.Marker(

        location=[

            st.session_state.latitude,

            st.session_state.longitude
        ],

        tooltip="Vald position",

        icon=folium.Icon(
            icon="home"
        )

    ).add_to(m)

    # =========================
    # VISA KARTA
    # =========================

    map_data = st_folium(

        m,

        width=300,

        height=500,

        key="property_location_map",

        returned_objects=[
            "last_clicked",
            "center"
        ]
    )

    # =========================
    # KARTKLICK
    # =========================

    last_clicked = map_data.get("last_clicked")

    click_signature = (
        round(last_clicked["lat"], 7),
        round(last_clicked["lng"], 7),
    ) if last_clicked else None

    if (
        last_clicked
        and click_signature
        != st.session_state.last_handled_map_click
    ):
        st.session_state.pop("prediction_result", None)
        # Markera klicket som hanterat före nätverksanrop och rerun.
        st.session_state.last_handled_map_click = click_signature

        new_latitude = (
            last_clicked["lat"]
        )

        new_longitude = (
            last_clicked["lng"]
        )

        # =========================
        # SPARA PINNENS POSITION
        # =========================

        st.session_state.latitude = (
            new_latitude
        )

        st.session_state.longitude = (
            new_longitude
        )

        # =========================
        # SPARA KARTANS NUVARANDE
        # CENTRUM
        # =========================

        if map_data.get("center"):

            st.session_state.map_center_latitude = (
                map_data["center"]["lat"]
            )

            st.session_state.map_center_longitude = (
                map_data["center"]["lng"]
            )

        # =========================
        # HÄMTA ADRESS
        # =========================

        clicked_address = (
            get_address_from_coordinates(
                new_latitude,
                new_longitude
            )
        )

        # =========================
        # HÄMTA KOMMUN
        # =========================

        geocoded_municipality = (
            get_municipality_from_coordinates(
                new_latitude,
                new_longitude
            )
        )

        # =========================
        # MATCHA KOMMUN
        # =========================

        matched_municipality = (
            match_municipality(
                geocoded_municipality,
                municipalities
            )
        )

        if matched_municipality:

            st.session_state.selected_municipality = (
                matched_municipality
            )

        # =========================
        # FYLL ADRESSFÄLTET
        # =========================

        if clicked_address:

            st.session_state.map_address = (
                clicked_address
            )

            st.session_state.address_search_version += 1

        else:

            st.session_state.map_address = ""

        # =========================
        # RITA OM SIDAN
        # =========================

        st.rerun()


# =========================
# PREDIKTION
# =========================

if submitted:

    # =========================
    # LADDA VALD MODELL
    # =========================

    bundle = load_bundle(
        model_paths[typology]
    )

    # =========================
    # PIPELINE
    # =========================

    pipeline = bundle[
        "pipeline"
    ]

    # =========================
    # VALIDERING MED PYDANTIC
    # =========================

    housing_input = HousingInput(

        typology=typology,

        municipality=(
            st.session_state.selected_municipality
        ),

        land_area_sqm=land_area,

        living_area_sqm=living_area,

        number_rooms=number_rooms,

        latitude=st.session_state.latitude,

        longitude=st.session_state.longitude,
    )

    # =========================
    # OMVANDLA TILL DICTIONARY
    # =========================

    user_input = (
        housing_input.model_dump()
    )

    # =========================
    # TOMTLOGIK
    # =========================

    user_input[
        "has_land_area"
    ] = int(
        land_area > 0
    )

    # Lägenheter har ingen relevant
    # tomtarea.

    if typology == "APARTMENT":

        user_input[
            "land_area_sqm"
        ] = None

    # För villor används tomtarea endast
    # om den är minst 50 m².

    if (
        typology == "HOUSE"
        and land_area < 50
    ):

        user_input[
            "land_area_sqm"
        ] = None

    # =========================
    # SKAPA MODELLINPUT
    # =========================

    model_input = pd.DataFrame(
        [user_input]
    )

    # =========================
    # GÖR PREDIKTION
    # =========================

    prediction = float(

        pipeline.predict(
            model_input
        )[0]
    )

    # =========================
    # HÄMTA MAE
    # =========================

    if typology == "APARTMENT":

        mae = float(

            bundle[
                "metrics"
            ][
                "mae"
            ]
        )

    else:

        mae = float(

            bundle[
                "metrics_by_segment"
            ][
                typology
            ][
                "mae"
            ]
        )

    # =========================
    # PRISINTERVALL
    # =========================

    lower_price = max(

        0,

        prediction - mae
    )

    upper_price = (

        prediction + mae
    )

    # =========================
    # LOGGA PREDIKTION
    # =========================

    log_prediction(
        address=(
            address.get("address", "")
            if isinstance(address, dict)
            else address
        ) or st.session_state.map_address,
        latitude=st.session_state.latitude,
        longitude=st.session_state.longitude,
        municipality=st.session_state.selected_municipality,
        property_type=typology,
        living_area=living_area,
        land_area=land_area,
        predicted_price=prediction,
        lower_price=lower_price,
        upper_price=upper_price,
        model_name=typology,
        number_rooms=number_rooms,
    )

    # Undertryck popupen för den egna prediktionen.
    st.session_state.just_created_prediction = True


# =========================
# SPARA PREDIKTIONSRESULTAT
# =========================

if submitted:

    st.session_state["prediction_result"] = {
        "prediction": prediction,
        "lower_price": lower_price,
        "upper_price": upper_price,
        "mae": mae,
    }


# =========================
# VISA PREDIKTIONSRESULTAT
# =========================

result = st.session_state.get("prediction_result")

if result:

    prediction = result["prediction"]
    lower_price = result["lower_price"]
    upper_price = result["upper_price"]
    mae = result["mae"]

    st.html(
        f"""
        <div id="result" style="
            border-radius: 12px;
            padding: 28px;
            margin-top: 25px;
            text-align: center;
            border: 1px solid #dbe2ea;
        ">

            <div style="
                font-size: 22px;
                font-weight: 600;
                margin-bottom: 10px;
            ">
                🏠 Uppskattat utgångspris
            </div>

            <div style="
                font-size: 42px;
                font-weight: 700;
                margin-bottom: 20px;
            ">
                {prediction:,.0f} kr
            </div>

            <div style="
                font-size: 17px;
                margin-bottom: 6px;
            ">
                Ungefärligt prisintervall
            </div>

            <div style="
                font-size: 25px;
                font-weight: 600;
            ">
                {lower_price:,.0f}
                –
                {upper_price:,.0f} kr
            </div>

            <div style="
                font-size: 14px;
                margin-top: 14px;
                opacity: 0.7;
            ">
                Modellens genomsnittliga fel:
                ± {mae:,.0f} kr
            </div>

        </div>

        <script>
            setTimeout(function() {{
                const result = document.getElementById("result");

                if (result) {{
                    result.scrollIntoView({{
                        behavior: "smooth",
                        block: "center"
                    }});
                }}
            }}, 200);
        </script>
        """,
        unsafe_allow_javascript=True
    )
