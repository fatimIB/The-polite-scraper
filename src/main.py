from pathlib import Path
from urllib.parse import urljoin
import time

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_DIR = Path("cache")

USER_AGENT = "FlyRankInternship A9/1.0 (https://github.com/fatimIB/The-polite-scraper)"
TIMEOUT = 10
DELAY = 0.5


def get_cache_file(page_number):
    return CACHE_DIR / f"catalogue-page-{page_number}.html"


def fetch_page(url, cache_file):
    CACHE_DIR.mkdir(exist_ok=True)

    if cache_file.exists():
        content = cache_file.read_bytes()
        print(f"CACHE HIT {cache_file.name} bytes={len(content)}")
        return content

    headers = {
        "User-Agent": USER_AGENT
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=TIMEOUT
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch page: HTTP {response.status_code}"
        )

    cache_file.write_text(response.text, encoding="utf-8")

    print(
        f"FETCH {cache_file.name} "
        f"status={response.status_code} "
        f"bytes={len(response.content)}"
    )

    return response.content


def extract_books(html, page_url):
    soup = BeautifulSoup(html, "html.parser")

    book_urls = []

    for article in soup.select("article.product_pod"):
        link = article.select_one("h3 a")

        if link and link.get("href"):
            absolute_url = urljoin(page_url, link["href"])
            book_urls.append(absolute_url)

    return book_urls


def find_next_page(html, current_url):
    soup = BeautifulSoup(html, "html.parser")

    next_link = soup.select_one("li.next a")

    if next_link and next_link.get("href"):
        return urljoin(current_url, next_link["href"])

    return None


def discover_books():
    all_book_urls = []
    current_url = START_URL

    for page_number in range(1, 4):

        cache_file = get_cache_file(page_number)

        if not cache_file.exists() and page_number > 1:
            time.sleep(DELAY)

        html = fetch_page(current_url, cache_file)

        book_urls = extract_books(html, current_url)

        print(
            f"page={page_number} "
            f"books={len(book_urls)}"
        )

        all_book_urls.extend(book_urls)

        if page_number < 3:
            next_url = find_next_page(html, current_url)

            if not next_url:
                raise RuntimeError(
                    f"No next page found after page {page_number}"
                )

            current_url = next_url

    unique_book_urls = list(dict.fromkeys(all_book_urls))

    print(f"catalogue_pages=3")
    print(f"discovered={len(all_book_urls)}")
    print(f"unique_urls={len(unique_book_urls)}")

    return unique_book_urls


def main():
    discover_books()


if __name__ == "__main__":
    main()