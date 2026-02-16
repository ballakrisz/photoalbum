from django.shortcuts import render, redirect, get_object_or_404
from .models import Photo
from django.contrib.auth.decorators import login_required
from .forms import PhotoForm
from django.contrib.auth.forms import UserCreationForm

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
    return render(request, 'album/photo_detail.html', {'photo': photo})

@login_required
def photo_upload(request):
    if request.method == "POST":
        name = request.POST.get("name")
        image = request.FILES.get("image")

        Photo.objects.create(
            name=name,
            image=image,
            owner=request.user
        )

        return redirect("photo_list")

    return render(request, "album/upload_photo.html")

@login_required
def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk)

    if photo.owner != request.user:
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
