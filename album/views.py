from django.shortcuts import render, redirect, get_object_or_404
from .models import Photo
from django.contrib.auth.decorators import login_required
from .forms import PhotoForm

def photo_list(request):
    sort = request.GET.get('sort', 'name')
    photos = Photo.objects.all().order_by(sort)
    return render(request, 'album/photo_list.html', {'photos': photos})

def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    return render(request, 'album/photo_detail.html', {'photo': photo})

@login_required
def upload_photo(request):
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
def delete_photo(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if photo.owner == request.user:
        photo.delete()
    return redirect('photo_list')
