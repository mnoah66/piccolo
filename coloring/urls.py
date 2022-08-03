from django.urls import path, include

from .views import index, coloring_page

urlpatterns = [
    path("", index, name="coloring-index"),
    path("api/coloring-page", coloring_page, name="coloring-page"),

]
