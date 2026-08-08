from datetime import datetime, timezone
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
    all_books = []
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

        for book_url in book_urls:
            all_books.append({
                "url": book_url,
                "source_page": current_url
            })

        if page_number < 3:
            next_url = find_next_page(html, current_url)

            if not next_url:
                raise RuntimeError(
                    f"No next page found after page {page_number}"
                )

            current_url = next_url

    unique_books = {}

    for book in all_books:
        unique_books[book["url"]] = book

    unique_books = list(unique_books.values())

    print("catalogue_pages=3")
    print(f"discovered={len(all_books)}")
    print(f"unique_urls={len(unique_books)}")

    return unique_books

def get_detail_cache_file(index):
    return CACHE_DIR / "details" / f"book-{index}.html"


def fetch_detail_page(url, cache_file):
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    if cache_file.exists():
        content = cache_file.read_bytes()
        print(f"CACHE HIT {cache_file.name} bytes={len(content)}")
        return content

    time.sleep(DELAY)

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
            f"Failed to fetch {url}: HTTP {response.status_code}"
        )

    cache_file.write_text(response.text, encoding="utf-8")

    print(
        f"FETCH {cache_file.name} "
        f"status={response.status_code} "
        f"bytes={len(response.content)}"
    )

    return response.content


def extract_book_record(html, product_url, source_page):
    soup = BeautifulSoup(html, "html.parser")

    product = soup.select_one("article.product_page")

    if not product:
        raise RuntimeError(
            f"Product section not found: {product_url}"
        )

    # Title
    title_element = product.select_one("div.product_main h1")
    title = title_element.get_text(strip=True) if title_element else None

    # Price
    price_element = product.select_one("div.product_main .price_color")
    price_text = (
        price_element.get_text(strip=True)
        if price_element
        else None
    )

    # Availability
    availability_element = product.select_one(
        "div.product_main .availability"
    )

    availability_text = (
        availability_element.get_text(" ", strip=True)
        if availability_element
        else None
    )

    # Rating
    rating_element = product.select_one(
        "div.product_main .star-rating"
    )

    rating_text = None

    if rating_element:
        classes = rating_element.get("class", [])

        rating_names = {
            "One",
            "Two",
            "Three",
            "Four",
            "Five"
        }

        for class_name in classes:
            if class_name in rating_names:
                rating_text = class_name
                break

    # Description
    description_element = soup.select_one(
        "#product_description + p"
    )

    description = (
        description_element.get_text(strip=True)
        if description_element
        else None
    )

    fetched_at = datetime.now(timezone.utc).isoformat()

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at
    }


def extract_all_details(books):
    records = []

    for index, book in enumerate(books, start=1):

        html = fetch_detail_page(
            book["url"],
            get_detail_cache_file(index)
        )

        record = extract_book_record(
            html,
            book["url"],
            book["source_page"]
        )

        records.append(record)

        if index == 1:
            print("\nFIRST RAW RECORD:")
            print(record)
            print()

    print(f"detail_pages={len(records)}")

    return records


def main():
    books = discover_books()

    records = extract_all_details(books)

    print(f"raw_records={len(records)}")


if __name__ == "__main__":
    main()