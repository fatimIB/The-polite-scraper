from pathlib import Path
import requests


URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_DIR = Path("cache")
CACHE_FILE = CACHE_DIR / "catalogue-page-1.html"

USER_AGENT = "FlyRankInternship A9/1.0(https://github.com/fatimIB/The-polite-scraper)"
TIMEOUT = 10


def fetch_page():
    CACHE_DIR.mkdir(exist_ok=True)

    headers = {
        "User-Agent": USER_AGENT
    }

    response = requests.get(
        URL,
        headers=headers,
        timeout=TIMEOUT
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch page: HTTP {response.status_code}"
        )

    CACHE_FILE.write_text(response.text, encoding="utf-8")

    print(f"FETCH status={response.status_code} bytes={len(response.content)}")


def main():
    if CACHE_FILE.exists():
        content = CACHE_FILE.read_bytes()
        print(f"CACHE HIT bytes={len(content)}")
    else:
        fetch_page()


if __name__ == "__main__":
    main()