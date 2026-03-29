from django.shortcuts import render, redirect, get_object_or_404
from .models import Photo
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
import os
import threading

# Progress tracker
delete_progress = {
    "total": 0,
    "deleted": 0,
    "running": False
}


# Background delete task
def delete_locust_photos_task():
    global delete_progress

    locust_users = User.objects.filter(username__startswith="locust_")
    photos = list(Photo.objects.filter(owner__in=locust_users))

    delete_progress["total"] = len(photos)
    delete_progress["deleted"] = 0
    delete_progress["running"] = True

    for photo in photos:
        if photo.image:
            photo.image.delete(save=False)
        photo.delete()
        delete_progress["deleted"] += 1

    delete_progress["running"] = False  # reset after done


# Gallery view
@cache_page(5)
def photo_list(request):
    sort = request.GET.get("sort")
    page_number = request.GET.get("page")

    photos = Photo.objects.all()

    if sort == "name":
        photos = photos.order_by("name")
    else:
        photos = photos.order_by("-uploaded_at")

    paginator = Paginator(photos, 9)
    photos_page = paginator.get_page(page_number)

    return render(request, "album/photo_list.html", {
        "photos": photos_page,
        "current_sort": sort
    })


def next_photo(request):
    exclude_ids = request.GET.getlist("exclude[]")
    sort = request.GET.get("sort", "date")
    page = int(request.GET.get("page", 1))

    photos = Photo.objects.all()

    # same ordering as gallery
    if sort == "name":
        photos = photos.order_by("name")
    else:
        photos = photos.order_by("-uploaded_at")

    paginator = Paginator(photos, 9) 

    try:
        next_page = paginator.page(page + 1)
    except:
        return JsonResponse({"photo": None})

    # find first photo not currently shown
    for photo in next_page.object_list:
        if str(photo.id) not in exclude_ids:
            return JsonResponse({
                "photo": {
                    "id": photo.id,
                    "name": photo.name,
                    "image": photo.image.url,
                    "uploaded": photo.uploaded_at.strftime("%Y-%m-%d %H:%M"),
                    "owner": photo.owner.username,
                }
            })

    return JsonResponse({"photo": None})

#  Detail
def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)

    return render(request, "album/photo_detail.html", {
        "photo": photo,
        "next": request.GET.get("next") or "/"  # fallback
    })


# Upload (preserve sorting/page)
@login_required
def photo_upload(request):
    if request.method == "POST":
        name = request.POST.get("name")
        image = request.FILES.get("image")

        if not name or len(name) > 40:
            messages.error(request, "Photo name must be 40 characters or less.")
            return render(request, "album/photo_upload.html")

        if not image:
            messages.error(request, "Please select an image.")
            return render(request, "album/photo_upload.html")

        if image.size > 2 * 1024 * 1024:
            messages.error(request, "Image size must be less than 2MB.")
            return render(request, "album/photo_upload.html")

        if not image.content_type.startswith("image/"):
            messages.error(request, "Only image files are allowed.")
            return render(request, "album/photo_upload.html")

        ext = os.path.splitext(image.name)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif"]:
            messages.error(request, "Only JPG, PNG or GIF images are allowed.")
            return render(request, "album/photo_upload.html")

        Photo.objects.create(
            name=name,
            image=image,
            owner=request.user
        )

        return redirect(request.META.get("HTTP_REFERER", "photo_list"))

    return render(request, "album/photo_upload.html")


#  Delete (idempotent + preserve state)
@login_required
def photo_delete(request, pk):
    photo = Photo.objects.filter(pk=pk).first()

    redirect_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/"

    if not photo:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "ok"})
        return redirect(redirect_url)

    if not (request.user == photo.owner or request.user.is_staff):
        return HttpResponseForbidden("Not allowed")

    if photo.image:
        photo.image.delete(save=False)

    photo.delete()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"status": "ok"})

    return redirect(redirect_url)


# Start async delete of locust stress test photos
@staff_member_required
def start_delete_locust(request):
    global delete_progress

    if delete_progress["running"]:
        return JsonResponse({"status": "already running"})

    thread = threading.Thread(target=delete_locust_photos_task)
    thread.start()

    return JsonResponse({"status": "started"})


#  Progress endpoint
def delete_progress_view(request):
    return JsonResponse(delete_progress)


#  Register
def register(request):
    from django.contrib.auth.forms import UserCreationForm

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})