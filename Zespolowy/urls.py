"""
URL configuration for Zespolowy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from kanban.views import ColumnAPIView, ColumnRedirectView,  NoteAPIView, TeamAPIView, ColumnHTMLView, PersonAPIView, PersonNoteAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/people/', PersonAPIView.as_view()),
    path('api/columns/', ColumnAPIView.as_view()),
    path('api/notes/', NoteAPIView.as_view()),
    path('api/notes/connections/', PersonNoteAPIView.as_view()),
    path('api/teams/', TeamAPIView.as_view()),
    path('columns/', ColumnHTMLView.as_view()),
    path('', ColumnRedirectView.as_view())
]
