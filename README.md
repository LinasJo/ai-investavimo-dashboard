# AI Investavimo Asistentas

Šis projektas naudoja AI (sentimentų analizę) ir akcijų rinkos duomenis, kad sugeneruotų rekomendacijas investuotojams.

## Funkcijos
- 30 dienų kainų grąžos analizė
- Sentimentų analizė pagal naujienas (NewsAPI)
- Vizualizacijos Streamlit'e
- Rekomendacijos (laikyti, atsargiai, saugotis)

## Paleidimas Streamlit Cloud

1. Įkelk šį projektą į GitHub
2. Eik į [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. Prijunk repozitoriją ir paleisk `dashboard.py`
4. „Secrets“ skiltyje pridėk:

```
NEWS_API_KEY = tavo_api_raktas
```

Viskas – tavo AI dashboard veikia!
