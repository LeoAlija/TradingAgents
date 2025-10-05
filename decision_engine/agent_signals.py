#### `decision_engine/agent_signals.py`


import os
from dotenv import load_dotenv
import requests

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

def fetch_recent_news_sentiments(symbol="BTC"):
    news_url = f"https://finnhub.io/api/v1/news/{symbol.lower()}?token={FINNHUB_API_KEY}"
    resp = requests.get(news_url)
    items = resp.json()[:3]  # Most recent 3 articles
    headlines = [item['headline'] for item in items if 'headline' in item]
    sentiments = []
    for headline in headlines:
        sent = get_openai_sentiment(headline)
        sentiments.append(sent)
    return sentiments

def get_openai_sentiment(text):
    import openai

    openai.api_key = OPENAI_API_KEY
    prompt = f"Is this crypto news headline bullish (+1), bearish (-1), or neutral (0)?\nHeadline: {text}\nSentiment (give only number):"
    try:
        completion = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=2,
            temperature=0.0,
        )
        val = float(completion.choices[0].text.strip())
        return max(-1, min(val, 1))
    except Exception as e:
        print(f"OpenAI error: {e}")
        return 0  # neutral fallback

def aggregate_news_signal():
    sentiments = fetch_recent_news_sentiments("BTC")
    if not sentiments:
        return [0, 0, 0]
    return sentiments