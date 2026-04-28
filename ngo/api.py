from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from .models import NGO, Activity
from .serializers import NGOSerializer, ActivitySerializer
from accounts.api_permissions import IsAdminOrReadOnly, IsAdmin


class NGOViewSet(viewsets.ModelViewSet):
    queryset = NGO.objects.all()
    serializer_class = NGOSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def list(self, request, *args, **kwargs):
        """
        Topic 9.2: Cache NGO listing for performance.
        Cache key includes query params + a cache version that is bumped on writes.
        """
        version = cache.get('api:v1:ngos:version', 1)
        cache_key = f"api:v1:ngos:list:v{version}:{request.get_full_path()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        resp = super().list(request, *args, **kwargs)
        cache.set(cache_key, resp.data, timeout=60)
        return resp

    def _bump_cache_version(self):
        try:
            cache.incr('api:v1:ngos:version')
        except ValueError:
            cache.set('api:v1:ngos:version', 2, timeout=None)

    def perform_create(self, serializer):
        obj = serializer.save()
        self._bump_cache_version()
        return obj

    def perform_update(self, serializer):
        obj = serializer.save()
        self._bump_cache_version()
        return obj

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        self._bump_cache_version()


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.select_related('ngo').all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'location', 'ngo']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_permissions(self):
        # Anyone authenticated can read activities; only admins can see participants list.
        return super().get_permissions()

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def participants(self, request, pk=None):
        """
        Topic 9.2: Cache participants listing.
        GET /api/v1/activities/<id>/participants/
        """
        activity = self.get_object()
        version_key = f"api:v1:activity:{activity.id}:participants:version"
        version = cache.get(version_key, 1)
        cache_key = f"api:v1:activity:{activity.id}:participants:v{version}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        from registration.models import Registration
        regs = (
            Registration.objects
            .filter(activity=activity, status='active')
            .select_related('employee')
            .order_by('-registered_at')
        )
        data = [
            {
                'registration_id': r.id,
                'employee_username': r.employee.username,
                'employee_id': r.employee.id,
                'registered_at': r.registered_at,
                'status': r.status,
            }
            for r in regs
        ]
        payload = {'activity_id': activity.id, 'count': len(data), 'results': data}
        resp = Response(payload)
        cache.set(cache_key, payload, timeout=60)
        return resp

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def availability(self, request, pk=None):
        """
        Topic 11: NGO service endpoint the gateway can call to check slot availability.
        GET /api/v1/activities/<id>/availability/
        """
        activity = self.get_object()
        from registration.models import Registration

        active_count = Registration.objects.filter(activity=activity, status="active").count()
        remaining = max(int(activity.max_slots) - int(active_count), 0)
        return Response(
            {
                "activity_id": activity.id,
                "max_slots": activity.max_slots,
                "active_registrations": active_count,
                "remaining_slots": remaining,
                "available": remaining > 0,
            }
        )
