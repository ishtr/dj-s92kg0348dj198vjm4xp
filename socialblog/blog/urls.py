from django.urls import path
from . import views

 
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('post/create/', views.post_create, name='post_create'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/like/<str:action>/', views.like_post, name='like_post'),
    path('chat/', views.chat_room, name='chat_room'),
    path('profile/', views.profile, name='profile'),
]

