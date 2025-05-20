from django.urls import path, include
from home.views import home_page
from django.contrib import admin

from . import views

urlpatterns = [
    path('', views.home_page, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('book-now/<int:unit_id>/', views.book_now, name='book_now'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('pk-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('bookings/<int:booking_id>/terminate/', views.terminate_booking, name='terminate_booking'),
    path('employee/booking/<int:booking_id>/terminate/', views.terminate_booking, name='terminate_booking'),
    path('bookings/<int:booking_id>/extend/', views.customer_extend_booking, name='extend_booking'),
    path('bookings/<int:booking_id>/terminate/', views.terminate_booking, name='terminate_booking'),
    path('employee/booking/<int:booking_id>/terminate/', views.employee_terminate_booking, name='employee_terminate_booking'),
    path('employee/booking/<int:booking_id>/extend/', views.employee_extend_booking, name='employee_extend_booking'),
    


]
