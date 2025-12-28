from django.urls import path
from django.views.generic import TemplateView
from nitro.api import api
from counter_app.components.counter import Counter

def index(request):
    from django.shortcuts import render
    counter = Counter(request=request, initial=0, step=1)
    return render(request, 'index.html', {'counter': counter})

urlpatterns = [
    path('', index, name='index'),
    path('api/nitro/', api.urls),
]
