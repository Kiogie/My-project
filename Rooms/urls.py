from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('book-now/<int:unit_id>/', views.book_now, name='book_now'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
]
