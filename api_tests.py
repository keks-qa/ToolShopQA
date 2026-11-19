import requests

import os
import requests

BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://api.practicesoftwaretesting.com",
).rstrip("/")


def test_filter_and_sort():
    page = 1
    products = []
    total = None

    while True:
        response = requests.get(
            f"{BASE_URL}/products",
            params={
                "page": page,
                "between": "price,1,20",
                "sort": "price,asc",
            },
            timeout=20,
        )
        assert response.status_code == 200, (
            f"Stranica {page}: HTTP {response.status_code}"
        )

        body = response.json()
        if total is None:
            total = body["total"]

        products.extend(body["data"])

        if page >= body["last_page"]:
            break
        page += 1

    assert products, "Prazna lista proizvoda"
    assert len(products) == total, (
        f"Ocekivano {total}, preuzeto {len(products)} proizvoda"
    )

    ids = [product["id"] for product in products]
    assert len(ids) == len(set(ids)), "Duplirani proizvodi"

    prices = [product["price"] for product in products]
    assert all(1 <= price <= 20 for price in prices), prices
    assert prices == sorted(prices), prices

    print(
        f"PASS: filter i sortiranje — "
        f"{len(products)} proizvoda, {page} stranica"
    )

def test_login_and_profile():
    email = "customer@practicesoftwaretesting.com"

    login = requests.post(
        f"{BASE_URL}/users/login",
        json={"email": email, "password": "welcome01"},
        timeout=20,
    )
    assert login.status_code == 200, (
        f"Login HTTP {login.status_code}: {login.text[:200]}"
    )

    token = login.json().get("access_token")
    assert isinstance(token, str) and token, "Login nije vratio token"

    profile = requests.get(
        f"{BASE_URL}/users/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    assert profile.status_code == 200, (
        f"Profil HTTP {profile.status_code}: {profile.text[:200]}"
    )
    assert profile.json().get("email") == email, "Pogresan korisnik"

    print("PASS: login i profil")

def test_expected_status(path, expected_status):
    response = requests.get(
        f"{BASE_URL}{path}",
        timeout=20,
    )

    assert response.status_code == expected_status, (
        f"{path}: ocekivan {expected_status}, "
        f"dobijen {response.status_code}"
    )

    print(f"PASS: {path} -> {expected_status}")

def test_cart_lifecycle():
    catalog = requests.get(
        f"{BASE_URL}/products",
        params={"between": "price,1,20", "sort": "price,asc"},
        timeout=20,
    )
    assert catalog.status_code == 200

    products = [
        p for p in catalog.json()["data"]
        if p["in_stock"] and not p["is_rental"]
    ]
    assert products, "Nema dostupnog proizvoda za test"
    product_id = products[0]["id"]
    
    created = requests.post(
        f"{BASE_URL}/carts",
        json={},
        timeout=20,
    )
    assert created.status_code == 201, (
        f"Kreiranje: HTTP {created.status_code}"
    )

    cart_id = created.json()["id"]
    url = f"{BASE_URL}/carts/{cart_id}"

    try:
        added = requests.post(
            url,
            json={"product_id": product_id, "quantity": 1},
            timeout=20,
        )
        assert added.status_code == 200, (
            f"Dodavanje: HTTP {added.status_code}"
        )

        cart = requests.get(url, timeout=20)
        assert cart.status_code == 200

        items = cart.json()["cart_items"]
        assert len(items) == 1, "Ocekivan jedan proizvod"
        assert items[0]["product_id"] == product_id
        assert items[0]["quantity"] == 1

        expected_quantity = 1

        for quantity, expected_status in (
            (0, 422),
            (1, 200),
            (99, 200),
            (100, 422),
        ):
            response = requests.put(
                f"{url}/product/quantity",
                headers={"Accept": "application/json"},
                json={"product_id": product_id, "quantity": quantity},
                timeout=20,
            )
            assert response.status_code == expected_status, (
                f"Kolicina {quantity}: ocekivan {expected_status}, "
                f"dobijen {response.status_code}"
            )

            if expected_status == 200:
                expected_quantity = quantity

            cart = requests.get(url, timeout=20)
            assert cart.status_code == 200

            items = cart.json()["cart_items"]
            assert len(items) == 1
            assert items[0]["quantity"] == expected_quantity, (
                f"Pogresno stanje posle slanja kolicine {quantity}"
            )

        updated = requests.put(
            f"{url}/product/quantity",
            json={"product_id": product_id, "quantity": 3},
            timeout=20,
        )
        assert updated.status_code == 200, (
            f"Izmena: HTTP {updated.status_code}"
        )

        cart = requests.get(url, timeout=20)
        assert cart.status_code == 200

        items = cart.json()["cart_items"]
        assert len(items) == 1, "Ocekivan jedan proizvod"
        assert items[0]["product_id"] == product_id
        assert items[0]["quantity"] == 3, "Kolicina nije sacuvana"

    finally:
        deleted = requests.delete(url, timeout=20)

    assert deleted.status_code == 204, (
        f"Brisanje: HTTP {deleted.status_code}"
    )

    check = requests.get(url, timeout=20)
    assert check.status_code == 404, (
        f"Posle brisanja: HTTP {check.status_code}"
    )

    print("PASS: kreiranje, citanje i brisanje korpe")

def run_tests():
    cases = [
        ("Filter i sortiranje", test_filter_and_sort, ()),
        ("Login i profil", test_login_and_profile, ()),
        (
            "Nepostojeci proizvod",
            test_expected_status,
            ("/products/00000000000000000000000000", 404),
        ),
        (
            "Profil bez tokena",
            test_expected_status,
            ("/users/me", 401),
        ),
        ("Zivotni ciklus korpe", test_cart_lifecycle, ()),
    ]

    passed = failed = errors = 0

    for name, function, args in cases:
        try:
            function(*args)
        except AssertionError as error:
            failed += 1
            print(f"FAIL: {name}: {error}")
        except Exception as error:
            errors += 1
            print(f"ERROR: {name}: {type(error).__name__}: {error}")
        else:
            passed += 1

    print(f"\nREZULTAT: PASS={passed}, FAIL={failed}, ERROR={errors}")
    return 1 if failed or errors else 0

if __name__ == "__main__":
    raise SystemExit(run_tests())