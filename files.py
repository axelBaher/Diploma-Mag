import json
import os
import re

import pandas as pd


def read_websites_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:  # data/websites.txt
        websites = [line.strip() for line in f]
    return websites


def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error while loading {filename}. Creating new file.")
            return {}
    return {}


def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f'Error while saving into {filename}: {e}')


def clean_content():
    def clean_news_content(text: str) -> str:
        if pd.isna(text):
            return text
        text = re.sub(r'\s+', ' ', text)
        text = text.replace("«", '"').replace("»", '"')
        text = re.sub(r'Читайте (также|материал):\s*"?«?.*?»?"?\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()
        return text

    def remove_duplicates(news_data):
        unique_links = set()
        cleaned_news = {}

        for topic, articles in news_data.items():
            cleaned_news[topic] = []
            for article in articles:
                link = article['link']
                if link not in unique_links:
                    unique_links.add(link)
                    cleaned_news[topic].append(article)
        return cleaned_news

    news_data_ria = load_json("data/news_ria_data.json")
    news_data_mk = load_json("data/news_mk_data.json")
    for news_topic_ria, news_topic_mk in zip(news_data_ria, news_data_mk):
        for news_item_ria, news_item_mk in zip(news_data_ria[news_topic_ria], news_data_mk[news_topic_mk]):
            news_item_ria['content'] = clean_news_content(news_item_ria['content'])
            news_item_mk['content'] = clean_news_content(news_item_mk['content'])

    news_data_ria = remove_duplicates(news_data_ria)
    news_data_mk = remove_duplicates(news_data_mk)

    save_json("data/news_ria_data_cleaned.json", news_data_ria)
    save_json("data/news_mk_data_cleaned.json", news_data_mk)
