import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer

from files import load_json

nltk.download("stopwords")
stop_words_russian = stopwords.words("russian")


def run_vectorization(vectorization_method, files):
    def extract_news_data(data, source):
        news_list = []
        for category, articles in data.items():
            for article in articles:
                news_list.append({
                    "id": article.get("link", ""),  # Уникальный идентификатор
                    "text": article.get("content", ""),
                    "title": article.get("title", ""),
                    "keywords": " ".join(article.get("keywords", [])),
                    "date": article.get("publish_date", ""),
                    "source": source,
                    "author": article.get("author", "")
                })
        return news_list
    news_data = list()
    for file in files:
        data = load_json(f"data/{file}")
        source = file.split('_')
        news_data += extract_news_data(data, source[1])
    # news_mk = load_json("data/news_mk_data_cleaned.json")

    # news_ria_list = extract_news_data(data=news_ria, source="ria")
    # news_mk_list = extract_news_data(data=news_mk, source="mk")
    # news_data = news_ria_list + news_mk_list
    news_texts = [news["text"] for news in news_data]
    if vectorization_method == 'TF-IDF':
        vectorizer = TfidfVectorizer(stop_words=stop_words_russian, max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(news_texts)
        return news_data, tfidf_matrix, vectorizer
