from rest_framework import serializers
from .models import User
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Required for OWNER role"
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Required for OWNER role"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role', 'first_name', 'last_name')
        extra_kwargs = {
            'role': {'required': False}
        }

    def validate(self, attrs):
        """Validasi bahwa OWNER harus memiliki first_name dan last_name"""
        role = attrs.get('role', User.Role.BUYER)
        first_name = attrs.get('first_name', '')
        last_name = attrs.get('last_name', '')

        if role == User.Role.OWNER:
            if not first_name or not last_name:
                raise serializers.ValidationError({
                    'first_name': 'First name is required for OWNER role.',
                    'last_name': 'Last name is required for OWNER role.'
                })

        return attrs

    def create(self, validated_data):
        role = validated_data.get('role', User.Role.BUYER)

        # Prepare user data
        user_data = {
            'username': validated_data['username'],
            'email': validated_data['email'],
            'role': role
        }

        # Tambahkan first_name dan last_name hanya untuk OWNER
        if role == User.Role.OWNER:
            user_data['first_name'] = validated_data.get('first_name', '')
            user_data['last_name'] = validated_data.get('last_name', '')

        # Extract password untuk dihandle terpisah
        password = validated_data['password']

        # Create user dengan password terpisah
        user = User.objects.create_user(password=password, **user_data)
        return user

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role')