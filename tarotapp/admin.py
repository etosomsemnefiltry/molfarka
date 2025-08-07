from django.contrib import admin
from .models import TarotDeck, PredictionLog

@admin.register(TarotDeck)
class TarotDeckAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'max_cards')

@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'deck', 'ip', 'question_short')
    list_filter = ('deck', 'created_at')
    search_fields = ('question', 'ip', 'user_agent')

    def question_short(self, obj):
        return (obj.question[:50] + '...') if len(obj.question) > 50 else obj.question
    question_short.short_description = "Питання"