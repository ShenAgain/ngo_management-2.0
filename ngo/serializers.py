from rest_framework import serializers
from .models import NGO, Activity
from accounts.models import CustomUser


class NGOSerializer(serializers.ModelSerializer):
    class Meta:
        model = NGO
        fields = ('id', 'name', 'contact_email', 'website', 'description', 'created_at')


class ActivitySerializer(serializers.ModelSerializer):
    ngo_name = serializers.CharField(source='ngo.name', read_only=True)
    registered_count = serializers.IntegerField(source='get_registered_count', read_only=True)
    slots_remaining = serializers.IntegerField(read_only=True)
    created_by = serializers.SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        model = Activity
        fields = (
            'id', 'title', 'description', 'location', 'date', 'cut_off_datetime', 'max_slots',
            'ngo', 'ngo_name', 'registered_count', 'slots_remaining', 'created_by', 'created_at',
        )
        read_only_fields = ('created_by', 'created_at', 'ngo_name', 'registered_count', 'slots_remaining')
