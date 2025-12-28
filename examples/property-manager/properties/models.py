# properties/models.py
from django.db import models


from django.utils import timezone

class Property(models.Model):
    """A property that can have multiple tenants."""
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Tenant(models.Model):
    """A tenant associated with a property."""
    property = models.ForeignKey(Property, related_name="tenants", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    document = models.FileField(upload_to='tenant_documents/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']
        constraints = [
            models.UniqueConstraint(
                fields=['property', 'email'],
                name='unique_tenant_per_property'
            )
        ]

    def __str__(self):
        return f"{self.full_name} ({self.property.name})"