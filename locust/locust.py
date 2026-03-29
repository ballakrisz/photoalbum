from locust import HttpUser, task, between
import re
from PIL import Image
import io
import random
import string

class PhotoAlbumUser(HttpUser):
    wait_time = between(1, 2)

    def get_csrf_token(self, response):
        match = re.search(r'name="csrfmiddlewaretoken" value="(.+?)"', response.text)
        return match.group(1) if match else None

    def random_string(self, length=8):
            return ''.join(random.choices(string.ascii_lowercase, k=length))

    # helper to query the locut user's own photos
    def extract_my_photo_ids(self, html):
        ids = []

        # split into cards
        cards = html.split('<div class="col-md-4 mb-4">')

        for card in cards:
            # find photo id - FIXED: single backslash
            id_match = re.search(r'/photo/(\d+)/', card)

            # find owner
            owner_match = re.search(r'By:\s*([^<]+)', card)

            if id_match and owner_match:
                photo_id = int(id_match.group(1))
                owner = owner_match.group(1).strip()

                if owner == self.username:
                    ids.append(photo_id)
        return ids

    def on_start(self):
        self.username = f"locust_{self.random_string()}"
        self.password = "StressTest0"
        self.my_photo_ids = []

        # 🔹 REGISTER
        response = self.client.get("/register/")
        csrf_token = self.get_csrf_token(response)

        self.client.post(
            "/register/",
            data={
                "username": self.username,
                "password1": self.password,
                "password2": self.password,
                "csrfmiddlewaretoken": csrf_token,
                "next": "/",
            },
            headers={"Referer": self.host + "/register/"}
        )

        # 🔹 LOGIN
        response = self.client.get("/accounts/login/")
        csrf_token = self.get_csrf_token(response)

        self.client.post(
            "/accounts/login/",
            data={
                "username": self.username,
                "password": self.password,
                "csrfmiddlewaretoken": csrf_token,
                "next": "/",
            },
            headers={"Referer": self.host + "/accounts/login/"}
        )

    # VIEWING POHOTO LIST
    @task(2)
    def index(self):
        response = self.client.get("/")
        print(response.text)

        # update owned photo IDs
        new_ids = self.extract_my_photo_ids(response.text)
        for i in new_ids:
            if i not in self.my_photo_ids:
                self.my_photo_ids.append(i)

        print("USERNAME:", self.username)
        print("IDS:", self.my_photo_ids)

    # SORTING
    @task(1)
    def sort(self):
        self.client.get("/?sort=name")
        self.client.get("/?sort=date")

    @task(2)
    def upload(self):
        response = self.client.get("/upload/")
        csrf_token = self.get_csrf_token(response)

        if not csrf_token:
            return

        img = Image.new(
            "RGB",
            (64, 64),
            (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            ),
        )
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        image_bytes = buf.getvalue()

        # STEP 4: Upload
        response = self.client.post(
            "/upload/",
            data={
                "name": "test-photo",
                "csrfmiddlewaretoken": csrf_token,
            },
            files={
                "image": ("test.jpg", image_bytes, "image/jpeg")
            },
            headers={"Referer": self.host + "/upload/"},
            catch_response=True
        ) 
        # refresh and collect new IDs
        response = self.client.get("/")
        new_ids = self.extract_my_photo_ids(response.text)

        for i in new_ids:
            if i not in self.my_photo_ids:
                self.my_photo_ids.append(i)

        print("AFTER UPLOAD IDS:", self.my_photo_ids)

    #  VIEW PHOTO DETAIL 
    @task(1)
    def view_detail(self):
        if not self.my_photo_ids:
            return

        photo_id = random.choice(self.my_photo_ids)
        self.client.get(f"/photo/{photo_id}/")

    # Delete photo
    @task(1)
    def delete(self):
        if not self.my_photo_ids:
            return

        photo_id = random.choice(self.my_photo_ids)

        self.client.get(f"/delete/{photo_id}/")
        self.my_photo_ids.remove(photo_id)

    #  LOGOUT + LOGIN again (session churn)
    @task(1)
    def logout_login(self):
        # 🔹 STEP 1: get page to extract CSRF
        response = self.client.get("/")
        csrf_token = self.get_csrf_token(response)

        # fallback: try login page if not found
        if not csrf_token:
            response = self.client.get("/accounts/login/")
            csrf_token = self.get_csrf_token(response)

        # 🔹 POST logout
        self.client.post(
            "/accounts/logout/",
            data={
                "csrfmiddlewaretoken": csrf_token,
                "next": "/",
            },
            headers={"Referer": self.host + "/"}
        )

        response = self.client.get("/accounts/login/")
        csrf_token = self.get_csrf_token(response)

        self.client.post(
            "/accounts/login/",
            data={
                "username": self.username,
                "password": self.password,
                "csrfmiddlewaretoken": csrf_token,
                "next": "/",
            },
            headers={"Referer": self.host + "/accounts/login/"}
        )
