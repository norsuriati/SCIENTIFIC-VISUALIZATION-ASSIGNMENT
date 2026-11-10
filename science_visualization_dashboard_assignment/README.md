# Malaysia Cost of Living Dashboard

Streamlit dashboard for JIE42403 Scientific Visualisation.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Keep `analysis.py` beside `app.py` and `merged_dataset.csv` inside `data/`.

## Dashboard structure
1. Income growth vs overall CPI growth by state (grouped horizontal bar chart).
2. Population vs mean household income, with Overall CPI shown by bubble size and colour (bubble scatter plot).
3. State ranking by overall or selected spending-category CPI growth (ranked horizontal bar chart).

The dashboard contains no map, heatmap, line chart or dumbbell chart. All calculations use the supplied dataset; no synthetic values are generated.
