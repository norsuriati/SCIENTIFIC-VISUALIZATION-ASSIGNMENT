# Malaysia States Dashboard (2017–2023)

Streamlit app for **JIE42403 Scientific Visualisation**. Three pages, one objective each, each with a summary box, three interactive Plotly visualisations and an interpretation.

| Page | Objective | Visualisations |
|---|---|---|
| 1 · Population growth | Population growth by state, 2017–2023 | line plot · growth heatmap · bubble map |
| 2 · Household income | Mean vs median income by state (survey years 2019, 2020, 2022) | dumbbell plot · scatter · bubble map |
| 3 · Marriage trends | Marriage counts and rates by state, 2017–2023 | line plot · heatmap · scatter |

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (GitHub → Streamlit Community Cloud)
1. Push this folder to a GitHub repository (see commands below).
2. Go to <https://share.streamlit.io>, sign in with GitHub and click **Create app**.
3. Pick the repository, branch `main`, main file path `app.py`, then **Deploy**.
4. Every later `git push` redeploys the app automatically. Submit the app URL with your report.

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

## Files
- `app.py` – layout, charts and interpretation text
- `dashboard_data.py` – data loading and calculations (pure pandas)
- `data/` – CSVs. `population_state.csv` is the original file trimmed to 2017–2023 and `ethnicity = overall`; the other two are unchanged.
- `requirements.txt`, `.streamlit/config.toml`

## Data notes (also discussed in the app)
- **Income** is only surveyed in some years; 2019, 2020 and 2022 are the only ones in 2017–2023.
- **Population** shows a large step change between 2019 and 2020 (e.g. Sabah −12%, Perlis +12%), most likely a re-basing of the series rather than real movement. The app flags this.
- **Marriages**: Perak male 2023 has a published rate (30.8) inconsistent with its count; it is flagged and excluded from rate averages by default (checkbox on page 3). 2024 data is outside the study window and is not used.
- Source: Department of Statistics Malaysia (DOSM) open data (data.gov.my) – confirm and cite the exact dataset pages in your report.
