from django.contrib import admin
from .models import TarotDeck, PredictionLog, SampleQuestion

@admin.register(TarotDeck)
class TarotDeckAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'name_ru')
    search_fields = ('slug', 'name', 'name_ru')

@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'deck', 'ip', 'question_short')
    list_filter = ('deck', 'created_at')
    search_fields = ('question', 'ip', 'user_agent')

    def question_short(self, obj):
        return (obj.question[:50] + '...') if len(obj.question) > 50 else obj.question
    question_short.short_description = "Питання"

@admin.register(SampleQuestion)
class SampleQuestionAdmin(admin.ModelAdmin):
    list_display = ('text_uk', 'text_ru', 'category', 'is_active', 'sort_order')
    list_filter = ('category', 'is_active')
    search_fields = ('text_uk', 'text_ru')
    ordering = ('sort_order', 'id')