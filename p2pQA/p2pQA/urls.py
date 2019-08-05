"""p2pQA URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from qabroadcast import account
from qabroadcast import broadcast
from qabroadcast import adminOP

urlpatterns = [
    path('admin/', admin.site.urls),
    #account
    path('account/register',account.register),
    path('account/login',account.login),
    path('account/logout',account.logout),
    #QA
    path('api/query',broadcast.query),  
    path('api/answer',broadcast.answer),
    path('api/questions',broadcast.questions),
    path('api/answers',broadcast.answers),
    path('api/querylist',broadcast.querylist),
    path('api/queryamount',broadcast.queryAmount),
    path('api/accept',broadcast.acceptAnswer),
    path('api/reject',broadcast.reject),
    path('api/checkpoint',adminOP.checkPoint)
]
