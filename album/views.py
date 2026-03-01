from django.shortcuts import render, redirect, get_object_or_404
from .models import Photo
from django.contrib.auth.decorators import login_required
from .forms import PhotoForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
import os

def photo_list(request):
    sort = request.GET.get("sort")

    photos = Photo.objects.all()

    if sort == "name":
        photos = photos.order_by("name")
    elif sort == "date":
        photos = photos.order_by("-uploaded_at")
    else:
        photos = photos.order_by("-uploaded_at")

    return render(request, "album/photo_list.html", {
        "photos": photos,
        "current_sort": sort
    })

def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)

    return render(request, "album/photo_detail.html", {
        "photo": photo
    })

@login_required
def photo_upload(request):
    if request.method == "POST":
        name = request.POST.get("name")
        image = request.FILES.get("image")

        # Name validation
        if not name or len(name) > 40:
            messages.error(request, "Photo name must be 40 characters or less.")
            return render(request, "album/photo_upload.html")

        # File exists
        if not image:
            messages.error(request, "Please select an image.")
            return render(request, "album/photo_upload.html")

        # Size check (2MB)
        if image.size > 2 * 1024 * 1024:
            messages.error(request, "Image size must be less than 2MB.")
            return render(request, "album/photo_upload.html")

        # MIME type check
        if not image.content_type.startswith("image/"):
            messages.error(request, "Only image files are allowed.")
            return render(request, "album/photo_upload.html")

        # Extension check
        ext = os.path.splitext(image.name)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif"]:
            messages.error(request, "Only JPG, PNG or GIF images are allowed.")
            return render(request, "album/photo_upload.html")

        Photo.objects.create(
            name=name,
            image=image,
            owner=request.user
        )

        return redirect("photo_list")

    return render(request, "album/photo_upload.html")

@login_required
def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk)

    if not (request.user == photo.owner or request.user.is_staff):
        return HttpResponseForbidden("You are not allowed to delete this photo.")

    photo.delete()
    return redirect("photo_list")

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})
