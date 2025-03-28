import time
from datetime import datetime, timedelta
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium import webdriver
from files import load_json, save_json


class ParsingThread(QThread):
    progress_updated = pyqtSignal(int)  # Сигнал для обновления прогресса
    parsing_finished = pyqtSignal()

    def __init__(self, sites, cutoff_date):
        super().__init__()
        self.parsing_thread = None
        self.sites = sites
        self.cutoff_date = cutoff_date

    def run(self):
        total_sites = len(self.sites)
        for i, site in enumerate(self.sites):
            if 'ria.ru' in site:  # Пример: для RIA мы запускаем соответствующую функцию
                self.parsing_ria(site)
            elif 'mk.ru' in site:  # Пример: для MK
                self.parsing_mk(site)
            else:
                pass

            # Обновляем прогресс
            self.progress_updated.emit(int(((i + 1) / total_sites) * 100))
        self.parsing_finished.emit()  # Завершение потока

    def parsing_ria(self, url):
        # url = "https://ria.ru"
        news_ria_data = parse_ria(url, self.cutoff_date)
        # Здесь можно обработать полученные данные, если нужно
        print(f"Парсинг для {url} завершен")

    def parsing_mk(self, url):
        # url = "https://mk.ru"
        news_mk_data = parse_mk(url, self.cutoff_date)
        # Здесь можно обработать полученные данные, если нужно
        print(f"Парсинг для {url} завершен")


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


def parse_ria(url, cutoff_date):
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

    news_ria_data = load_json("data/news_ria_data.json")
    link_hrefs = get_link_hrefs()
    driver = setup_selenium_driver()
    for link in link_hrefs:
        try:
            print("link: ", link)
            driver.get(link)
            time.sleep(0.5)
            news_ria_data, topic, found_new_news = parse_news_links(news_ria_data, cutoff_date)

            if found_new_news:
                for article in news_ria_data[topic]:
                    parse_news_article(article)
                save_json("data/news_ria_data.json", news_ria_data)
        except Exception as e:
            print(f'\nError:\n{e}\nLink: {link} skipped due to an error')
    driver.quit()
    print('Parsing completed')
    return news_ria_data


def parse_mk(url, cutoff_date):
    def get_link_hrefs(url_part):
        link_hrefs_main = [
            url_part + '/news/',
        ]
        return link_hrefs_main

    def parse_news_links(url_link, news_links: dict):
        pages = list()
        current_datetime = datetime.today()
        new_article_found = False

        while current_datetime >= cutoff_date:
            pages.append(current_datetime.strftime('%Y/%m/%d'))
            current_datetime -= timedelta(days=1)
        pages_links = [url_link + f'{page}/' for page in pages]
        for page_link in pages_links:
            resp = requests.get(page_link)
            soup = BeautifulSoup(resp.text, 'html.parser')

            items = soup.find_all('a', class_='news-listing__item-link')
            for item in items:
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
    news_mk_data = load_json("data/news_mk_data.json")
    link_hrefs = get_link_hrefs(url)
    for link in link_hrefs:
        try:
            news_mk_data, found_new_news = parse_news_links(link, news_mk_data)

            if found_new_news:
                for news_topic in news_mk_data:
                    for article in news_mk_data[news_topic]:
                        a_data = parse_news_article(article)
                        if news_topic in news_mk_data:
                            if a_data in news_mk_data[news_topic]:
                                continue
                        else:
                            news_mk_data[news_topic] = list()
                        news_mk_data[news_topic].append(a_data)
                        new_articles_counter += 1
            save_json("data/news_mk_data.json", news_mk_data)
        except Exception as e:
            print(f'Error:\n{e}\nLink: {link} skipped due to an error')

    print('Found new articles: ', new_articles_counter)
    return news_mk_data
