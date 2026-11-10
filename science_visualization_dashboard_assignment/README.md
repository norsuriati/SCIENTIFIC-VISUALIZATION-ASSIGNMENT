# Malaysia Cost of Living Dashboard

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Keep `analysis.py` beside `app.py`, and `merged_dataset.csv` inside `data/`.

## Views
1. Income growth vs Overall CPI growth by state, with Mean/Median income selection.
2. Population vs mean monthly household income, with Overall CPI shown by point colour.
3. Ranked spending-category CPI growth or state Overall CPI growth.

## Design
Compact header, top comparison filter, navigation-only sidebar, and a consistent palette:
teal = income; coral = price growth; navy/grey = text and neutral UI.
Only years present in the dataset are selectable. No map, heatmap, line or dumbbell chart.
