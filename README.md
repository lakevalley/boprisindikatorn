# Boprisindikatorn

Boprisindikatorn är en Streamlitapp som uppskattar **utgångspriset** för lägenheter, villor och radhus i Sverige. Användaren anger bostadstyp, läge, boarea och andra bostadsuppgifter och får en uppskattning från en tränad maskininlärningsmodell. Appen innehåller också sidor där man kan utforska geografiska prisskillnader, boareans betydelse och statistik. Målet är att visa ett helt flöde från rådata och modellträning till en användbar applikation.

Uppskattningen gäller annonsens utgångspris, inte bostadens slutpris. Den ska ses som en indikation, inte som en värdering av en enskild bostad.

## Testa appen

[Öppna Boprisindikatorn](https://boprisindikatorn.streamlit.app/)

## Kör lokalt

Projektet använder Python 3.14 och [uv](https://docs.astral.sh/uv/getting-started/installation/) för att installera beroenden från `pyproject.toml` och `uv.lock`. Installera Git och uv först. Öppna sedan en terminal och kör:

```bash
git clone https://github.com/lakevalley/boprisindikatorn.git
cd boprisindikatorn
uv sync
uv run streamlit run app.py
```

`uv sync` skapar projektets virtuella miljö och installerar rätt Pythonversion och beroenden vid behov. Du behöver inte aktivera miljön manuellt. När Streamlit startar öppnar du adressen som visas i terminalen, vanligtvis `http://localhost:8501`. Avsluta med `Ctrl+C`.

Om du vill installera uv i Windows PowerShell kan du använda `winget install --id=astral-sh.uv -e` och sedan öppna en ny terminal. För andra operativsystem finns installationsanvisningar i länken ovan.

De två modellfiler som appen använder finns i `models/`. Lägenheter använder lägenhetsmodellen, medan villor och radhus använder globalmodellen. Det behövs alltså ingen egen modellträning för att starta appen.

## Så fungerar projektet

Rådata läses från `data/SwedenHousingPrices.csv`. I `notebooks/model_training.ipynb` tvättas datan, delas upp i träning, validering och test och används för att jämföra en enkel baslinje med flera modeller. Både en global modell och separata modeller per bostadstyp har utvärderats. De modeller som appen använder har sparats som färdiga pipelines i `models/`, så appen behöver inte träna om dem vid varje start.

Streamlit samlar in bostadsuppgifter och visar uppskattningen. SQLite lagrar gjorda uppskattningar i `data/boprisindikatorn.db`. Notebookarna för geografi och boarea undersöker hur dessa variabler påverkar modellens resultat. [Den tekniska rapporten](docs/teknisk_rapport.md) sammanfattar arbetet, resultaten och möjliga förbättringar.

## Projektstruktur

```text
boprisindikatorn/
├── app.py                         # Startpunkt och navigering i Streamlit
├── pages/
│   ├── 0_App.py                   # Prisuppskattning
│   ├── 1_Geografi.py              # Geografisk analys
│   ├── 2_Boarea.py                # Analys av boarea
│   └── 3_Statistik.py             # Statistik över uppskattningar
├── src/
│   ├── database.py                # SQLite och sparade uppskattningar
│   ├── geography.py               # Geografiska hjälpfunktioner
│   ├── model_loader.py            # Inläsning av sparade modeller
│   └── schemas.py                 # Validering av indata
├── notebooks/
│   ├── model_training.ipynb       # Datatvätt, modellval och slutligt test
│   ├── geography_hypothesis.ipynb # Hypotes om geografi
│   ├── H2-living-area.ipynb       # Hypotes om boarea
│   ├── H3-model-comparison.ipynb  # Modelljämförelse
│   └── legacy/                    # Tidigare träningsarbete
├── data/                           # Rådata, bearbetad data och analysresultat
│   └── h2/                        # Underlag till boareaanalysen
├── models/                         # Färdiga globala och lägenhetsmodeller
├── docs/
│   └── teknisk_rapport.md         # Gemensam teknisk rapport
├── pyproject.toml                  # Projektets beroenden och Pythonkrav
└── uv.lock                         # Låsta beroendeversioner
```

## Träna modellerna själv

Öppna `notebooks/model_training.ipynb` i VS Code eller Jupyter och kör cellerna i ordning. Notebooken skapar modeller för global data, lägenheter, villor och radhus i `models/`. Appen är i nuläget konfigurerad att läsa de två filer som nämns ovan. De separata villa och radhusmodellerna används för jämförelse och kopplas inte automatiskt in i appen.

För att använda notebooken i VS Code väljer du projektets `.venv` som Pythonmiljö och Jupyterkärna efter `uv sync`.
