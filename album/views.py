from django.shortcuts import render, redirect, get_object_or_404
from .models import Photo
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.contrib.auth.models import User
from .forms import PhotoForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
import os

def photo_list(request):
    sort = request.GET.get("sort")
    page_number = request.GET.get("page")

    photos = Photo.objects.all()

    # Sorting 
    if sort == "name":
        photos = photos.order_by("name")
    else:
        photos = photos.order_by("-uploaded_at")

    # Pagination (9 per page to match my UI)
    paginator = Paginator(photos, 9)
    photos_page = paginator.get_page(page_number)

    return render(request, "album/photo_list.html", {
        "photos": photos_page,
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

    photo.image.delete(save=False)  # delete photo from S3
    photo.delete()                  # delet DB row
    return redirect("photo_list")

@staff_member_required
def delete_locust_photos(request):
    #  Get all locust users
    locust_users = User.objects.filter(username__startswith="locust_")

    # Get all their photos
    photos = Photo.objects.filter(owner__in=locust_users)

    # Delete images from S3 FIRST
    for photo in photos:
        photo.image.delete(save=False)

    # Delete photo rows
    photos.delete()

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
