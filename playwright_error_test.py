from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def inspect_search_error():
    with sync_playwright() as p:
        p.selectors.set_test_id_attribute("data-test")
        browser = p.chromium.launch(channel="chrome", headless=False)
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
                    status=500,
                    json={"message": "Simulirana greska servera"},
                ),
            )

            page.goto("https://practicesoftwaretesting.com/")

            expect(
                page.get_by_test_id("product-name").first
            ).to_be_visible(timeout=20_000)

            page.get_by_test_id("search-query").fill("Slip Joint Pliers")

            with page.expect_response("**/products/search*") as response_info:
                page.get_by_test_id("search-submit").click()

            response = response_info.value
            assert response.status == 500
            print(f"Search HTTP status: {response.status}")

            expect(
                page.get_by_text(
                    "There are no products found.",
                    exact=True,
                )
            ).to_be_visible(timeout=20_000)

            page.screenshot(
                path=Path(__file__).with_name("search_500.png"),
                full_page=True,
            )

            print("REPRODUCED: HTTP 500 uz poruku da nema proizvoda")

        finally:
            try:
                context.tracing.stop(
                    path=Path(__file__).with_name("error_trace.zip")
                )
            finally:
                browser.close()


if __name__ == "__main__":
    inspect_search_error()