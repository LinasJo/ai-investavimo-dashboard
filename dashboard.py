import yfinance as yf
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
import streamlit as st
import pandas as pd

NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

tickers = ['QQQ', 'XLE', 'ICLN', 'AAPL', 'MSFT', 'NVDA', 'ARKK']
end_date = datetime.today()
start_date = end_date - timedelta(days=30)

def calculate_returns(ticker):
    data = yf.download(ticker, start=start_date, end=end_date)
    if data.empty:
        return None, None
    price_start = data['Adj Close'][0]
    price_end = data['Adj Close'][-1]
    grąža = (price_end - price_start) / price_start * 100
    return grąža, data['Adj Close']

def get_news_sentiment(ticker):
    url = f"https://newsapi.org/v2/everything?q={ticker}&apiKey={NEWS_API_KEY}&language=en"
    response = requests.get(url)
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = 0
    if response.status_code == 200:
        articles = response.json().get('articles', [])[:5]
        for article in articles:
            text = article['title'] + '. ' + article.get('description', '')
            score = analyzer.polarity_scores(text)['compound']
            sentiment_score += score
        return sentiment_score / max(len(articles), 1)
    else:
        return 0

def generate_recommendation(ret, sentiment):
    if ret > 2 and sentiment > 0.2:
        return "Laikyti (stiprus signalas)"
    elif ret > 0 and sentiment > 0:
        return "Laikyti"
    elif ret < 0 and sentiment < 0:
        return "Saugotis"
    else:
        return "Atsargiai"

st.title("AI Investavimo Asistentas")
st.write("30 dienų grąžos ir sentimentų analizė")

ataskaita = []

for ticker in tickers:
    grąža, prices = calculate_returns(ticker)
    sentimentas = get_news_sentiment(ticker)
    if grąža is not None:
        rekomendacija = generate_recommendation(grąža, sentimentas)
        ataskaita.append({
            "Turtas": ticker,
            "Grąža (%)": round(grąža, 2),
            "Sentimentas": round(sentimentas, 2),
            "Rekomendacija": rekomendacija
        })
        st.subheader(ticker)
        st.line_chart(prices)
        st.write(f"**Grąža**: {grąža:.2f}% | **Sentimentas**: {sentimentas:.2f} | **{rekomendacija}**")
    else:
        st.write(f"{ticker}: Duomenų nėra")

if ataskaita:
    df = pd.DataFrame(ataskaita)
    st.dataframe(df.set_index("Turtas"))
