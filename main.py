import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import time


def read_cites_file():
    with open('data/cites.txt', 'r', encoding='utf-8') as f:
        cites = [line.strip() for line in f]
    return cites


def parse_news(url):
    if 'ria.ru' in url:
        news = parse_ria(url)
        with open("news_ria.json", "w", encoding="utf-8") as f:
            json.dump(news, f, ensure_ascii=False, indent=4)
        return news


def parse_ria(url):
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
                news_datetime = news_datetime.replace(month=months[month], day=int(parts[0]),
                                                      hour=int(time_part[0]), minute=int(time_part[1]), second=0, microsecond=0)
            elif len(parts) == 4:
                year = parts[2].split(',')[0]
                month = parts[1].split(',')[0]
                news_datetime = news_datetime.replace(year=int(year), month=months[month], day=int(parts[0]),
                                                      hour=int(time_part[0]), minute=int(time_part[1]), second=0, microsecond=0)
        except Exception as err:
            print(f'Date parse error: ', err)
        return news_datetime

    months = {
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
    link_href_tourism = [
        url + '/tourism_news/',
        url + '/tourism_navigator/',
        url + '/tourism_visual/',
        url + '/tourism_food/',
        url + '/category_intervyu_turizm/'
    ]
    link_href_religion = [
        url + '/category_religiya/',
        url + '/religion_expert/',
        url + '/religion_interview/',
        url + '/category_holydays/'
    ]
    link_hrefs_main.extend(link_href_science)
    link_hrefs_main.extend(link_href_culture)
    link_hrefs_main.extend(link_href_tourism)
    link_hrefs_main.extend(link_href_religion)
    # resp = requests.get(url)
    # resp.raise_for_status()
    # soup = BeautifulSoup(resp.text, 'html.parser')
    # articles = soup.find_all('a', class_='cell-extension__item-link color-font-hover-only')
    news = dict()
    visited_news = set()
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.set_preference("general.useragent.override",
                           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    driver = webdriver.Firefox(options=options)
    cutoff_date = datetime.today() - timedelta(days=7)
    for link in link_hrefs_main:
        news_topic = ''
        link_iteration_done = False
        try:
            print('Parsing link:', link)
            driver.get(link)
            time.sleep(0.5)
            news_count = 0

            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'div.list-more')
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                time.sleep(0.5)
                next_button.click()
                time.sleep(1)
            except (NoSuchElementException, ElementClickInterceptedException):
                break

            while True:
                if link_iteration_done:
                    break
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

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
                        news_tags = [tag.text.strip() for tag in tags_list_element]
                        if not news_tags:
                            continue
                        news_topic = news_tags[0]
                        news_tags = news_tags[1:]

                        date_element = item.find_element(By.CLASS_NAME, 'list-item__info-item[data-type="date"]')
                        news_date = parse_news_date(date_element.text)

                        if news_date < cutoff_date:
                            print(f'Processed {news_count} news with topic {news_topic}')
                            link_iteration_done = True
                            break
                            # driver.quit()
                            # return news

                        news_item = {
                            'link': news_link,
                            'lastdate': news_date.strftime("%Y-%m-%d %H:%M"),
                            'tags': news_tags
                        }

                        if news_topic not in news:
                            news[news_topic] = list()
                        news[news_topic].append(news_item)

                        visited_news.add(news_link)
                        new_news_found = True
                        if not new_news_found:
                            break

                        news_count += 1
                    except Exception as e:
                        print(f'Error while processing news item:\n{e}')

        except Exception as e:
            print(f'Error:\n{e}\nLink: {link} skipped due to an error')
    driver.quit()
    return news


def main():
    cites = read_cites_file()
    # for cite_url in cites:
    #     parse_news(cite_url)
    parse_news(cites[0])
    pass


if __name__ == '__main__':
    main()
