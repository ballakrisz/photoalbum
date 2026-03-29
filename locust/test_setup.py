import requests
import re

BASE_URL = "https://photoalbum-git-skicpausz-dev.apps.rm1.0a51.p1.openshiftapps.com"

def create_user(username, password):
    session = requests.Session()

    # 🔹 STEP 1: GET register page
    r = session.get(f"{BASE_URL}/register/")

    print("GET status:", r.status_code)
    print("Final URL:", r.url)

    # 🔹 Extract CSRF token from cookies (more reliable!)
    csrf_token = session.cookies.get("csrftoken")

    if not csrf_token:
        print("❌ No CSRF cookie!")
        print(r.text[:500])
        return

    # 🔹 STEP 2: POST register
    r = session.post(
        f"{BASE_URL}/register/",
        data={
            "username": username,
            "password1": password,
            "password2": password,
            "csrfmiddlewaretoken": csrf_token,
        },
        headers={
            "Referer": f"{BASE_URL}/register/",
            "X-CSRFToken": csrf_token,  # 🔥 important
        }
    )

    print(f"{username}: {r.status_code}")


if __name__ == "__main__":
    for i in range(50):
        create_user(f"locust_{i}", "Test12345!")