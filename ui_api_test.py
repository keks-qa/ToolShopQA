import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_search_ui_matches_api():
    query = "Slip Joint Pliers"

    response = requests.get(
        "https://api.practicesoftwaretesting.com/products/search",
        params={"q": query},
        timeout=20,
    )
    assert response.status_code == 200

    products = response.json()["data"]
    assert len(products) == 1
    product = products[0]

    driver = webdriver.Chrome()

    cart_id = None

    try:
        driver.maximize_window()
        driver.get("https://practicesoftwaretesting.com/")
        wait = WebDriverWait(driver, 20)

        wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, '[data-test="product-name"]')
        ))

        search = driver.find_element(
            By.CSS_SELECTOR, '[data-test="search-query"]'
        )
        search.send_keys(query)
        driver.find_element(
            By.CSS_SELECTOR, '[data-test="search-submit"]'
        ).click()

        wait.until(
            lambda d: len(d.find_elements(
                By.CSS_SELECTOR, 'a[data-test^="product-"]'
            )) == 1
        )

        card = driver.find_element(
            By.CSS_SELECTOR, f'a[data-test="product-{product["id"]}"]'
        )
        name = card.find_element(
            By.CSS_SELECTOR, '[data-test="product-name"]'
        ).text.strip()
        price = card.find_element(
            By.CSS_SELECTOR, '[data-test="product-price"]'
        ).text.strip()

        expected_price = f"${product['price']:.2f}"

        assert name == product["name"], f"Pogresan naziv: {name}"
        assert price == expected_price, (
            f"UI cena: {price}, API cena: {expected_price}"
        )

        print("PASS: naziv i cena na UI odgovaraju API-ju")

        card.click()

        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-test="add-to-cart"]')
        )).click()

        cart_id = wait.until(
            lambda d: d.execute_script(
                "return sessionStorage.getItem('cart_id');"
            )
        )

        wait.until(
            lambda d: d.execute_script(
                "return sessionStorage.getItem('cart_quantity');"
            ) == "1"
        )

        cart = requests.get(
            f"https://api.practicesoftwaretesting.com/carts/{cart_id}",
            timeout=20,
        )
        assert cart.status_code == 200

        items = cart.json()["cart_items"]
        assert len(items) == 1, "Ocekivan jedan proizvod u korpi"
        assert items[0]["product_id"] == product["id"]
        assert items[0]["quantity"] == 1, "Pogresna kolicina"


    finally:

        try:

            if cart_id:
                cleanup = requests.delete(

                    f"https://api.practicesoftwaretesting.com/carts/{cart_id}",

                    timeout=20,

                )

        finally:

            driver.quit()

    assert cleanup.status_code == 204, (

        f"Brisanje testne korpe: HTTP {cleanup.status_code}"

    )

    print("PASS: proizvod dodat kroz UI postoji u API korpi")


if __name__ == "__main__":
    test_search_ui_matches_api()