from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.files import File

import io, os
from io import BytesIO
import tempfile

import numpy as np
import skimage

from PIL import Image, ImageOps
from PIL.Image import Image as PilImage

from .forms import UploadFileForm

@login_required
def index(request):
    # url lets javascript grab the url for the fetch call
    url = reverse('coloring-page')
    return render(request, 'index.html', {'url':url})

@login_required
def coloring_page(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]
            if file is None:
                return HttpResponse("Missing input-image parameter")
            
            if file.size > 1024 * 1024:
                compressed_file = compress(file)    
                input_image = Image.open(compressed_file)
            else:        
                input_image = Image.open(file)
            
            output_image = generate_coloring_page(input_image)

            image_io = io.BytesIO()
            output_format = "png"
            output_image.save(image_io, format=output_format)
            image_io.seek(0)

            response = HttpResponse(image_io, content_type='image/png')
            
            return response
        else:
            return JsonResponse({"error": form.errors}, status=403)
    return render(request, 'index.html', {'form': form})
def compress(image):
    im = Image.open(image)
    im_io = BytesIO() 
    im.save(im_io,"png", optimize=True, quality=20) 
    new_image = File(im_io, name=image.name)
    return new_image

def generate_coloring_page(input: PilImage) -> PilImage:
    # Convert to grayscale if needed
    if input.mode != "L":
        input = input.convert("L")
    # Transpose if taken in non-native orientation (rotated digital camera)
    NATIVE_ORIENTATION = 1
    if input.getexif().get(0x0112, NATIVE_ORIENTATION) != NATIVE_ORIENTATION:
        input = ImageOps.exif_transpose(input)
    np_image = np.asarray(input)

    # Remove some noise to keep the most visible edges
    np_image = skimage.restoration.denoise_tv_chambolle(np_image, weight=0.05)
    # Detect the edges
    np_image = skimage.filters.sobel(np_image)
    # Convert to 8 bpp
    np_image = skimage.util.img_as_ubyte(np_image)
    # Invert to get dark edges on a light background
    np_image = 255 - np_image
    # Improve the contrast
    np_image = skimage.exposure.rescale_intensity(np_image)

    return Image.fromarray(np_image)