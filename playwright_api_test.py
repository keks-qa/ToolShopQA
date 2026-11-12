from playwright.sync_api import sync_playwright, expect


def test_search_playwright():
    with sync_playwright() as p:
        p.selectors.set_test_id_attribute("data-test")

        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
        )
        api = p.request.new_context(
            base_url="https://api.practicesoftwaretesting.com"
        )

        try:
            query = "Slip Joint Pliers"

            response = api.get(
                "/products/search",
                params={"q": query},
            )
            assert response.status == 200

            products = response.json()["data"]
            assert len(products) == 1
            product = products[0]

            page = browser.new_page()
            page.goto("https://practicesoftwaretesting.com/")

            expect(
                page.get_by_test_id("product-name").first
            ).to_be_visible(timeout=20_000)

            page.get_by_test_id("search-query").fill(query)
            page.get_by_test_id("search-submit").click()

            cards = page.locator('a[data-test^="product-"]')
            expect(cards).to_have_count(1, timeout=20_000)

            card = page.get_by_test_id(f"product-{product['id']}")

            expect(card.get_by_test_id("product-name")).to_have_text(
                product["name"]
            )
            expect(card.get_by_test_id("product-price")).to_have_text(
                f"${product['price']:.2f}"
            )

            print("PASS: Playwright UI naziv i cena odgovaraju API-ju")

        finally:
            browser.close()
            api.dispose()


if __name__ == "__main__":
    test_search_playwright()