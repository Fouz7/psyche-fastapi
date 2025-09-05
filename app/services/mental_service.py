from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

import numpy as np

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.health_test import HealthTest
from app.schemas.mental import PredictRequest, MENTAL_HEALTH_FIELDS
from app.core.config import USE_GEMINI_SUGGESTION, GEMINI_API_KEY, GEMINI_MODEL

# Lazy-loaded ML model
action_model = None
model_load_error: Optional[Exception] = None
logger = logging.getLogger(__name__)


def _load_model_once():
    global action_model, model_load_error
    if action_model is not None or model_load_error is not None:
        return
    try:
        # Try TensorFlow first
        try:
            from tensorflow.keras.models import load_model  # type: ignore
        except Exception:
            load_model = None  # type: ignore
        model_path = Path("psyche_model.keras")
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if load_model is not None:
            action_model = load_model(model_path)
            return
        # Fallback to keras v3 loader
        try:
            from keras.models import load_model as load_model_k3  # type: ignore
            action_model = load_model_k3(model_path)
            return
        except Exception as e2:
            raise e2
    except Exception as e:
        model_load_error = e


def _predict_depression_state(scores: List[float]) -> int:
    _load_model_once()
    if model_load_error is not None:
        raise RuntimeError(f"Model not available: {model_load_error}")
    if action_model is None:
        raise RuntimeError("Model failed to load")

    x = np.array([scores], dtype=float)
    y = action_model.predict(x, verbose=0)

    arr = np.array(y)
    if arr.ndim >= 2 and arr.shape[-1] in (4,):
        idx = int(np.argmax(arr.reshape(-1, arr.shape[-1])[0]))
        return max(0, min(3, idx))
    val = float(arr.reshape(-1)[0])
    cls = int(round(val))
    return max(0, min(3, cls))


def _build_specific_score_details(scores: List[int], language: str) -> str:
    notable = [(name, int(val)) for name, val in zip(MENTAL_HEALTH_FIELDS, scores) if int(val) >= 5]
    if not notable:
        return ""
    notable.sort(key=lambda x: x[1], reverse=True)
    pairs = ", ".join([f"{k}={v}" for k, v in notable[:4]])
    if language == 'id':
        return f" (kekhawatiran spesifik: {pairs})"
    return f" (specific concerns: {pairs})"


def _suggestion_with_gemini(state: int, language: str, scores: List[int]) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")
    try:
        import google.generativeai as genai
    except Exception as e:
        raise RuntimeError("google-generativeai package is not installed. Install requirements and restart the server.") from e
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    specific = _build_specific_score_details(scores, language)

    if language == 'id':
        if state == 0:
            promptBase = (
                f"Hasil asesmen kesehatan mental pengguna menunjukkan tidak ada gejala depresi yang signifikan.{specific} "
                "Berikan saran singkat (1-2 kalimat) yang memberi semangat dan suportif untuk menjaga kesehatan mental yang baik. "
                "Jika ada kekhawatiran kecil spesifik yang disebutkan, akui secara halus jika sesuai sambil mempertahankan nada positif."
            )
        elif state == 1:
            promptBase = (
                f"Hasil asesmen kesehatan mental pengguna menunjukkan gejala depresi ringan.{specific} "
                "Berikan saran singkat (1-2 kalimat) yang suportif, fokus pada perawatan diri, pemantauan suasana hati, dan mengatasi kekhawatiran spesifik yang disebutkan."
            )
        elif state == 2:
            promptBase = (
                f"Hasil asesmen kesehatan mental pengguna menunjukkan gejala depresi sedang.{specific} "
                "Berikan saran singkat (2-3 kalimat) yang suportif, mendorong mereka untuk mempertimbangkan berbicara dengan profesional kesehatan mental, terutama menyoroti pentingnya mengatasi kekhawatiran spesifik yang disebutkan."
            )
        elif state == 3:
            promptBase = (
                f"Hasil asesmen kesehatan mental pengguna menunjukkan gejala depresi berat.{specific} "
                "Berikan saran singkat (2-3 kalimat) yang suportif dan empatik, sangat merekomendasikan mereka untuk segera mencari bantuan profesional. "
                "Tekankan keseriusan setiap kekhawatiran spesifik yang disebutkan seperti ide bunuh diri."
            )
        else:
            promptBase = f"Berikan tips kesehatan mental umum (1-2 kalimat).{specific}"
        fullPrompt = (
            f"{promptBase} Pastikan saran tersebut empatik dan dapat ditindaklanjuti. Berikan jawaban dalam Bahasa Indonesia."
        )
    else:
        if state == 0:
            promptBase = (
                f"A user's mental health assessment indicates no significant depressive symptoms.{specific} "
                "Provide a brief, encouraging, and supportive suggestion (1-2 sentences) for maintaining good mental well-being. "
                "If there were specific minor concerns mentioned, subtly acknowledge them if appropriate while maintaining a positive tone."
            )
        elif state == 1:
            promptBase = (
                f"A user's mental health assessment indicates mild depressive symptoms.{specific} "
                "Provide a brief, supportive suggestion (1-2 sentences) focusing on self-care, monitoring mood, and addressing any specifically mentioned concerns."
            )
        elif state == 2:
            promptBase = (
                f"A user's mental health assessment indicates moderate depressive symptoms.{specific} "
                "Provide a brief, supportive suggestion (2-3 sentences) encouraging them to consider talking to a mental health professional, especially highlighting the importance of addressing the specifically mentioned concerns."
            )
        elif state == 3:
            promptBase = (
                f"A user's mental health assessment indicates severe depressive symptoms.{specific} "
                "Provide a brief, supportive, and empathetic suggestion (2-3 sentences) strongly recommending they seek professional help immediately. "
                "Emphasize the seriousness of any specifically mentioned concerns like suicidal ideation."
            )
        else:
            promptBase = f"Provide a general mental wellness tip (1-2 sentences).{specific}"
        fullPrompt = promptBase

    resp = model.generate_content(fullPrompt)
    text = (resp.text or "").strip() if hasattr(resp, "text") else ""
    if not text:
        raise RuntimeError("Empty response from Gemini")
    return text[:500]


