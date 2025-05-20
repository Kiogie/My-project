from django.http import BadHeaderError, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import StorageUnit, Booking, Payment, Notification
from .forms import BookingForm
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Booking, Notification
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def index(request):
    units = StorageUnit.objects.filter(available=True)
    return render(request, 'home/index.html', {'units': units})


# Modify the book_now view to send an email after booking is confirmed
@login_required
def book_now(request, unit_id):
    unit = get_object_or_404(StorageUnit, id=unit_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.storage_unit = unit
            booking.save()

            # Decrement available units
            unit.decrement_available_units()

            # Create Payment (dummy, later integrate real payment)
            Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                is_successful=True,
                transaction_reference='TXN123456'
            )

            Notification.objects.create(user=request.user, message="Booking Successful!")

            from django.core.mail import send_mail, BadHeaderError
from django.conf import settings

def send_booking_email(user, booking):
    try:
        subject = 'Booking Confirmed! PK Storage'
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [user.email]

        # Render HTML content with dynamic data
        html_content = render_to_string(
            'emails/booking_confirmation.html',  # Path to your HTML template
            {
                'customer_name': user.username,
                'unit_size': booking.storage_unit.size,
                'booking_id': booking.id,
                'price_per_month': booking.storage_unit.price_per_month,
                'start_date': booking.start_date,
                'end_date': booking.end_date,
                'site_url': 'https://yourwebsite.com',
                'unsubscribe_link': 'https://yourwebsite.com/unsubscribe'
            }
        )

        # Create the plain-text version of the email
        text_content = strip_tags(html_content)

        # Send the email
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        print("Booking confirmation email sent.")

    except BadHeaderError:
        print("Invalid header found when sending email.")
    except Exception as e:
        print(f"Error occurred while sending email: {e}")



# Function to send email
def send_booking_email(user, booking):
    subject = 'Booking Confirmed! PK Storage'
    from_email = 'Your Company <murithibrian58@gmail.com>'
    to = [user.email]

    # Render HTML content with dynamic data
    html_content = render_to_string(
        'emails/booking_confirmation.html',  # Path to your HTML template
        {
            'customer_name': user.username,
            'unit_size': booking.storage_unit.size,
            'booking_id': booking.id,
            'price_per_month': booking.storage_unit.price_per_month,
            'start_date': booking.start_date,
            'end_date': booking.end_date,
            'site_url': 'https://yourwebsite.com',
            'unsubscribe_link': 'https://yourwebsite.com/unsubscribe'
        }
    )

    # Create the plain-text version of the email
    text_content = strip_tags(html_content)

    # Send the email
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    print("Booking confirmation email sent.")

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(customer=request.user)
    return render(request, 'home/my_bookings.html')


# Notify user if the contract is nearing expiration
@login_required
def check_expiry_notifications(request):
    today = timezone.now().date()
    # Get all bookings where contract is active and check if it expires within 7 days
    bookings = Booking.objects.filter(customer=request.user, is_active=True)

    for booking in bookings:
        expiry_date = booking.end_date
        if expiry_date - today <= timedelta(days=7):  # Notify 7 days before expiry
            # Send notification to the user
            message = f"Your contract for {booking.storage_unit} will expire soon on {expiry_date}. Would you like to renew?"
            Notification.objects.create(user=request.user, message=message)

    return redirect('my_bookings')


@login_required
def renew_contract(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)

    if request.method == 'POST':
        # Renew the booking by extending the end date (e.g., adding one more month)
        new_end_date = booking.end_date + timedelta(days=30)  # Adjust according to your business logic

        # Create a new booking or update the current one
        booking.end_date = new_end_date
        booking.contract_status = 'renewed'
        booking.save()

        # Notify the user
        Notification.objects.create(user=request.user, message=f"Your contract has been renewed until {new_end_date}.")

        messages.success(request, "Your contract has been renewed!")
        return redirect('my_bookings')

    return render(request, 'home/renew_contract.html', {'booking': booking})


@login_required
def terminate_contract(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)

    if request.method == 'POST':
        # Terminate the contract
        booking.is_active = False
        booking.contract_status = 'terminated'
        booking.save()

        # Notify the user
        Notification.objects.create(user=request.user, message="Your contract has been terminated.")

        messages.success(request, "Your contract has been terminated.")
        return redirect('my_bookings')

    return render(request, 'home/terminate_contract.html', {'booking': booking})


def send_contract_notification(user, subject, message):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

# GOOD: inside a view
@login_required
def notify_user_about_contract(request):
    send_contract_notification(
        user=request.user,   # now request exists
        subject="Contract Notification",
        template_name='emails/contract_notification.html',
        context={
            'user': request.user,
            'message': 'Your contract will expire soon. Please renew it!',
            'action_link': 'https://yourdomain.com/renew/',
            'current_year': timezone.now().year
        }
    )
    return HttpResponse("Notification sent!")

    send_contract_notification(
        user=request.user,
        subject="Contract Renewal Successful",
        message="Dear {},\n\nYour contract has been successfully renewed. Thank you for staying with us!\n\nRegards,\nCompany Team".format(request.user.username)
)
    send_contract_notification(
    user=request.user,
    subject="Contract Termination Confirmed",
    message="Dear {},\n\nYour contract has been terminated as requested. We're sorry to see you go.\n\nBest,\nCompany Team".format(request.user.username)
)

