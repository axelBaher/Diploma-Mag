import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from tqdm import tqdm
import os

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
CUTOFF_DATE = datetime.today() - timedelta(hours=18)


def read_cites_file():
    with open('data/cites.txt', 'r', encoding='utf-8') as f:
        cites = [line.strip() for line in f]
    return cites


def parse_news(url):
    if 'ria.ru' in url:
        parse_ria(url)
    elif 'mk.ru' in url:
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
    # options.add_argument("--headless")
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
        news_count = 0
        news_topic = ''
        link_iteration_done = False
        visited_news = set()

        next_button = driver.find_element(By.CSS_SELECTOR, 'div.list-more')
        driver.execute_script("arguments[0].scrollIntoView();", next_button)
        time.sleep(0.5)
        next_button.click()
        time.sleep(0.5)

        while True:
            if link_iteration_done:
                break

            news_items = driver.find_elements(By.CSS_SELECTOR, 'div.list-item')
            new_news_found = False
            for item in news_items:
                try:
                    content_element = item.find_element(By.CLASS_NAME, 'list-item__content')
                    news_link = content_element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                    if news_link in visited_news:
                        continue

                    tag_element = item.find_element(By.CLASS_NAME, 'list-item__tags')
                    tags_list_element = tag_element.find_elements(By.CLASS_NAME, 'list-tag')
                    news_tags = [tag.get_attribute('text').strip() for tag in tags_list_element]
                    if not news_tags:
                        continue

                    news_topic = driver.find_element(By.CLASS_NAME, 'tag-input__tag-text').text

                    date_element = item.find_element(By.CLASS_NAME, 'list-item__info-item[data-type="date"]')
                    news_date = parse_news_date(date_element.text)

                    if news_date < date_limit:
                        # print(f'Found {news_count} news with topic "{news_topic}"')
                        link_iteration_done = True
                        break

                    news_item = {
                        'link': news_link
                    }

                    if news_topic not in news_links:
                        news_links[news_topic] = list()
                    news_links[news_topic].append(news_item)

                    visited_news.add(news_link)
                    new_news_found = True

                    news_count += 1
                except Exception as excep:
                    print(f'Error while processing news item:\n{excep}')

            if not new_news_found:
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        return news_links, news_topic

    def parse_news_article(article_url):
        try:
            # print('Parsing article from url: ', article_url)
            resp = requests.get(article_url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            article_data = {
                "title": soup.find('meta', attrs={'name': 'analytics:title'})['content'],
                "description": soup.find('meta', attrs={'name': 'description'})['content'],
                "topic": soup.find('meta', attrs={'name': 'analytics:rubric'})['content'],
                "keywords": soup.find('meta', attrs={'name': 'keywords'})['content'].split(', '),
                "author": None,
                "publish_date": None,
                "modified_date": None,
                "content": ''
            }

            author_meta = soup.find('meta', attrs={'name': 'analytics:author'})
            if author_meta and author_meta.has_attr('content') and author_meta['content'] != '':
                article_data["author"] = author_meta['content']
            else:
                author_meta = soup.find('meta', attrs={'property': 'article:author'})
                if author_meta and author_meta.has_attr('content'):
                    article_data["author"] = author_meta['content']

            publish_date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if publish_date_meta and publish_date_meta.has_attr('content'):
                article_data["publish_date"] = datetime.strptime(publish_date_meta['content'],
                                                                 "%Y%m%dT%H%M").strftime("%Y-%m-%d %H:%M")

            modified_date_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
            if modified_date_meta and modified_date_meta.has_attr('content'):
                article_data["modified_date"] = datetime.strptime(modified_date_meta['content'],
                                                                  "%Y%m%dT%H%M").strftime("%Y-%m-%d %H:%M")

            contents = soup.find_all('div', class_='article__text')
            article_content = [content.text.strip() for content in contents]
            for string in article_content:
                article_data['content'] += string

            # print('Done')

            return article_data
        except Exception as err:
            print('News article data parse error: ', err)

    news_ria_links = load_json("data/news_ria_links.json")
    news_ria_data = load_json("data/news_ria_data.json")

    links = dict()
    data = dict()

    link_hrefs = get_link_hrefs()
    driver = setup_selenium_driver()
    progress_bar_links = tqdm(link_hrefs, desc='Processing links', unit=' link', position=0,
                              leave=True, dynamic_ncols=True)
    for link in progress_bar_links:
        try:
            progress_bar_links.set_postfix_str(f'{link}')
            driver.get(link)
            time.sleep(0.5)
            links, topic = parse_news_links(links, CUTOFF_DATE)

            if topic not in links:
                continue

            if topic not in news_ria_links:
                news_ria_links[topic] = []
            if topic not in news_ria_data:
                news_ria_data[topic] = []

            progress_bar_articles = tqdm(links[topic],
                                         desc=f'Processing articles with topic: "{topic}"',
                                         unit=' article',
                                         position=0,
                                         leave=True,
                                         dynamic_ncols=True)
            for article in progress_bar_articles:
                if article['link'] not in [item['link'] for item in news_ria_links[topic]]:
                    news_ria_links[topic].append(article)
                    data_item = parse_news_article(article['link'])
                    if data_item:
                        news_ria_data[topic].append(data_item)

            save_json("data/news_ria_links.json", news_ria_links)
            save_json("data/news_ria_data.json", news_ria_data)
        except Exception as e:
            print(f'Error:\n{e}\nLink: {link} skipped due to an error')
    driver.quit()
    return links, data


def parse_mk(url):
    def get_link_hrefs():
        link_hrefs_main = [
            url + '/news/',
        ]
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

    def parse_news_links(url_link, news_links: dict, date_limit):
        news_count = 0
        news_topic = ''
        link_iteration_done = False
        visited_news = set()
        pages = list()
        current_datetime = datetime.today()
        while current_datetime >= CUTOFF_DATE:
            pages.append(current_datetime.strftime('%Y/%m/%d'))
            current_datetime -= timedelta(days=1)
        pages_links = [url_link + f'{page}/' for page in pages]
        for page_link in pages_links:
            driver.get(page_link)
            news_items_day_group = driver.find_element(By.CSS_SELECTOR, 'section.news-listing__day-group')
            group_date = news_items_day_group.find_element(By.CLASS_NAME, 'news-listing__day-date').text.split(' ')
            group_date[1] = MONTHS[str.lower(group_date[1])]
            news_items = news_items_day_group.find_elements(By.CLASS_NAME, 'news-listing__item-link')
            for item in news_items:
                item_time = item.find_element(By.CLASS_NAME, 'news-listing__item-time').text
                if item_time != '':
                    item_datetime = '-'.join(map(str, group_date[::-1])) + f' {item_time}'
                    item_datetime = datetime.strptime(item_datetime, '%Y-%m-%d %H:%M')
                    print(item_datetime)
        """
        while True:
            if link_iteration_done:
                break

            news_items = driver.find_elements(By.CSS_SELECTOR, 'div.list-item')
            new_news_found = False
            for item in news_items:
                try:
                    content_element = item.find_element(By.CLASS_NAME, 'list-item__content')
                    news_link = content_element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                    if news_link in visited_news:
                        continue

                    tag_element = item.find_element(By.CLASS_NAME, 'list-item__tags')
                    tags_list_element = tag_element.find_elements(By.CLASS_NAME, 'list-tag')
                    news_tags = [tag.get_attribute('text').strip() for tag in tags_list_element]
                    if not news_tags:
                        continue

                    news_topic = driver.find_element(By.CLASS_NAME, 'tag-input__tag-text').text

                    date_element = item.find_element(By.CLASS_NAME, 'list-item__info-item[data-type="date"]')
                    news_date = parse_news_date(date_element.text)

                    if news_date < date_limit:
                        # print(f'Found {news_count} news with topic "{news_topic}"')
                        link_iteration_done = True
                        break

                    news_item = {
                        'link': news_link
                    }

                    if news_topic not in news_links:
                        news_links[news_topic] = list()
                    news_links[news_topic].append(news_item)

                    visited_news.add(news_link)
                    new_news_found = True

                    news_count += 1
                except Exception as excep:
                    print(f'Error while processing news item:\n{excep}')

            if not new_news_found:
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        """
        return news_links, news_topic

    def parse_news_article(article_url):
        try:
            # print('Parsing article from url: ', article_url)
            resp = requests.get(article_url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            article_data = {
                "title": soup.find('meta', attrs={'name': 'analytics:title'})['content'],
                "description": soup.find('meta', attrs={'name': 'description'})['content'],
                "topic": soup.find('meta', attrs={'name': 'analytics:rubric'})['content'],
                "keywords": soup.find('meta', attrs={'name': 'keywords'})['content'].split(', '),
                "author": None,
                "publish_date": None,
                "modified_date": None,
                "content": ''
            }

            author_meta = soup.find('meta', attrs={'name': 'analytics:author'})
            if author_meta and author_meta.has_attr('content') and author_meta['content'] != '':
                article_data["author"] = author_meta['content']
            else:
                author_meta = soup.find('meta', attrs={'property': 'article:author'})
                if author_meta and author_meta.has_attr('content'):
                    article_data["author"] = author_meta['content']

            publish_date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if publish_date_meta and publish_date_meta.has_attr('content'):
                article_data["publish_date"] = datetime.strptime(publish_date_meta['content'],
                                                                 "%Y%m%dT%H%M").strftime("%Y-%m-%d %H:%M")

            modified_date_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
            if modified_date_meta and modified_date_meta.has_attr('content'):
                article_data["modified_date"] = datetime.strptime(modified_date_meta['content'],
                                                                  "%Y%m%dT%H%M").strftime("%Y-%m-%d %H:%M")

            contents = soup.find_all('div', class_='article__text')
            article_content = [content.text.strip() for content in contents]
            for string in article_content:
                article_data['content'] += string

            # print('Done')

            return article_data
        except Exception as err:
            print('News article data parse error: ', err)

    news_mk_links = load_json("data/news_mk_links.json")
    news_mk_data = load_json("data/news_mk_data.json")

    links = dict()
    data = dict()

    link_hrefs = get_link_hrefs()
    driver = setup_selenium_driver()
    progress_bar_links = tqdm(link_hrefs, desc='Processing links', unit=' link', position=0,
                              leave=True, dynamic_ncols=True)
    for link in progress_bar_links:
        try:
            progress_bar_links.set_postfix_str(f'{link}')
            driver.get(link)
            time.sleep(0.5)
            links, topic = parse_news_links(link, links, CUTOFF_DATE)

            if topic not in links:
                continue

            if topic not in news_mk_links:
                news_mk_links[topic] = []
            if topic not in news_mk_data:
                news_mk_data[topic] = []

            progress_bar_articles = tqdm(links[topic],
                                         desc=f'Processing articles with topic: "{topic}"',
                                         unit=' article',
                                         position=0,
                                         leave=True,
                                         dynamic_ncols=True)
            for article in progress_bar_articles:
                if article['link'] not in [item['link'] for item in news_mk_links[topic]]:
                    news_mk_links[topic].append(article)
                    data_item = parse_news_article(article['link'])
                    if data_item:
                        news_mk_data[topic].append(data_item)

            save_json("data/news_mk_links.json", news_mk_links)
            save_json("data/news_mk_data.json", news_mk_data)
        except Exception as e:
            print(f'Error:\n{e}\nLink: {link} skipped due to an error')
    driver.quit()

    return links, data


def main():
    cites = read_cites_file()
    print('Parse news from:\t', cites[0])
    parse_news(cites[0])
    pass


if __name__ == '__main__':
    main()
