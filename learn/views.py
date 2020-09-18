from django.shortcuts import HttpResponse, render
from learn.models import Test


def index(request):
    context = {}
    context['hello'] = 'Hello World!'
    test1 = Test(name='adsjfilds')
    test1.save()
    return render(request, 'runoob.html', context)
    # return HttpResponse("Hello world    hello    !")
