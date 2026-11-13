from playwright.sync_api import sync_playwright, expect
from pathlib import Path
import os


def test_search_empty_mock():
    empty_response = {
        "current_page": 1,
        "data": [],
        "from": None,
        "last_page": 1,
        "per_page": 9,
        "to": None,
        "total": 0,
    }

    with sync_playwright() as p:
        p.selectors.set_test_id_attribute("data-test")
        browser = p.chromium.launch(
            channel="chrome",
            headless=os.getenv("HEADLESS") == "1",
        )

        context = browser.new_context()
        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
        )

        try:
            page = context.new_page()

            page.route(
                "**/products/search*",
                lambda route: route.fulfill(
                    status=200,
                    json=empty_response,
                ),
            )

            page.goto("https://practicesoftwaretesting.com/")

            expect(
                page.get_by_test_id("product-name").first
            ).to_be_visible(timeout=20_000)

            page.get_by_test_id("search-query").fill("Slip Joint Pliers")
            page.get_by_test_id("search-submit").click()

            expect(
                page.locator('a[data-test^="product-"]')
            ).to_have_count(0, timeout=20_000)

            expect(
                page.get_by_text(
                    "There are no products found.",
                    exact=True,
                )
            ).to_be_visible()

            print("PASS: UI prikazuje prazan rezultat uz mockovan API odgovor")


        finally:

            try:

                context.tracing.stop(

                    path=Path(__file__).with_name("search_trace.zip")

                )

            finally:

                browser.close()


if __name__ == "__main__":
    test_search_empty_mock()