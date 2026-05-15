from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended User model with additional fields"""
    
    # User Types
    class UserType(models.TextChoices):
        PASSENGER = 'PASSENGER', 'Passenger'
        AGENT = 'AGENT', 'Travel Agent'
        ADMIN = 'ADMIN', 'Admin Staff'
    
    # Title choices
    class Title(models.TextChoices):
        MR = 'MR', 'Mr.'
        MS = 'MS', 'Ms.'
        MRS = 'MRS', 'Mrs.'
        DR = 'DR', 'Dr.'
        PROF = 'PROF', 'Prof.'
    
    # Basic Information
    user_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=10, choices=Title.choices, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    user_type = models.CharField(max_length=20, choices=UserType.choices, default=UserType.PASSENGER)
    
    # Address Information
    street_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='USA')
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='en')
    preferred_currency = models.CharField(max_length=3, default='USD')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    
    # Security
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255, blank=True, null=True)
    reset_password_token = models.CharField(max_length=255, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Loyalty Program
    loyalty_points = models.IntegerField(default=0)
    loyalty_tier = models.CharField(max_length=20, default='BRONZE')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['user_type']),
            models.Index(fields=['loyalty_tier']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    @property
    def get_full_name(self):
        """Return the full name of the user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])
    
    def add_loyalty_points(self, points):
        """Add loyalty points and update tier"""
        self.loyalty_points += points
        self.update_loyalty_tier()
        self.save(update_fields=['loyalty_points', 'loyalty_tier'])
    
    def update_loyalty_tier(self):
        """Update loyalty tier based on points"""
        if self.loyalty_points >= 10000:
            self.loyalty_tier = 'PLATINUM'
        elif self.loyalty_points >= 5000:
            self.loyalty_tier = 'GOLD'
        elif self.loyalty_points >= 2000:
            self.loyalty_tier = 'SILVER'
        else:
            self.loyalty_tier = 'BRONZE'


class UserProfile(models.Model):
    """Additional user profile information"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    
    # Travel Preferences
    preferred_airline = models.CharField(max_length=100, blank=True)
    preferred_seat = models.CharField(max_length=10, blank=True, choices=[
        ('WINDOW', 'Window'),
        ('MIDDLE', 'Middle'),
        ('AISLE', 'Aisle'),
    ])
    meal_preference = models.CharField(max_length=50, blank=True, choices=[
        ('REGULAR', 'Regular'),
        ('VEGETARIAN', 'Vegetarian'),
        ('VEGAN', 'Vegan'),
        ('HALAL', 'Halal'),
        ('KOSHER', 'Kosher'),
    ])
    
    # Known Traveler Numbers
    known_traveler_number = models.CharField(max_length=20, blank=True)
    redress_number = models.CharField(max_length=20, blank=True)
    passport_number = models.CharField(max_length=20, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)
    passport_country = models.CharField(max_length=100, blank=True)
    
    # Notifications
    newsletter_subscribed = models.BooleanField(default=False)
    promotional_emails = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class LoginHistory(models.Model):
    """Track user login history"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(default=timezone.now)
    login_status = models.CharField(max_length=20, choices=[
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ])
    
    class Meta:
        db_table = 'login_history'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', 'login_time']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.login_time}"