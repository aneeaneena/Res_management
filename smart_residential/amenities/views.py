from django.shortcuts import render


def list_amenities(request):
    return render(request, 'amenities/list.html')

def detail(request):
    return render(request, 'amenities/detail.html')

def book_slot(request):
    return render(request, 'amenities/book_slot.html')

def history(request):
    return render(request, 'amenities/history.html')
