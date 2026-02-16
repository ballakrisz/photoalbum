from django.shortcuts import render, redirect, get_object_or_404
from .models import Photo
from django.contrib.auth.decorators import login_required
from .forms import PhotoForm
from django.contrib.auth.forms import UserCreationForm

def photo_list(request):
    sort = request.GET.get('sort', 'name')
    photos = Photo.objects.all().order_by(sort)
    return render(request, 'album/photo_list.html', {'photos': photos})

def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    return render(request, 'album/photo_detail.html', {'photo': photo})

@login_required
def photo_upload(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.owner = request.user
            photo.save()
            return redirect('photo_list')
    else:
        form = PhotoForm()
    return render(request, 'album/upload.html', {'form': form})

@login_required
def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk, user=request.user)
    if request.method == 'POST':
        photo.delete()
        return redirect('photo_list')
    return redirect('photo_detail', pk=pk)

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})
