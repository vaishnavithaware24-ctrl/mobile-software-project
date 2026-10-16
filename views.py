import os
import tempfile

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .services.stt_service import transcribe
from .services.tts_service import synthesize
from rag.pipeline import answer


@api_view(["POST"])
@parser_classes([MultiPartParser])
def voice_chat(request):
    audio = request.FILES.get("audio")
    if not audio:
        return Response({"error": "No audio"}, status=400)

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        for chunk in audio.chunks():
            tmp.write(chunk)
        path = tmp.name

    try:
        text = transcribe(path)
    except Exception as e:
        return Response({"error": f"Speech-to-text failed: {e}"}, status=500)
    finally:
        os.remove(path)

    if not text:
        return Response({"error": "Could not understand audio"}, status=400)

    data = {"transcript": text, "answer": "", "error": None}

    try:
        data["answer"] = answer(text)
    except Exception as e:
        data["error"] = f"Answer step failed: {e}"

    return Response(data)


@api_view(["POST"])
def chat(request):
    text = request.data.get("text", "").strip()
    if not text:
        return Response({"error": "No text"}, status=400)

    data = {"transcript": text, "answer": "", "error": None}

    try:
        data["answer"] = answer(text)
    except Exception as e:
        data["error"] = f"Answer step failed: {e}"

    return Response(data)


@api_view(["POST"])
def speak(request):
    text = request.data.get("text", "").strip()
    if not text:
        return Response({"error": "No text"}, status=400)

    try:
        audio_url = synthesize(text)
    except Exception as e:
        return Response({"error": f"Voice reply failed: {e}"}, status=500)

    return Response({"audio_url": request.build_absolute_uri(audio_url)})