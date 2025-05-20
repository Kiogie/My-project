from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings


class CustomUser(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text=('The groups this user belongs to.'),
        verbose_name=('groups'),
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        help_text=('Specific permissions for this user.'),
        verbose_name=('user permissions'),
    )

class StorageUnit(models.Model):
    UNIT_SIZES = [
        ('Small', 'Small'),
        ('Medium', 'Medium'),
        ('Large', 'Large'),
    ]
    size = models.CharField(max_length=20, choices=UNIT_SIZES)
    description = models.TextField()
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)
    total_units = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='storage_images/')

    def __str__(self):
        return f"{self.size} - Ksh {self.price_per_month}"
    
    def decrement_available_units(self):
        """Decrements the available units by 1."""
        if self.total_units > 0:
            self.total_units -= 1
            self.save()

    def increment_available_units(self):
        """Increments the available units by 1."""
        if self.total_units < self.total_units:
            self.total_units += 1
            self.save()

class Booking(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'is_customer': True})
    storage_unit = models.ForeignKey(StorageUnit, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contract_status = models.CharField(max_length=20, choices=[('active', 'Active'), ('terminated', 'Terminated'), ('renewed', 'Renewed')], default='active')


    def save(self, *args, **kwargs):
        # Calculate total price
        months = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
        if months == 0:
            months = 1
        self.total_price = months * self.storage_unit.price_per_month
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking by {self.customer.username} for {self.storage_unit}"

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_successful = models.BooleanField(default=False)
    transaction_reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Payment of {self.amount} for {self.booking}"

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}"

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=1)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.rating} Stars"
