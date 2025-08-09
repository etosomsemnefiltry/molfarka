from django.db import models
from slugify import slugify
from django.utils import timezone

class TarotDeck(models.Model):
    name = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100, blank=True, default='')
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    max_cards = models.PositiveIntegerField(default=3)

    def display_name(self, lang: str = 'uk') -> str:
        if lang == 'ru' and self.name_ru:
            return self.name_ru
        return self.name

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
        return self.display_name('uk')

class PredictionLog(models.Model):
    question = models.TextField()
    deck = models.CharField(max_length=100)
    cards = models.JSONField(default=list)
    ip = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M')} — {self.deck}"
    
class SampleQuestion(models.Model):
    text_uk = models.CharField(max_length=255, db_index=True)
    text_ru = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=50, blank=True, default='')  # love/work/money/health/etc
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.text_uk