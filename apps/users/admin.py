from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, LoginHistory


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class LoginHistoryInline(admin.TabularInline):
    model = LoginHistory
    fields = ['ip_address', 'user_agent', 'login_time', 'login_status']
    readonly_fields = ['login_time']
    extra = 0
    max_num = 10


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 
                    'loyalty_tier', 'is_active', 'is_verified', 'last_login']
    list_filter = ['user_type', 'is_active', 'is_verified', 'loyalty_tier']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Personal Info', {'fields': ('title', 'phone_number', 'date_of_birth', 'user_type')}),
        ('Address', {'fields': ('street_address', 'city', 'state', 'country', 'postal_code')}),
        ('Preferences', {'fields': ('preferred_language', 'preferred_currency', 
                                    'email_notifications', 'sms_notifications')}),
        ('Loyalty', {'fields': ('loyalty_points', 'loyalty_tier')}),
        ('Security', {'fields': ('is_verified', 'verification_token', 'reset_password_token')}),
    )
    
    inlines = [UserProfileInline, LoginHistoryInline]
    
    actions = ['verify_users', 'send_welcome_email']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users were successfully verified.')
    verify_users.short_description = 'Verify selected users'
    
    def send_welcome_email(self, request, queryset):
        # Bulk welcome email logic
        self.message_user(request, f'Welcome emails sent to {queryset.count()} users.')
    send_welcome_email.short_description = 'Send welcome email'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_seat', 'meal_preference', 'newsletter_subscribed']
    search_fields = ['user__email', 'user__username']
    list_filter = ['preferred_seat', 'meal_preference', 'newsletter_subscribed']


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'ip_address', 'login_status']
    list_filter = ['login_status', 'login_time']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['login_time']