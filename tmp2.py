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

    @task(2)
    def index(self):
        self.client.get("/")

    @task(2)
    def upload(self):
        # STEP 3: Get upload page (for CSRF)
        response = self.client.get("/upload/")
        csrf_token = self.get_csrf_token(response)

        if not csrf_token:
            return

        # ✅ REPLACED: real image using PIL (64x64 colored square)
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
        with self.client.post(
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
        ) as response:

            # Detect Django validation errors
            if "error" in response.text.lower():
                response.failure("Upload failed (validation error)")
