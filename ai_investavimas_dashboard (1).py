
# AI investavimo aplikacija su pilnu funkcionalumu + AI prognozė

import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
import pandas as pd
import plotly.graph_objs as go
from streamlit_option_menu import option_menu
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
import numpy as np

# Slaptas API raktas
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

# --- Nustatymai ---
tickers = ['QQQ', 'XLE', 'ICLN', 'AAPL', 'MSFT', 'NVDA', 'ARKK']
end_date = datetime.today()
start_date = end_date - timedelta(days=60)
analyzer = SentimentIntensityAnalyzer()

# --- Šoninis meniu ---
with st.sidebar:
    selected = option_menu(
        menu_title="AI Investavimas",
        options=["Apžvalga", "Sentimentas", "Rekomendacijos", "AI prognozė"],
        icons=["graph-up", "chat-left-text", "stars", "cpu"],
        menu_icon="cast",
        default_index=0,
    )

# --- Funkcija: Gauti akcijos grąžą ---
def calculate_returns(ticker):
    data = yf.download(ticker, start=start_date, end=end_date)
    if data.empty:
        return None
    returns = (data['Close'][-1] - data['Close'][0]) / data['Close'][0] * 100
    return round(returns, 2), data

# --- Funkcija: Gauti naujienas ir sentimentą ---
def get_news_sentiment(ticker):
    url = f"https://newsapi.org/v2/everything?q={ticker}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    articles = response.json().get("articles", [])
    results = []
    for article in articles[:10]:
        sentiment = analyzer.polarity_scores(article["title"])
        results.append({
            "title": article["title"],
            "url": article["url"],
            "sentiment": sentiment["compound"]
        })
    return results

# --- Funkcija: AI prognozė ---
def forecast_stock_price(ticker, days):
    df = yf.download(ticker, period="6mo", interval="1d")
    if df.empty or len(df) < 60:
        return None, None

    data = df["Close"].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)

    X = []
    y = []
    for i in range(50, len(scaled_data) - days):
        X.append(scaled_data[i - 50:i])
        y.append(scaled_data[i:i + days])
    X, y = np.array(X), np.array(y)

    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
    model.add(LSTM(50))
    model.add(Dense(days))
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=10, verbose=0)

    last_50 = scaled_data[-50:]
    input_seq = last_50.reshape(1, 50, 1)
    prediction_scaled = model.predict(input_seq)
    prediction = scaler.inverse_transform(prediction_scaled.reshape(-1, 1)).flatten()

    dates = pd.date_range(df.index[-1] + timedelta(days=1), periods=days)
    return df, pd.DataFrame({'Date': dates, 'Predicted Close': prediction})

# --- Apžvalga ---
if selected == "Apžvalga":
    st.title("Akcijų grąžos analizė")
    ticker = st.selectbox("Pasirink akciją", tickers)
    result = calculate_returns(ticker)
    if result:
        returns, data = result
        st.metric(label=f"{ticker} 30 dienų grąža", value=f"{returns}%")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name=ticker))
        fig.update_layout(title=f"{ticker} kainos grafikas", xaxis_title="Data", yaxis_title="Kaina (USD)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nepavyko gauti duomenų.")

# --- Sentimentas ---
elif selected == "Sentimentas":
    st.title("Naujienų sentimentų analizė")
    ticker = st.selectbox("Pasirink akciją naujienų analizei", tickers)
    sentiment_data = get_news_sentiment(ticker)

    if sentiment_data:
        filter_option = st.radio("Filtruoti pagal sentimentą:", ["Visos", "Teigiamos", "Neigiamos"])
        filtered = []
        pos, neg = 0, 0
        for item in sentiment_data:
            if item["sentiment"] >= 0.05:
                pos += 1
                if filter_option in ["Visos", "Teigiamos"]:
                    filtered.append(item)
            elif item["sentiment"] <= -0.05:
                neg += 1
                if filter_option in ["Visos", "Neigiamos"]:
                    filtered.append(item)
            else:
                if filter_option == "Visos":
                    filtered.append(item)

        st.write(f"Teigiamos: {pos} | Neigiamos: {neg}")

        for article in filtered:
            st.write(f"[{article['title']}]({article['url']})")
    else:
        st.warning("Naujienų nerasta.")

# --- Rekomendacijos ---
elif selected == "Rekomendacijos":
    st.title("AI Rekomendacijos")
    recommendations = []
    for ticker in tickers:
        result = calculate_returns(ticker)
        news = get_news_sentiment(ticker)
        if result and news:
            sentiment_score = sum(n['sentiment'] for n in news) / len(news)
            if result[0] > 0 and sentiment_score > 0:
                recommendations.append((ticker, result[0], round(sentiment_score, 2)))

    if recommendations:
        st.success("Šios akcijos turi teigiamą grąžą ir sentimentą:")
        for rec in recommendations:
            st.write(f"**{rec[0]}** - Grąža: {rec[1]}%, Sentimentas: {rec[2]}")
    else:
        st.warning("Nerasta rekomenduojamų akcijų.")

# --- AI prognozė ---
elif selected == "AI prognozė":
    st.title("AI prognozė (LSTM)")
    ticker = st.selectbox("Pasirink akciją AI prognozei", tickers)
    forecast_days = st.slider("Pasirink prognozės trukmę (dienomis)", min_value=1, max_value=14, value=7)
    with st.spinner("Mokome AI modelį..."):
        history, prediction = forecast_stock_price(ticker, forecast_days)
    if history is None or prediction is None:
        st.warning("Nepavyko prognozuoti. Per mažai duomenų.")
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=history.index, y=history['Close'], name="Istorinė kaina"))
        fig.add_trace(go.Scatter(x=prediction['Date'], y=prediction['Predicted Close'], name="Prognozė"))
        fig.update_layout(title=f"{ticker} prognozė ({forecast_days} d.)", xaxis_title="Data", yaxis_title="Kaina (USD)")
        st.plotly_chart(fig, use_container_width=True)
