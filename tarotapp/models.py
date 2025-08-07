from django.db import models
from slugify import slugify
from django.utils import timezone

class TarotDeck(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    max_cards = models.PositiveIntegerField(default=3)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name or '')
            slug = base_slug
            n = 1
            while slug == '' or TarotDeck.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name

class PredictionLog(models.Model):
    question = models.TextField()
    deck = models.CharField(max_length=100)
    cards = models.JSONField()
    ip = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M')} — {self.deck}"