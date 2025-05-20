from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from Rooms.models import *
from .forms import *
from django.contrib.auth.models import User
from Rooms.models import CustomUser  
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.core.mail import send_mail
import logging
from django.db.models.functions import TruncMonth
from django.db.models import Sum


def home_page(request):
    units = StorageUnit.objects.all()
    reviews = Review.objects.order_by('-created_at')[:5]  # Latest 5 reviews

    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('index')
    else:
        form = ReviewForm()

    return render(request, 'home/index.html', {
        'units': units,
        'form': form,
        'reviews': reviews,
    })



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            next_url = request.GET.get('next')  #  check if login was forced
            if next_url:
                return redirect(next_url)

            # Role-based redirection
            if user.is_admin:
                return redirect('admin_dashboard')
            elif user.is_employee:
                return redirect('employee_dashboard')
            else:
                return redirect('index')  # customer goes to homepage

        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'home/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('index')


logger = logging.getLogger(__name__)

@login_required(login_url='login')
def book_now(request, unit_id):
    unit = get_object_or_404(StorageUnit, id=unit_id)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            if booking.start_date < timezone.now().date():
                messages.error(request, "Start date cannot be in the past.")
                return render(request, 'home/book_now.html', {'form': form, 'unit': unit})

            booking.customer = request.user
            booking.storage_unit = unit
            booking.save()


            unit.decrement_available_units()

            Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                is_successful=True,
                transaction_reference='TXN123456'
            )

            Notification.objects.create(user=request.user, message="Booking Successful!")

            # ✅ EMAIL TO CLIENT
            subject = "Booking Confirmation"
            message = f"""
Dear {request.user.username},

Thank you for booking with PK Storage.

Your booking was successful.

Details:
- Unit: {unit.size}
- Total Amount: Ksh {booking.total_price}
- Booking End Date: {booking.end_date}

Regards,
PK Storage Team
"""
            # ✅ EMAIL TO ADMIN
            admin_subject = "New Booking Alert"
            admin_message = f"""
"""
            try:
                send_mail(
                    subject,
                    message,
                    'from@example.com',
                    [request.user.email],
                    fail_silently=False,
                )
                logger.info(f"Booking confirmation email sent to {request.user.email}")
            except Exception as e:
                logger.error(f"Failed to send booking confirmation: {e}")

            messages.success(request, "Booking successful!")
            return redirect('my_bookings')
    else:
        form = BookingForm()
    return render(request, 'home/book_now.html', {'form': form, 'unit': unit})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(customer=request.user)
    return render(request, 'home/my_bookings.html', {'bookings': bookings})

def logout_view(request):
    logout(request)
    return render(request, 'home/logout.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')

        user = CustomUser.objects.create_user(username=username, email=email, password=password1)
        user.is_customer = True  # Make default new user a customer
        user.save()

        login(request, user)
        messages.success(request, "Registration successful! You are now logged in.")
        return redirect('index')

    return render(request, 'home/register.html')


# Admin Check
def is_admin(user):
    return user.is_authenticated and user.is_admin

# Employee Check
def is_employee(user):
    return user.is_authenticated and user.is_employee

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    from Rooms.models import Booking, StorageUnit, CustomUser, Payment, Review

    bookings = Booking.objects.all()
    customers = CustomUser.objects.filter(is_customer=True)
    storage_units = StorageUnit.objects.all()
    reviews = Review.objects.all()

    # Financial analytics: Monthly revenue
    monthly_revenue = (
        Payment.objects.filter(is_successful=True)
        .annotate(month=TruncMonth('payment_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    return render(request, 'home/admin_dashboard.html', {
        'bookings': bookings,
        'customers': customers,
        'storage_units': storage_units,
        'monthly_revenue': monthly_revenue,
        'reviews': reviews,
    })


@login_required
@user_passes_test(is_employee)
def employee_dashboard(request):
    from Rooms.models import Booking

    # Example: list all active bookings for employee to manage
    active_bookings = Booking.objects.filter(is_active=True)

    return render(request, 'home/employee_dashboard.html', {
        'active_bookings': active_bookings,
    })


def storage_unit_detail(request, pk):
    storage_unit = StorageUnit.objects.get(pk=pk)
    reviews = storage_unit.reviews.all()

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.storage_unit = storage_unit
            review.save()
            return redirect('storage_unit_detail', pk=pk)
    else:
        form = ReviewForm()

    return render(request, 'home/storage_unit_detail.html', {
        'storage_unit': storage_unit,
        'reviews': reviews,
        'form': form
    })


@user_passes_test(is_employee)
@login_required
def employee_extend_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)

        new_end_date_str = request.POST.get('new_end_date')
        new_end_date = parse_date(new_end_date_str)

        if not new_end_date:
            messages.error(request, "Invalid date provided.")
            return redirect('my_bookings')

        if new_end_date <= booking.end_date:
            messages.error(request, "New end date must be later than the current end date.")
            return redirect('my_bookings')

        # Update end date
        booking.end_date = new_end_date

        # Reactivate booking if new end date is in the future
        if new_end_date >= timezone.now().date():
            booking.is_active = True

        # Save to recalculate total_price and persist changes
        booking.save()

        messages.success(request, f"Booking extended successfully to {new_end_date}.")
        return redirect('my_bookings')
    
@login_required
def customer_extend_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)

        new_end_date_str = request.POST.get('new_end_date')
        new_end_date = parse_date(new_end_date_str)

        if not new_end_date:
            messages.error(request, "Invalid date provided.")
            return redirect('my_bookings')

        if new_end_date <= booking.end_date:
            messages.error(request, "New end date must be later than the current end date.")
            return redirect('my_bookings')

        booking.end_date = new_end_date

        if new_end_date >= timezone.now().date():
            booking.is_active = True

        booking.save()

        messages.success(request, f"Booking extended successfully to {new_end_date}.")
        return redirect('my_bookings')



@user_passes_test(is_employee)
@login_required
def employee_terminate_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)
        booking.is_active = False
        booking.contract_status = 'terminated'
        booking.save()
        booking.storage_unit.increment_available_units()

        return redirect('employee_dashboard')

@login_required
def terminate_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)
        booking.is_active = False
        booking.contract_status = 'terminated'
        booking.save()
        booking.storage_unit.increment_available_units()

        return redirect('my_bookings')
