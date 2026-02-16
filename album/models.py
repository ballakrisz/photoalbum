from django.db import models
from django.contrib.auth.models import User

class Photo(models.Model):
    name = models.CharField(max_length=40)
    image = models.ImageField(upload_to='photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
