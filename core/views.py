from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, "core/home.html")

def pulse(request):
    return HttpResponse("Working!")

def spots_geojson(request):
    data = [
        {"name": "Bunratty Pier", "lat": 52.699, "lon": -8.814, "type": "kayak"},
        {"name": "Kilrush Marina", "lat": 52.640, "lon": -9.483, "type": "kayak/Sailing/Tours "},
        {"name": "Foynes Marina", "lat": 52.615, "lon": -9.114, "type": "kayak/Sailing" },
        {"name": "Glin Pier", "lat": 52.5754, "lon": -9.2834, "type": "Swimming/kayak" },
        {"name": "Kilteery Pier", "lat": 52.5947, "lon": -9.2237, "type": "Swimming/kayak" },
    ]
    return JsonResponse(data, safe=False)
