import json
import textwrap
from collections import defaultdict
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import os
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go
import webbrowser

MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12
}
CUTOFF_DATE = datetime.today() - timedelta(days=3)
nltk.download("stopwords")
stop_words_russian = stopwords.words("russian")
matplotlib.use("TkAgg")


def read_websites_file():
    with open('data/websites.txt', 'r', encoding='utf-8') as f:
        websites = [line.strip() for line in f]
    return websites


def parse_news(url):
    if 'ria.ru' in url:
        parse_ria(url)
    if 'mk.ru' in url:
        parse_mk(url)


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


def setup_selenium_driver():
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.set_preference("general.useragent.override",
                           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    web_driver = webdriver.Firefox(options=options)
    return web_driver


def parse_ria(url):
    def get_link_hrefs():
        link_hrefs_main = [
            url + '/politics/',
            url + '/world/',
            url + '/economy/',
            url + '/society/',
            url + '/incidents/',
            url + '/defense_safety/'
        ]
        link_href_science = [
            url + '/space/',
            url + '/sn_health/',
            url + '/technology/',
            url + '/tag_thematic_category_Arkheologija/',
            url + '/keyword_fizika/',
            url + '/keyword_biologija/',
            url + '/keyword_genetika/',
            url + '/earth/',
            url + '/keyword_matematika/',
            url + '/keyword_khimija/',
            url + '/keyword_sociologija/'
        ]
        link_hrefs_main.extend(link_href_science)
        link_href_culture = [
            url + '/category_kino/',
            url + '/category_teatr/',
            url + '/tag_thematic_category_Vystavka/',
            url + '/category_knigi/',
            url + '/category_stil-zhizni/',
            url + '/category_foto---kultura/',
            url + '/category_muzyka/',
            url + '/category_novosti-kultury/',
            url + '/category_balet/',
            url + '/category_opera/'
        ]
        link_hrefs_main.extend(link_href_culture)
        link_href_tourism = [
            url + '/tourism_news/',
            url + '/tourism_navigator/',
            url + '/tourism_visual/',
            url + '/tourism_food/',
            url + '/category_intervyu_turizm/'
        ]
        link_hrefs_main.extend(link_href_tourism)
        link_href_religion = [
            url + '/category_religiya/',
            url + '/religion_expert/',
            url + '/religion_interview/',
            url + '/category_holydays/'
        ]
        link_hrefs_main.extend(link_href_religion)
        return link_hrefs_main

    def parse_news_date(date_str):
        news_datetime = datetime.today()
        parts = date_str.split()
        time_part = parts[-1].split(':')
        try:
            if len(parts) == 1:
                news_datetime = news_datetime.replace(hour=int(time_part[0]), minute=int(time_part[1]), second=0, microsecond=0)
            elif len(parts) == 2:
                news_datetime = news_datetime - timedelta(days=1)
                news_datetime = news_datetime.replace(hour=int(time_part[0]), minute=int(time_part[1]), second=0, microsecond=0)
            elif len(parts) == 3:
                month = parts[1].split(',')[0]
                news_datetime = news_datetime.replace(month=MONTHS[month], day=int(parts[0]),
                                                      hour=int(time_part[0]), minute=int(time_part[1]), second=0, microsecond=0)
            elif len(parts) == 4:
                year = parts[2].split(',')[0]
                month = parts[1].split(',')[0]
                news_datetime = news_datetime.replace(year=int(year), month=MONTHS[month], day=int(parts[0]),
                                                      hour=int(time_part[0]), minute=int(time_part[1]), second=0, microsecond=0)
        except Exception as err:
            print(f'Date parse error: ', err)
        return news_datetime

    def parse_news_links(news_links: dict, date_limit):
        news_topic = ''
        link_iteration_done = False
        last_news_index = 1
        new_news_found = False
        while True:
            if last_news_index == 2:
                next_button = driver.find_element(By.CSS_SELECTOR, 'div.list-more')
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                time.sleep(0.5)
                next_button.click()
                time.sleep(0.5)
            elif ((last_news_index - 1) % 10) == 0:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            if link_iteration_done:
                break
            if (last_news_index == 3 or last_news_index == 6 or last_news_index == 8 or last_news_index == 12
                    or last_news_index == 16):
                last_news_index += 1
            news_item = driver.find_element(By.CSS_SELECTOR, f'div.list-item:nth-child({last_news_index})')
            try:
                date_element = news_item.find_element(By.CLASS_NAME, 'list-item__info-item[data-type="date"]')
                news_date = parse_news_date(date_element.text)
                if news_date < date_limit:
                    link_iteration_done = True
                    break

                content_element = news_item.find_element(By.CLASS_NAME, 'list-item__content')
                news_link = content_element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                news_topic = driver.find_element(By.CLASS_NAME, 'tag-input__tag-text').text
                news_item_dict = {
                    "link": news_link,
                    "title": None,
                    "description": None,
                    "topic": None,
                    "keywords": None,
                    "author": None,
                    "publish_date": None,
                    "modified_date": None,
                    "content": ''
                }

                if news_topic in news_links:
                    if news_item_dict['link'] in [item['link'] for item in news_links[news_topic]]:
                        last_news_index += 1
                        continue
                else:
                    news_links[news_topic] = list()
                news_links[news_topic].append(news_item_dict)
                last_news_index += 1
                new_news_found = True
            except Exception as excep:
                print(f'Error while processing news item:\n{excep}')
            # news_items = driver.find_elements(By.CSS_SELECTOR, 'div.list-item:nth-last-child(-n+20)')
            # print("news_items len: ", len(news_items))
            # for item in news_items:
            #     try:
            #         date_element = item.find_element(By.CLASS_NAME, 'list-item__info-item[data-type="date"]')
            #         news_date = parse_news_date(date_element.text)
            #         if news_date < date_limit:
            #             link_iteration_done = True
            #             break
            #
            #         content_element = item.find_element(By.CLASS_NAME, 'list-item__content')
            #         news_link = content_element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            #         news_topic = driver.find_element(By.CLASS_NAME, 'tag-input__tag-text').text
            #         news_item_dict = {
            #             "link": news_link,
            #             "title": None,
            #             "description": None,
            #             "topic": None,
            #             "keywords": None,
            #             "author": None,
            #             "publish_date": None,
            #             "modified_date": None,
            #             "content": ''
            #         }
            #
            #         if news_topic in news_links:
            #             if news_item_dict in news_links[news_topic]:
            #                 continue
            #         else:
            #             news_links[news_topic] = list()
            #         news_links[news_topic].append(news_item_dict)
            #     except Exception as excep:
            #         print(f'Error while processing news item:\n{excep}')
        return news_links, news_topic, new_news_found

    def parse_news_article(article_item):
        try:
            resp = requests.get(article_item['link'])
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            article_item["title"] = soup.find('meta', attrs={'name': 'analytics:title'})['content']

            article_item["description"] = soup.find('meta', attrs={'name': 'description'})['content']

            article_item["topic"] = soup.find('meta', attrs={'name': 'analytics:rubric'})['content']

            article_item["keywords"] = soup.find('meta', attrs={'name': 'keywords'})['content'].split(', ')
            # article_data = {
            #     "link": article_item['link'],
            #     "title": soup.find('meta', attrs={'name': 'analytics:title'})['content'],
            #     "description": soup.find('meta', attrs={'name': 'description'})['content'],
            #     "topic": soup.find('meta', attrs={'name': 'analytics:rubric'})['content'],
            #     "keywords": soup.find('meta', attrs={'name': 'keywords'})['content'].split(', '),
            #     "author": None,
            #     "publish_date": None,
            #     "modified_date": None,
            #     "content": ''
            # }

            author_meta = soup.find('meta', attrs={'name': 'analytics:author'})
            if author_meta and author_meta.has_attr('content') and author_meta['content'] != '':
                article_item["author"] = author_meta['content']
            else:
                author_meta = soup.find('meta', attrs={'property': 'article:author'})
                if author_meta and author_meta.has_attr('content'):
                    article_item["author"] = author_meta['content']

            publish_date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if publish_date_meta and publish_date_meta.has_attr('content'):
                article_item["publish_date"] = datetime.strptime(publish_date_meta['content'],
                                                                 "%Y%m%dT%H%M").strftime("%Y-%m-%d %H:%M")

            modified_date_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
            if modified_date_meta and modified_date_meta.has_attr('content'):
                article_item["modified_date"] = datetime.strptime(modified_date_meta['content'],
                                                                  "%Y%m%dT%H%M").strftime("%Y-%m-%d %H:%M")

            contents = soup.find_all('div', class_='article__text')
            article_content = [content.text.strip() for content in contents]
            for string in article_content:
                article_item['content'] += string

            return article_item
        except Exception as err:
            print('News article data parse error: ', err)

    new_articles_counter = 0

    # news_ria_links = load_json("data/news_ria_links.json")
    news_ria_data = load_json("data/news_ria_data.json")

    link_hrefs = get_link_hrefs()
    driver = setup_selenium_driver()
    progress_bar_links = tqdm(link_hrefs, desc='Processing links', unit=' link', position=0,
                              leave=True, dynamic_ncols=True)
    for link in progress_bar_links:
        try:
            progress_bar_links.set_postfix_str(f'{link}')
            driver.get(link)
            time.sleep(0.5)
            news_ria_data, topic, found_new_news = parse_news_links(news_ria_data, CUTOFF_DATE)

            # if topic not in news_ria_data:
            #     continue

            # if topic not in news_ria_links:
            #     news_ria_links[topic] = []
            # if topic not in news_ria_data:
            #     news_ria_data[topic] = []
            if found_new_news:
                progress_bar_articles = tqdm(news_ria_data[topic],
                                             desc=f'Processing articles with topic: "{topic}"',
                                             unit=' article',
                                             position=0,
                                             leave=True,
                                             dynamic_ncols=True)
                for article in progress_bar_articles:
                    parse_news_article(article)
                    new_articles_counter += 1

                # save_json("data/news_ria_links.json", news_ria_links)
                save_json("data/news_ria_data.json", news_ria_data)
            # else:
            #     progress_bar_links.set_postfix_str(f'{link}: no new articles found')
        except Exception as e:
            tqdm.write(f'\nError:\n{e}\nLink: {link} skipped due to an error')
    driver.quit()
    # return news_ria_links, news_ria_data
    print('Found new articles: ', new_articles_counter)
    return news_ria_data


def parse_mk(url):
    def get_link_hrefs(url_part):
        link_hrefs_main = [
            url_part + '/news/',
        ]
        return link_hrefs_main

    def parse_news_links(url_link, news_links: dict):
        pages = list()
        current_datetime = datetime.today()
        new_article_found = False

        while current_datetime >= CUTOFF_DATE:
            pages.append(current_datetime.strftime('%Y/%m/%d'))
            current_datetime -= timedelta(days=1)
        pages_links = [url_link + f'{page}/' for page in pages]
        for page_link in pages_links:
            resp = requests.get(page_link)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # driver.get(page_link)

            items = soup.find_all('a', class_='news-listing__item-link')
            # items = driver.find_elements(By.CLASS_NAME, 'news-listing__item-link')
            for item in items:
                # item_time = item.find_element(By.CLASS_NAME, 'news-listing__item-time').text
                item_time = item.find('span', class_='news-listing__item-time').text
                if item_time != '':
                    item_link = item.attrs['href']
                    item_topic = item_link.split('/')[3]
                    news_item_dict = {
                        "link": item_link,
                        "title": None,
                        "description": None,
                        "topic": None,
                        "keywords": None,
                        "author": None,
                        "publish_date": None,
                        "modified_date": None,
                        "content": ''
                    }

                    if item_topic in news_links:
                        if news_item_dict['link'] in [item['link'] for item in news_links[item_topic]]:
                            continue
                    else:
                        news_links[item_topic] = list()
                    news_links[item_topic].append(news_item_dict)
                    new_article_found = True
        return news_links, new_article_found

    def parse_news_article(article_item):
        try:
            resp = requests.get(article_item['link'])
            soup = BeautifulSoup(resp.text, 'html.parser')
            article_item['title'] = soup.find('meta', attrs={'name': 'title'})['content']
            article_item['topic'] = soup.find('meta', attrs={'itemprop': 'articleSection'})['content']
            article_item['keywords'] = str.lower(soup.find('meta', attrs={'name': 'keywords'})['content']).split(', ')

            author_meta = soup.find_all('li', class_='article__authors-data-item')
            authors = list()
            for author in author_meta:
                if author.find('meta', attrs={'itemprop': 'name'}):
                    authors.append(author.find('meta', attrs={'itemprop': 'name'})['content'])
            article_item['author'] = ', '.join(authors)

            publish_date_meta = soup.find('meta', attrs={'itemprop': 'datePublished'})
            article_item["publish_date"] = datetime.strptime(publish_date_meta['content'],
                                                             "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M")

            modified_date_meta = soup.find('meta', attrs={'itemprop': 'dateModified'})
            modified_data = datetime.strptime(modified_date_meta['content'],
                                              "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M")
            if modified_data != article_item["publish_date"]:
                article_item["modified_date"] = modified_data

            contents = soup.find_all('div', class_='article__body')
            article_content = [content.text.strip() for content in contents]
            for string in article_content:
                article_item['content'] += string

            return article_item
        except Exception as err:
            print('News article data parse error: ', err)

    new_articles_counter = 0
    # news_mk_links = load_json("data/news_mk_links.json")
    news_mk_data = load_json("data/news_mk_data.json")
    link_hrefs = get_link_hrefs(url)
    # driver = setup_selenium_driver()
    progress_bar_links = tqdm(link_hrefs, desc='Processing links', unit=' link', position=0,
                              leave=True, dynamic_ncols=True)
    for link in progress_bar_links:
        try:
            progress_bar_links.set_postfix_str(f'{link}')
            # time.sleep(0.5)
            news_mk_data, found_new_news = parse_news_links(link, news_mk_data)
            # save_json("data/news_mk_links.json", news_mk_links)
            if found_new_news:
                for news_topic in news_mk_data:
                    progress_bar_articles = tqdm(news_mk_data[news_topic],
                                                 desc=f'Processing articles with topic: "{news_topic}"',
                                                 unit=' article',
                                                 position=0,
                                                 leave=True,
                                                 dynamic_ncols=True)
                    for article in progress_bar_articles:
                        a_data = parse_news_article(article)
                        if news_topic in news_mk_data:
                            if a_data in news_mk_data[news_topic]:
                                continue
                        else:
                            news_mk_data[news_topic] = list()
                        news_mk_data[news_topic].append(a_data)
                        new_articles_counter += 1
            else:
                pass
            save_json("data/news_mk_data.json", news_mk_data)
        except Exception as e:
            print(f'Error:\n{e}\nLink: {link} skipped due to an error')
    # driver.quit()
    print('Found new articles: ', new_articles_counter)
    return news_mk_data


def parse():
    websites = read_websites_file()
    for website in websites:
        print('Parse news from:\t', website)
        parse_news(website)


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


def find_similar_news(news_data, tfidf_matrix, cluster_labels, threshold=0.75):
    edges = []
    graph = nx.DiGraph()

    for cluster in set(cluster_labels):
        indices = np.where(cluster_labels == cluster)[0]
        if len(indices) < 2:
            continue

        news_subset = [news_data[i] for i in indices]
        subset_matrix = tfidf_matrix[indices]
        similarities = cosine_similarity(subset_matrix)

        for i in range(len(news_subset)):
            for j in range(i + 1, len(news_subset)):
                if similarities[i, j] > threshold and news_subset[i]["source"] != news_subset[j]["source"]:
                    if news_subset[i]["id"] not in graph.nodes:
                        graph.add_node(news_subset[i]["id"], title=news_subset[i]["title"], text=news_subset[i]["text"],
                                       date=news_subset[i]["date"], source=news_subset[i]["source"])

                    if news_subset[j]["id"] not in graph.nodes:
                        graph.add_node(news_subset[j]["id"], title=news_subset[j]["title"], text=news_subset[j]["text"],
                                       date=news_subset[j]["date"], source=news_subset[j]["source"])

                    edges.append((news_subset[i]["id"], news_subset[j]["id"], similarities[i, j]))
                    graph.add_edge(news_subset[i]["id"], news_subset[j]["id"], weight=similarities[i, j])

    return graph, edges


def visualize_interactive_graph(graph, edges):
    # Функция для отрисовки рёбер графа
    def draw_graph_edges(_pos, _edges):
        _graph_edges = {
            "x": [],
            "y": [],
        }

        for edge in _edges:
            x0, y0 = _pos[edge[0]]
            x1, y1 = _pos[edge[1]]
            _graph_edges["x"].extend([x0, x1, None])
            _graph_edges["y"].extend([y0, y1, None])

        _edge_trace = go.Scatter(
            x=_graph_edges["x"], y=_graph_edges["y"],
            line=dict(width=1, color='gray'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )

        return _edge_trace

    # Функция для отрисовки узлов графа
    def draw_graph_nodes(_pos, _graph, line_len=30, width_const=0.1, height_const=0.4):
        def calc_graph_node_rectangle(_data, _line_len=30, _width_const=0.005, _height_const=0.15):
            _node_rectangle = {
                "text": textwrap.fill(_data['title'], width=_line_len).replace("\n", "<br>"),
                "width": float,
                "height": float
            }

            num_lines = _node_rectangle["text"].count("<br>") + 1
            _node_rectangle["width"] = _width_const * max(len(line) for line in _node_rectangle["text"].split("<br>"))
            _node_rectangle["height"] = _height_const * num_lines

            return _node_rectangle

        _graph_nodes = {
            "x": [],
            "y": [],
            "text": [],
            "shapes": [],
            "links": [],
        }

        for node, data in _graph.nodes(data=True):
            x, y = _pos[node]

            node_rectangle = calc_graph_node_rectangle(_data=data, _line_len=line_len,
                                                       _width_const=width_const, _height_const=height_const)

            _graph_nodes["x"].append(x)
            _graph_nodes["y"].append(y)
            _graph_nodes["text"].append(f"<a href='{node}' target='_blank'>{node_rectangle['text']}</a>")
            _graph_nodes["links"].append(node)

            _graph_nodes["shapes"].append(
                dict(
                    type="rect",
                    x0=x - node_rectangle["width"] / 2, y0=y - node_rectangle["height"] / 2,
                    x1=x + node_rectangle["width"] / 2, y1=y + node_rectangle["height"] / 2,
                    line=dict(color='blue'),
                    fillcolor="rgba(0,0,0,0)"
                )
            )

        _node_trace = go.Scatter(
            x=_graph_nodes["x"], y=_graph_nodes["y"],
            mode='text',
            text=_graph_nodes["text"],
            textposition="middle center",
            hoverinfo='text'
        )

        return _graph_nodes, _node_trace

    # Начальная позиция для каждого подграфа
    pos = {}
    current_x = 0
    current_y = 0
    max_width = 5  # Максимальная ширина для группы (подграфа)
    node_padding = 0.2  # Отступы для узлов

    for edge in edges:
        # Для каждого подграфа вычисляем свои позиции
        x0, y0 = current_x, current_y
        x1, y1 = current_x, current_y + 5  # Смещение для следующего подграфа
        pos[edge[0]] = (x0, y0)
        pos[edge[1]] = (x1, y1)

        # Смещаемся вправо для следующего подграфа
        current_x += max_width + 1  # Отступ между подграфами
        if current_x > 15:  # Если нет места по оси X, переносим на новую строку
            current_x = 0
            current_y += 10

    # Создание рёбер и узлов для визуализации
    edge_trace = draw_graph_edges(_pos=pos, _edges=edges)
    graph_nodes, node_trace = draw_graph_nodes(_pos=pos, _graph=graph)

    # Построение графа
    fig = go.Figure(data=[edge_trace, node_trace])

    fig.update_layout(
        title="Граф схожих новостей",
        title_font_size=24,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=40, l=40, r=40, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        shapes=graph_nodes["shapes"]
    )

    fig.show()


def clusterization(threshold=0.75):
    def tfidf_vectorization(_news_texts):
        _vectorizer = TfidfVectorizer(stop_words=stop_words_russian, max_features=5000)
        _tfidf_matrix = _vectorizer.fit_transform(_news_texts)
        return _tfidf_matrix, _vectorizer

    def cluster_news(_tfidf_matrix, _num_clusters=20):
        kmeans = KMeans(n_clusters=_num_clusters, random_state=42)
        labels = kmeans.fit_predict(_tfidf_matrix)
        return labels

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
                    "source": source
                })
        return news_list

    news_ria = load_json("data/news_ria_data_cleaned.json")
    news_mk = load_json("data/news_mk_data_cleaned.json")

    news_ria_list = extract_news_data(data=news_ria, source="ria")
    news_mk_list = extract_news_data(data=news_mk, source="mk")
    all_news = news_ria_list + news_mk_list

    news_texts = [news["text"] for news in all_news]
    tfidf_matrix, vectorizer = tfidf_vectorization(news_texts)

    num_clusters = 20
    cluster_labels = cluster_news(_tfidf_matrix=tfidf_matrix, _num_clusters=num_clusters)

    graph_, edges = find_similar_news(all_news, tfidf_matrix, cluster_labels, threshold=threshold)

    print("Found similar news:")
    for edge in edges:
        print(f"{edge[0]} → {edge[1]} (сходство: {edge[2]:.2f})")

    visualize_interactive_graph(graph_, edges)


def main():
    # parse()
    # clean_content()
    clusterization(threshold=0.75)


if __name__ == '__main__':
    main()
