from django.test import TestCase
from django.core.mail import send_mail
from django.http import HttpResponse

def send_test_email(request):
    send_mail(
        'Test Email Subject',
        'This is a test email body.',
        'your-email@gmail.com',  # From Email
        ['recipient-email@example.com'],  # To Email
        fail_silently=False,
    )
    return HttpResponse("Test email sent.")

# Create your tests here.
