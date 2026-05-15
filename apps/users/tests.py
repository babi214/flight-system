from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserProfile

User = get_user_model()


class UserModelTest(TestCase):
    """Test User Model"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('TestPass123!'))
        self.assertTrue(user.is_active)
    
    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
    
    def test_user_str_method(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), f"{user.get_full_name} - {user.email}")
    
    def test_loyalty_points_update(self):
        user = User.objects.create_user(**self.user_data)
        user.add_loyalty_points(100)
        self.assertEqual(user.loyalty_points, 100)
        
        user.add_loyalty_points(1900)
        self.assertEqual(user.loyalty_tier, 'SILVER')
        
        user.add_loyalty_points(3000)
        self.assertEqual(user.loyalty_tier, 'GOLD')


class UserAPITest(TestCase):
    """Test User API Endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        
        self.user_data = {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'JohnPass123!',
            'password2': 'JohnPass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890'
        }
    
    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='john_doe').exists())
    
    def test_user_login(self):
        # Create user first
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Test login
        login_data = {
            'username': 'john_doe',
            'password': 'JohnPass123!'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_invalid_login(self):
        login_data = {
            'username': 'wronguser',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_user_profile_authenticated(self):
        # Register user
        register_response = self.client.post(self.register_url, self.user_data, format='json')
        access_token = register_response.data['access']
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Get profile
        response = self.client.get('/api/users/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'john@example.com')