def _suggestion_for_state(state: int, language: str) -> str:
    if language == 'id':
        mapping = {
            0: "Respons Anda menunjukkan tidak ada gejala depresi yang signifikan. Pertahankan kebiasaan sehat dan dukungan sosial.",
            1: "Gejala ringan terdeteksi. Coba rutinitas perawatan diri, tidur cukup, dan pantau suasana hati Anda.",
            2: "Gejala sedang terdeteksi. Pertimbangkan untuk berkonsultasi dengan profesional kesehatan mental.",
            3: "Gejala berat terdeteksi. Sangat disarankan untuk segera mencari bantuan profesional atau layanan darurat jika diperlukan.",
        }
    else:
        mapping = {
            0: "No significant depressive symptoms detected. Keep up healthy routines and social support.",
            1: "Mild symptoms detected. Try self-care routines, good sleep, and monitor your mood.",
            2: "Moderate symptoms detected. Consider speaking with a mental health professional.",
            3: "Severe symptoms detected. Please seek professional help promptly or emergency services if needed.",
        }
    return mapping.get(state, mapping[0])


def predict_and_save(db: Session, payload: PredictRequest) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == payload.userId).first()
    if not user:
        raise ValueError("Invalid userId. User does not exist.")

    scores = [int(getattr(payload, f)) for f in MENTAL_HEALTH_FIELDS]

    depression_state = _predict_depression_state(scores)

    suggestion: str
    if USE_GEMINI_SUGGESTION and GEMINI_API_KEY:
        try:
            logger.info("Using Gemini for suggestion (model=%s)", GEMINI_MODEL)
            suggestion = _suggestion_with_gemini(depression_state, payload.language, scores)
        except Exception:
            logger.warning("Gemini suggestion failed; falling back to local suggestion", exc_info=True)
            suggestion = _suggestion_for_state(depression_state, payload.language)
    else:
        logger.info("Gemini disabled or API key missing; using local suggestion mapping")
        suggestion = _suggestion_for_state(depression_state, payload.language)

    # Persist record
    rec = HealthTest(
        userId=payload.userId,
        language=payload.language,
        depressionState=depression_state,
        generatedSuggestion=suggestion,
        **{f: int(getattr(payload, f)) for f in MENTAL_HEALTH_FIELDS},
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "message": "Depression state predicted and recorded successfully.",
        "depressionState": depression_state,
        "suggestion": suggestion,
        "data": {
            "id": rec.id,
            "userId": rec.userId,
            **{f: getattr(rec, f) for f in MENTAL_HEALTH_FIELDS},
            "depressionState": rec.depressionState,
            "generatedSuggestion": rec.generatedSuggestion,
            "language": rec.language,
            "healthTestDate": rec.healthTestDate.isoformat() if rec.healthTestDate else None,
        },
    }


def history_by_user(db: Session, user_id: int) -> List[Dict[str, Any]]:
    if not db.query(User.id).filter(User.id == user_id).first():
        raise LookupError("User not found.")

    rows = (
        db.query(HealthTest)
        .filter(HealthTest.userId == user_id)
        .order_by(desc(HealthTest.healthTestDate))
        .all()
    )
    return [
        {
            "id": r.id,
            "userId": r.userId,
            **{f: getattr(r, f) for f in MENTAL_HEALTH_FIELDS},
            "depressionState": r.depressionState,
            "generatedSuggestion": r.generatedSuggestion,
            "language": r.language,
            "healthTestDate": r.healthTestDate.isoformat() if r.healthTestDate else None,
        }
        for r in rows
    ]


def latest_history_by_user(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    if not db.query(User.id).filter(User.id == user_id).first():
        raise LookupError("User not found.")

    r = (
        db.query(HealthTest)
        .filter(HealthTest.userId == user_id)
        .order_by(desc(HealthTest.healthTestDate))
        .first()
    )
    if not r:
        return None
    return {
        "id": r.id,
        "userId": r.userId,
        **{f: getattr(r, f) for f in MENTAL_HEALTH_FIELDS},
        "depressionState": r.depressionState,
        "generatedSuggestion": r.generatedSuggestion,
        "language": r.language,
        "healthTestDate": r.healthTestDate.isoformat() if r.healthTestDate else None,
    }
