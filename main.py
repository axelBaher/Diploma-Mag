import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

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


def read_cites_file():
    with open('data/cites.txt', 'r', encoding='utf-8') as f:
        cites = [line.strip() for line in f]
    return cites


def parse_news(url):
    if 'ria.ru' in url:
        news_ria_meta, news_ria_data = parse_ria(url)
        print('Saving news meta data into news_ria_meta.json file...')
        try:
            with open("data/news_ria_meta.json", "w", encoding="utf-8") as f:
                json.dump(news_ria_meta, f, ensure_ascii=False, indent=4)
            print('Done!')
        except Exception as e:
            print('Error while saving: ', e)
        print('Saving news articles into news_ria_data.json file...')
        try:
            with open("data/news_ria_data.json", "w", encoding="utf-8") as f:
                json.dump(news_ria_data, f, ensure_ascii=False, indent=4)
            print('Done!')
        except Exception as e:
            print('Error while saving: ', e)
    elif 'mk.ru' in url:
        news_mk = parse_mk(url)
        with open("data/news_mk.json", "w", encoding="utf-8") as f:
            json.dump(news_mk, f, ensure_ascii=False, indent=4)


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

    def setup_selenium_driver():
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.set_preference("general.useragent.override",
                               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
        driver = webdriver.Firefox(options=options)
        return driver

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

    def parse_news_meta(news_meta: dict, date_limit):
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
                        print(f'Processed {news_count} news with topic "{news_topic}"')
                        link_iteration_done = True
                        break

                    news_item = {
                        'link': news_link,
                        'lastdate': news_date.strftime("%Y-%m-%d %H:%M"),
                        'tags': list(set(news_tags))
                    }

                    if news_topic not in news_meta:
                        news_meta[news_topic] = list()
                    news_meta[news_topic].append(news_item)

                    visited_news.add(news_link)
                    new_news_found = True

                    news_count += 1
                except Exception as excep:
                    print(f'Error while processing news item:\n{excep}')

            if not new_news_found:
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        return news_meta, news_topic

    def parse_news_article(article_url):
        try:
            print('Parsing article from url: ', article_url)
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

            print('Done')

            return article_data
        except Exception as err:
            print('News article data parse error: ', err)

    meta = dict()
    data = dict()
    cutoff_date = datetime.today() - timedelta(days=1)
    link_hrefs = get_link_hrefs()
    driver = setup_selenium_driver()
    for link in link_hrefs:
        try:
            print('Parsing link:\t', link)
            driver.get(link)
            time.sleep(0.5)
            meta, topic = parse_news_meta(meta, cutoff_date)
            if topic not in meta:
                continue
            for article in meta[topic]:
                data_item = parse_news_article(article['link'])
                if topic not in data:
                    data[topic] = list()
                data[topic].append(data_item)

        except Exception as e:
            print(f'Error:\n{e}\nLink: {link} skipped due to an error')
    driver.quit()
    return meta, data


def parse_mk(url):
    news = dict()
    return news


def main():
    cites = read_cites_file()
    print('Parse news from:\t', cites[0])
    parse_news(cites[0])
    pass


if __name__ == '__main__':
    main()
