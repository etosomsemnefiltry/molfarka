from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TarotDeck


import os
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI


load_dotenv()
client = OpenAI()  # автоматом использует OPENAI_API_KEY из окружения

def index(request):
    decks = TarotDeck.objects.all()
    return render(request, 'index.html', {'decks': decks})

@csrf_exempt
def predict(request):
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        deck_slug = request.POST.get('deck', '').strip()
        count = request.POST.get('count', '3').strip()

        if not question or not deck_slug:
            return JsonResponse({"error": "Питання або колода відсутні."}, status=400)

        try:
            deck = TarotDeck.objects.get(slug=deck_slug)
        except TarotDeck.DoesNotExist:
            return JsonResponse({"error": "Колода не знайдена."}, status=404)

        prompt = f"""
Ти — Мольфарка, старовинна українська провидиця. Ти відповідаєш на питання користувача через розклад Таро.

Користувач питає: "{question}"

Колода: {deck.name}
Кількість карт: {count}

Зроби розклад: опиши кожну карту коротко, поясни їх значення в контексті питання, і дай метафоричну пораду або передбачення.
""".strip()

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content.strip()
            return JsonResponse({'result': result})
        except Exception as e:
            return JsonResponse({'error': f"⚠️ Помилка: {str(e)}"}, status=500)

    return JsonResponse({"error": "Метод не підтримується"}, status=405)
