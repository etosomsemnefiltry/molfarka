from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TarotDeck, PredictionLog, SampleQuestion
from django.utils.timezone import now, timedelta
from django.core import signing


import os
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
import json
import requests


load_dotenv()
client = OpenAI()  # автоматом использует OPENAI_API_KEY из окружения

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YT_API_KEY = os.getenv("YT_API_KEY", "").strip()

def index(request):
    decks = TarotDeck.objects.all()
    questions = SampleQuestion.objects.filter(is_active=True).order_by('sort_order', 'id')
    lang = 'uk'
    questions_data = [
        {'id': q.id, 'text': q.text_ru if lang == 'ru' else q.text_uk}
        for q in questions
    ]
    return render(request, 'index.html', {'decks': decks, 'base_questions': questions_data})

@csrf_exempt
def predict(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        deck_slug = data.get('deck', '').strip()
        cards = str(data.get('cards', [])).strip()
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Проверка лимита: 5 предсказань за 24 часа
        cutoff = now() - timedelta(days=1)
        recent_count = PredictionLog.objects.filter(ip=ip, created_at__gte=cutoff).count()
        if recent_count >= 5:
            return JsonResponse({'error': "⛔️ Ліміт передбачень на сьогодні вичерпано (5 за 24 години)."}, status=429)

        if not question or not cards or not deck_slug:
            return JsonResponse({"error": "Питання, колода або карти відсутні."}, status=400)

        try:
            deck = TarotDeck.objects.get(slug=deck_slug)
        except TarotDeck.DoesNotExist:
            return JsonResponse({"error": "Колода не знайдена."}, status=404)
        
        PredictionLog.objects.create(
            question=question,
            deck=deck.name,
            cards=cards,
            ip=ip,
            user_agent=user_agent
        )

        prompt = f"""
Ти ворожка Таро, яка говорить з глибини інтуїції. Відповідай з емпатією та натяками. Не вигадуй назви карт.
Не описуй карти по одній. Тільки їх взаємопоєднання. Намагайся, щоб було не дуже багато тексту.
Якщо карти показують смерть, втрату, замкнутість чи біль — не маскуй їх. Це може бути знак глибокої тривоги.
Не давай фальшивих надій. Враховуй, що люди питають с України.
Загальний висновой опиши більш докладно.
Враховуй особливості обранної колоди.
Колода: {deck.name}
Карти випали: {', '.join(cards)}
Запитання: "{question}"
""".strip()

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content.strip()
            return JsonResponse({'result': result})
        except Exception as e:
            return JsonResponse({'error': f"⚠️ Помилка: {str(e)}"}, status=500)

    return JsonResponse({"error": "Метод не підтримується"}, status=405)

@csrf_exempt
def draw_cards(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            deck_slug = data.get('deck')
            count = int(data.get('count', 3))

            if not deck_slug:
                return JsonResponse({"error": "Не вказана колода."}, status=400)
            if count < 1 or count > 10:
                return JsonResponse({"error": "Неприпустима кількість карт. Максимум — 10."}, status=400)

            deck = TarotDeck.objects.get(slug=deck_slug)

            prompt = f"""
Обери випадково {count} карт з колоди таро "{deck.name}". ОБОВ'ЯЗКОВО вибирай тільки з реальних карт Таро. Не вигадуй нових назв!
Напиши тільки їхні назви у форматі списку без нумерації, без описів. Українською мовою.
""".strip()

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            raw_output = response.choices[0].message.content.strip()

            cards = [line.strip("–-•*•1234567890. ").strip() for line in raw_output.split('\n') if line.strip()]

            return JsonResponse({"cards": cards})

        except TarotDeck.DoesNotExist:
            return JsonResponse({"error": "Колода не знайдена."}, status=404)
        except Exception as e:
            return JsonResponse({"error": f"⚠️ Помилка: {str(e)}"}, status=500)

    return JsonResponse({"error": "Метод не підтримується"}, status=405)

@csrf_exempt
def video_prediction(request):
    if request.method == 'POST':
        question = (request.POST.get('question') or '').strip()
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        if not question:
            return JsonResponse({'error': 'А де запитання?'}, status=400)

        cutoff = now() - timedelta(days=1)
        recent_count = PredictionLog.objects.filter(ip=ip, created_at__gte=cutoff).count()
        if recent_count >= 50:
            return JsonResponse({'error': "⛔️ Ліміт передбачень на сьогодні вичерпано (5 за 24 години)."}, status=429)

        # логируем как "video"
        PredictionLog.objects.create(
            question=question,
            deck='video',
            cards=[],  # JSONField: пустой масив
            ip=ip,
            user_agent=user_agent
        )

        if not YT_API_KEY:
            return JsonResponse({'error': 'YouTube API ключ не налаштовано (YT_API_KEY).'}, status=500)

        # чуть расширим запрос, чтобы точнее подбирать видео
        query = f"{question} таро"
        try:
            video_url = yt_embed_url_by_query(query)
        except requests.RequestException:
            return JsonResponse({'error': 'Сервіс недоступний'}, status=502)

        if not video_url:
            return JsonResponse({'error': 'Відео не знайдено'}, status=404)

        # На фронт отдаем ГОДНУЮ ссылку (embed); при необходимости можно сменить на watch
        return JsonResponse({'video_url': video_url})

    return JsonResponse({"error": "Метод не підтримується"}, status=405)

def yt_embed_url_by_query(query: str) -> str | None:
    params = {
        'key': YT_API_KEY,
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': 1,
        'videoEmbeddable': 'true',
        'relevanceLanguage': 'uk',
        'regionCode': 'UA',
        'safeSearch': 'none',
        'order': 'relevance',
    }
    r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=8)
    r.raise_for_status()
    data = r.json()
    items = data.get('items', [])
    if not items:
        return None
    vid = items[0]['id']['videoId']
    return f'https://www.youtube.com/embed/{vid}?rel=0&modestbranding=1&playsinline=1&controls=0&showinfo=0&disablekb=1&iv_load_policy=3'