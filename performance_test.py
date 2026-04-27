#!/usr/bin/env python
"""
Topic 9: Caching Performance Test Script
Tests performance improvement with Redis caching vs database queries.

Usage:
    python performance_test.py

Requirements:
    - PostgreSQL database configured
    - Redis server running (optional - falls back to local memory)
    - Test data created
"""

import os
import sys
import time
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ngo_management.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory
from accounts.models import CustomUser
from ngo.models import NGO, Activity
from ngo.api import NGOViewSet, ActivityViewSet
from registration.models import Registration
from django.core.cache import cache


def create_test_data():
    """Create test data for performance testing"""
    print("🔧 Creating test data...")

    # Create admin user
    admin, created = CustomUser.objects.get_or_create(
        username='test_admin',
        defaults={
            'email': 'admin@test.com',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin.set_password('testpass123')
        admin.save()

    # Create employee user
    employee, created = CustomUser.objects.get_or_create(
        username='test_employee',
        defaults={
            'email': 'employee@test.com',
            'role': 'employee'
        }
    )
    if created:
        employee.set_password('testpass123')
        employee.save()

    # Create NGOs
    ngos = []
    for i in range(50):  # Create 50 NGOs for testing
        ngo, created = NGO.objects.get_or_create(
            name=f'Test NGO {i}',
            defaults={
                'description': f'Description for NGO {i}',
                'contact_email': f'contact{i}@ngo.com',
                'website': f'https://ngo{i}.com'
            }
        )
        ngos.append(ngo)

    # Create Activities
    activities = []
    for i in range(100):  # Create 100 activities
        activity, created = Activity.objects.get_or_create(
            title=f'Test Activity {i}',
            ngo=ngos[i % len(ngos)],
            defaults={
                'description': f'Description for activity {i}',
                'date': '2024-12-31T10:00:00Z',
                'cut_off_datetime': '2024-12-30T10:00:00Z',
                'location': f'Location {i}',
                'max_slots': 20,
                'created_by': admin
            }
        )
        activities.append(activity)

    # Create registrations
    for i in range(200):  # Create 200 registrations
        Registration.objects.get_or_create(
            employee=employee,
            activity=activities[i % len(activities)],
            defaults={'status': 'active'}
        )

    print(f"✅ Created {len(ngos)} NGOs, {len(activities)} activities, 200 registrations")


def clear_cache():
    """Clear all cache"""
    cache.clear()
    print("🧹 Cache cleared")


def test_ngo_listing_performance(iterations=10):
    """Test NGO listing API performance with and without cache"""
    print(f"\n📊 Testing NGO Listing Performance ({iterations} iterations)")

    factory = APIRequestFactory()
    view = NGOViewSet()
    admin_user = CustomUser.objects.get(username='test_admin')

    # Test WITHOUT cache (simulate cold cache)
    clear_cache()
    times_without_cache = []

    for i in range(iterations):
        request = factory.get('/api/v1/ngos/')
        request.user = admin_user
        view.request = request  # Set request on view
        start_time = time.time()
        response = view.list(request)
        end_time = time.time()
        times_without_cache.append(end_time - start_time)
        print(".2f")

    # Test WITH cache (simulate warm cache)
    times_with_cache = []

    for i in range(iterations):
        request = factory.get('/api/v1/ngos/')
        request.user = admin_user
        view.request = request  # Set request on view
        start_time = time.time()
        response = view.list(request)
        end_time = time.time()
        times_with_cache.append(end_time - start_time)
        print(".2f")

    # Calculate averages
    avg_without = sum(times_without_cache) / len(times_without_cache)
    avg_with = sum(times_with_cache) / len(times_with_cache)
    improvement = ((avg_without - avg_with) / avg_without) * 100

    print("\n📈 NGO Listing Results:")
    print(f"Average without cache: {avg_without:.4f}s")
    print(f"Average with cache: {avg_with:.4f}s")
    print(f"Performance improvement: {improvement:.1f}%")
    return avg_without, avg_with, improvement


def test_activity_participants_performance(iterations=10):
    """Test activity participants API performance with and without cache"""
    print(f"\n📊 Testing Activity Participants Performance ({iterations} iterations)")

    factory = APIRequestFactory()
    view = ActivityViewSet()
    admin_user = CustomUser.objects.get(username='test_admin')
    activity = Activity.objects.first()  # Get first activity

    # Test WITHOUT cache
    clear_cache()
    times_without_cache = []

    for i in range(iterations):
        request = factory.get(f'/api/v1/activities/{activity.id}/participants/')
        request.user = admin_user
        view.request = request
        start_time = time.time()
        response = view.participants(request, pk=activity.id)
        end_time = time.time()
        times_without_cache.append(end_time - start_time)
        print(".2f")

    # Test WITH cache
    times_with_cache = []

    for i in range(iterations):
        request = factory.get(f'/api/v1/activities/{activity.id}/participants/')
        request.user = admin_user
        view.request = request
        start_time = time.time()
        response = view.participants(request, pk=activity.id)
        end_time = time.time()
        times_with_cache.append(end_time - start_time)
        print(".2f")

    # Calculate averages
    avg_without = sum(times_without_cache) / len(times_without_cache)
    avg_with = sum(times_with_cache) / len(times_with_cache)
    improvement = ((avg_without - avg_with) / avg_without) * 100

    print("\n📈 Activity Participants Results:")
    print(f"Average without cache: {avg_without:.4f}s")
    print(f"Average with cache: {avg_with:.4f}s")
    print(f"Performance improvement: {improvement:.1f}%")
    return avg_without, avg_with, improvement


def test_cache_invalidation():
    """Test that cache invalidation works when data changes"""
    print("\n🔄 Testing Cache Invalidation")

    factory = APIRequestFactory()
    view = NGOViewSet()
    admin_user = CustomUser.objects.get(username='test_admin')

    # Get initial cached response
    request = factory.get('/api/v1/ngos/')
    request.user = admin_user
    response1 = view.list(request)
    initial_count = len(response1.data)

    # Create new NGO (should invalidate cache)
    new_ngo = NGO.objects.create(
        name='Cache Test NGO',
        description='Testing cache invalidation',
        contact_email='cache@test.com',
        contact_phone='+60123456789',
        address='Cache Test Address',
        created_by=admin_user
    )

    # Get response again (should show new NGO)
    response2 = view.list(request)
    final_count = len(response2.data)

    if final_count > initial_count:
        print("✅ Cache invalidation working - new NGO appears")
        return True
    else:
        print("❌ Cache invalidation failed - new NGO not showing")
        return False


def main():
    """Main performance test function"""
    print("🚀 Starting Topic 9: Caching Performance Tests")
    print("=" * 60)

    # Check cache backend
    cache_backend = settings.CACHES['default']['BACKEND']
    if 'redis' in cache_backend.lower():
        print("✅ Using Redis cache backend")
    else:
        print("⚠️  Using local memory cache (Redis not configured)")

    # Create test data
    create_test_data()

    # Run performance tests
    ngo_results = test_ngo_listing_performance()
    participants_results = test_activity_participants_performance()

    # Test cache invalidation
    invalidation_works = test_cache_invalidation()

    # Summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("=" * 60)

    print("NGO Listing Performance:")
    print(f"  Improvement: {ngo_results[2]:.1f}%")
    print("Activity Participants Performance:")
    print(f"  Improvement: {participants_results[2]:.1f}%")
    print(f"Cache Invalidation: {'✅ Working' if invalidation_works else '❌ Failed'}")

    total_improvement = (ngo_results[2] + participants_results[2]) / 2
    print(f"Average Performance Improvement: {total_improvement:.1f}%")

    if total_improvement > 50:
        print("🎉 Excellent caching performance!")
    elif total_improvement > 20:
        print("👍 Good caching performance!")
    else:
        print("⚠️  Caching performance could be improved")

    print("\n✅ Performance tests completed!")


if __name__ == '__main__':
    main()