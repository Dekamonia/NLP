from bs4 import BeautifulSoup
import requests
import sqlite3

SITE_URL = 'https://lenta.ru'
PARTS_URL = f'{SITE_URL}/parts/news'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}

# Функция для создания таблицы в базе данных SQLite
def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS articles
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          title TEXT,
                          category TEXT,
                          create_date TEXT,
                          body TEXT,
                          url TEXT UNIQUE)''')
        conn.commit()
    except sqlite3.Error as e:
        print("Ошибка при создании таблицы:", e)

# Функция для добавления записи в базу данных SQLite
def insert_article(conn, title, category, create_date, body, url):
    try:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO articles (title, category, create_date, body, url) VALUES (?, ?, ?, ?, ?)''', 
                       (title, category, create_date, "\n".join(body), url))
        conn.commit()
    except sqlite3.Error as e:
        print("Ошибка при добавлении записи:", e)

# Основная функция для сохранения данных в базу данных SQLite
def save_to_database(title, category, create_date, body, url):
    conn = sqlite3.connect('articles.db')
    create_table(conn)
    insert_article(conn, title, category, create_date, body, url)
    conn.close()

# Функция для получения списка URL статей на странице
def get_article_urls(page_url):
    response = requests.get(page_url, headers=headers)
    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
        body = soup.find_all(class_='parts-page__item')
        return [SITE_URL + item.find('a').get('href') for item in body if item.find('a')]
    else:
        print('Ошибка при запросе:', response.status_code)
        return []

# Функция для получения содержания статьи
def get_article_content(article_url):
    response = requests.get(article_url, headers=headers)
    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('h1').text if soup.find('h1') else 'No Title'
        body = [p.text for p in soup.find('body').find_all('p')]
        category_tag = soup.find('a', class_='topic-header__rubric')
        category = category_tag.text if category_tag else 'Неизвестно'
        date_tag = soup.find('time', class_='topic-header__time')
        create_date = date_tag.get('datetime') if date_tag else 'Неизвестно'
        
        return title, category, create_date, body, article_url
    else:
        print('Ошибка при запросе:', response.status_code)
        return None, None, None, None, None

# Основная функция для запуска парсинга и сохранения данных
def main():
    page_urls = [PARTS_URL]  # начальная страница
    article_urls = get_article_urls(PARTS_URL)  # получаем адреса статей на начальной странице
    for article_url in article_urls:
        title, category, create_date, body, url = get_article_content(article_url)  # получаем содержание статьи
        if title and body and category and create_date:
            save_to_database(title, category, create_date, body, url)  # сохраняем статью в базу данных

if __name__ == "__main__":
    main()
