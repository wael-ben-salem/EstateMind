"""
Photo → listing pipeline. Framework-agnostic — imported by both `app.py`
(Streamlit dev UI) and `api.py` (FastAPI service).

Public surface:
    load_blip2_model(model_id)           # build a blip dict (caches on first call)
    load_blip_fallback()                 # smaller BLIP-1 fallback
    caption_image_blip2(blip, img)       # image -> English caption
    assemble_description_blip2(captions) # list of captions -> English description
    humanize_and_extract(captions)       # captions -> {description_fr, fields}
    caption_listing(blip, images)        # one-shot end-to-end pipeline
"""
from __future__ import annotations

import io
import json
import os
from typing import Any

import requests
import torch
from PIL import Image


# ─────────────────────────────────────────────────────────────────────────────
# Model loading
# ─────────────────────────────────────────────────────────────────────────────
_MODEL_CACHE: dict[str, dict] = {}


def load_blip2_model(model_id: str = "Salesforce/blip2-flan-t5-xl") -> dict:
    """Load BLIP-2 once per process; subsequent calls return the cached dict."""
    if model_id in _MODEL_CACHE:
        return _MODEL_CACHE[model_id]
    from transformers import Blip2ForConditionalGeneration, Blip2Processor

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float16 if device.type == "cuda" else torch.float32

    processor = Blip2Processor.from_pretrained(model_id)
    if device.type == "cuda":
        model = Blip2ForConditionalGeneration.from_pretrained(
            model_id, torch_dtype=torch.float16, device_map="auto"
        )
    else:
        model = Blip2ForConditionalGeneration.from_pretrained(
            model_id, torch_dtype=torch.float32
        )
    model.eval()
    bundle = {
        "processor": processor,
        "model": model,
        "model_id": model_id,
        "device": device,
        "dtype": dtype,
        "model_family": "blip2",
    }
    _MODEL_CACHE[model_id] = bundle
    return bundle


def load_blip_fallback() -> dict:
    """Smaller BLIP-1 model (~1 GB), used when BLIP-2 fails."""
    cache_key = "blip1-fallback"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    from transformers import BlipForConditionalGeneration, BlipProcessor

    model_id = "Salesforce/blip-image-captioning-large"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float16 if device.type == "cuda" else torch.float32
    processor = BlipProcessor.from_pretrained(model_id)
    model = BlipForConditionalGeneration.from_pretrained(
        model_id, torch_dtype=dtype
    ).to(device)
    model.eval()
    bundle = {
        "processor": processor,
        "model": model,
        "model_id": model_id,
        "device": device,
        "dtype": dtype,
        "model_family": "blip1",
    }
    _MODEL_CACHE[cache_key] = bundle
    return bundle


# ─────────────────────────────────────────────────────────────────────────────
# Captioning
# ─────────────────────────────────────────────────────────────────────────────
_BLIP2_FLAN_QUESTIONS = [
    "Question: What does this photo show? Answer:",
    "Question: What are the main features and materials visible? Answer:",
]
_BLIP2_OPT_PROMPT = "a photo of"

_DEDUP_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "with", "in", "on", "is", "are",
    "was", "were", "this", "that", "has", "have", "to", "for", "from", "by",
    "at", "it", "its", "be", "very", "some", "there", "here",
}


def _content_words(s: str) -> set[str]:
    out = set()
    for w in s.lower().split():
        w = w.strip(".,;:!?\"'()[]")
        if len(w) > 1 and w not in _DEDUP_STOPWORDS:
            out.add(w)
    return out


def _filter_overlapping(parts: list[str]) -> list[str]:
    """Drop a sentence when another in the list is a strict superset of it."""
    if len(parts) <= 1:
        return parts
    word_sets = [_content_words(p) for p in parts]
    keep = [True] * len(parts)
    for i in range(len(parts)):
        if not keep[i] or not word_sets[i]:
            continue
        for j in range(len(parts)):
            if i == j or not keep[j]:
                continue
            wi, wj = word_sets[i], word_sets[j]
            if wj and wj <= wi and len(wi) > len(wj):
                keep[j] = False
    return [p for p, k in zip(parts, keep) if k]


def _strip_prompt_echo(text: str, prompt: str) -> str:
    if text.lower().startswith(prompt.lower()):
        return text[len(prompt):].strip(" .,:;-")
    return text


def _dedupe_repeats(text: str) -> str:
    if not text:
        return text
    parts = [p.strip() for p in text.split(".") if p.strip()]
    seen, unique = set(), []
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    text = ". ".join(unique).strip()
    words = text.split()
    n = len(words)
    if n >= 8:
        for chunk in (n // 2, n // 3):
            if chunk >= 4:
                first = " ".join(words[:chunk]).lower().rstrip(".,;:!?")
                second = " ".join(words[chunk:2 * chunk]).lower().rstrip(".,;:!?")
                if first == second:
                    text = " ".join(words[:chunk]).rstrip(".,;:!?")
                    break
    return text.strip()


def _is_prompt_echo(text: str, prompt: str) -> bool:
    if not text:
        return True
    cleaned = text.lower().replace(prompt.lower(), "")
    cleaned = cleaned.replace("question:", "").replace("answer:", "")
    cleaned = cleaned.strip(" .,;:?!-")
    return len(cleaned) < 4


def _generate_caption(blip: dict, img: Image.Image, prompt: str | None,
                      max_new_tokens: int = 60) -> str:
    processor = blip["processor"]
    model = blip["model"]
    device = blip["device"]
    dtype = blip["dtype"]
    model_id = blip["model_id"]
    model_family = blip.get("model_family", "blip2")
    is_opt = model_family == "blip2" and "opt" in model_id.lower()

    if prompt is None:
        raw = processor(images=img.convert("RGB"), return_tensors="pt")
    else:
        raw = processor(images=img.convert("RGB"), text=prompt, return_tensors="pt")

    inputs: dict[str, Any] = {}
    for k, v in raw.items():
        v = v.to(device)
        if v.is_floating_point():
            v = v.to(dtype)
        inputs[k] = v

    with torch.no_grad():
        out_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            num_beams=5,
            repetition_penalty=1.5,
            no_repeat_ngram_size=3,
            length_penalty=1.0,
            early_stopping=True,
        )

    if is_opt and "input_ids" in inputs:
        out_ids = out_ids[:, inputs["input_ids"].shape[1]:]

    text = processor.batch_decode(out_ids, skip_special_tokens=True)[0].strip()
    if is_opt and prompt:
        text = _strip_prompt_echo(text, prompt)
    return _dedupe_repeats(text).strip()


def caption_image_blip2(blip: dict, img: Image.Image) -> str:
    model_id = blip["model_id"]
    model_family = blip.get("model_family", "blip2")
    is_flan = model_family == "blip2" and "flan" in model_id.lower()
    is_opt = model_family == "blip2" and "opt" in model_id.lower()

    if is_flan:
        answers: list[str] = []
        for q in _BLIP2_FLAN_QUESTIONS:
            try:
                ans = _generate_caption(blip, img, q, max_new_tokens=60)
            except Exception:
                continue
            if ans and not _is_prompt_echo(ans, q):
                answers.append(ans.rstrip("."))
        seen, exact_unique = set(), []
        for a in answers:
            key = a.lower()
            if key and key not in seen:
                seen.add(key)
                exact_unique.append(a)
        joined = _filter_overlapping(exact_unique)
        text = ". ".join(joined).strip()
        if text:
            return text
        try:
            simple_q = "Question: Describe this room. Answer:"
            ans = _generate_caption(blip, img, simple_q, max_new_tokens=60)
            if ans and not _is_prompt_echo(ans, simple_q):
                return ans
        except Exception:
            pass
        return "Caption failed"

    if is_opt:
        try:
            text = _generate_caption(blip, img, _BLIP2_OPT_PROMPT, max_new_tokens=50)
            if text and not _is_prompt_echo(text, _BLIP2_OPT_PROMPT):
                return text
        except Exception:
            pass
        try:
            text = _generate_caption(blip, img, "a", max_new_tokens=50)
            if text and not _is_prompt_echo(text, "a"):
                return text
        except Exception:
            pass
        return "Caption failed"

    # BLIP-1 fallback (unconditional)
    try:
        text = _generate_caption(blip, img, None, max_new_tokens=60)
        if text:
            return text
    except Exception:
        pass
    return "Caption failed"


# ─────────────────────────────────────────────────────────────────────────────
# Description assembly (English, room-grouped)
# ─────────────────────────────────────────────────────────────────────────────
_ROOM_KEYWORDS: dict[str, list[str]] = {
    "outdoor": ["swimming pool", "pool", "garden", "backyard", "yard", "lawn",
                "grass", "palm tree", "palm trees"],
    "exterior": ["facade", "exterior", "front of the house", "front of house",
                 "front door", "white house", "iron gate", "gated entrance",
                 "gate ", "villa exterior", "house with",
                 "house for sale", "for sale", "house is made of", "brick and tile",
                 "house is white", "house is brick"],
    "parking": ["driveway", "garage", "carport", "parking space",
                "parking spot", "parking area"],
    "kitchen": ["kitchen", "countertop", "counter top", "cabinet", "stove", "oven",
                "refrigerator", "fridge", "dishwasher", "microwave", "cooktop"],
    "bathroom": ["bathroom", "bath ", "shower", "toilet", "vanity", "bathtub",
                 " tub", "towel rack"],
    "bedroom": ["bedroom", "bed frame", "bed ", " beds", "mattress", "closet",
                "wardrobe", "dresser", "nightstand"],
    "living room": ["living room", "living area", "living space", "sofa", "couch",
                    "armchair", "coffee table", "fireplace", "lounge"],
    "dining room": ["dining room", "dining area", "dining table", "dining set"],
    "balcony": ["balcony", "terrace", "patio", "outdoor area", "deck", "city view",
                "garden view"],
    "hallway": ["hallway", "entryway", "foyer", "corridor"],
    "home office": ["home office", "office desk", "workspace", "study room"],
    "laundry": ["laundry room", "washer", "dryer", "laundry area"],
}

_ROOM_DISPLAY: dict[str, str] = {
    "outdoor": "Outdoor Space",
    "exterior": "Exterior",
    "parking": "Parking",
    "kitchen": "Kitchen",
    "bathroom": "Bathroom",
    "bedroom": "Bedroom",
    "living room": "Living Room",
    "dining room": "Dining Area",
    "balcony": "Balcony",
    "hallway": "Entryway",
    "home office": "Home Office",
    "laundry": "Laundry Room",
}


def _detect_room(caption: str) -> str:
    cl = caption.lower()
    for room, keywords in _ROOM_KEYWORDS.items():
        if any(kw in cl for kw in keywords):
            return room
    return "general"


def _label(room: str) -> str:
    return _ROOM_DISPLAY.get(room, room.title())


def _dedup(caps: list[str]) -> list[str]:
    seen, out = set(), []
    for c in caps:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def assemble_description_blip2(captions_data: list[dict]) -> dict:
    _empty = {
        "html": "No description could be generated from the uploaded photos.",
        "text": "No description could be generated from the uploaded photos.",
    }
    if not captions_data:
        return _empty

    rooms: dict[str, list[str]] = {}
    ungrouped: list[str] = []
    for d in captions_data:
        cap = d["caption"].strip()
        if not cap or cap.lower() == "caption failed":
            continue
        room = _detect_room(cap)
        if room == "general":
            ungrouped.append(cap)
        else:
            rooms.setdefault(room, []).append(cap)

    rooms = {k: _dedup(v) for k, v in rooms.items()}
    ungrouped = _dedup(ungrouped)

    if not rooms and not ungrouped:
        return _empty

    room_names = [_label(r).lower() for r in rooms.keys()]
    if not room_names:
        overview = "This property features the following highlights."
    elif len(room_names) == 1:
        overview = f"This property showcases a beautifully appointed {room_names[0]}."
    elif len(room_names) == 2:
        overview = f"This property features a well-designed {room_names[0]} and {room_names[1]}."
    else:
        overview = (
            f"This property features {', '.join(room_names[:-1])}, and {room_names[-1]}."
        )

    html_parts = [f"<p>{overview}</p>"]
    text_parts = [overview, ""]
    for room, caps in rooms.items():
        label = _label(room)
        html_parts.append(
            f'<p style="font-weight:700;margin:0.75rem 0 0.25rem;">{label}</p>'
            f'<ul style="margin:0;padding-left:1.2rem;">'
        )
        text_parts.append(f"{label}:")
        for cap in caps[:3]:
            cap = cap.rstrip(".") + "."
            html_parts.append(f"<li>{cap}</li>")
            text_parts.append(f"  - {cap}")
        html_parts.append("</ul>")
        text_parts.append("")

    if ungrouped:
        html_parts.append(
            '<p style="font-weight:700;margin:0.75rem 0 0.25rem;">Additional Features</p>'
            '<ul style="margin:0;padding-left:1.2rem;">'
        )
        text_parts.append("Additional Features:")
        for cap in ungrouped[:4]:
            cap = cap.rstrip(".") + "."
            html_parts.append(f"<li>{cap}</li>")
            text_parts.append(f"  - {cap}")
        html_parts.append("</ul>")

    return {"html": "".join(html_parts), "text": "\n".join(text_parts).strip()}


# ─────────────────────────────────────────────────────────────────────────────
# Ollama humanization + DB-aligned field extraction
# ─────────────────────────────────────────────────────────────────────────────
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:8b")

# External OpenAI-compatible fallback (ESPRIT Llama-3.1-70B or OpenRouter)
ESPRIT_BASE_URL = os.environ.get("ESPRIT_BASE_URL", "")
ESPRIT_API_KEY = os.environ.get("ESPRIT_LLM_API_KEY", "")
ESPRIT_MODEL = os.environ.get("ESPRIT_MODEL_NAME", "hosted_vllm/Llama-3.1-70B-Instruct")
OPENROUTER_KEYS = [
    k for k in [
        os.environ.get("OPENROUTER_API_1"),
        os.environ.get("OPENROUTER_API_2"),
        os.environ.get("OPENROUTER_API_3"),
    ] if k
]

_FIELD_DEFAULTS: dict[str, object] = {
    "has_piscine": False,
    "has_climatisation": False,
    "has_balcon": False,
    "has_terrasse": False,
    "has_jardin": False,
    "has_garage": False,
    "has_parking": False,
    "has_chaffage": False,
    "has_ascenseur": False,
    "has_gardien": False,
    "cuisine": "",
    "salle_de_bain": 0,
    "pieces_min": 0,
    "type": "",
    "topology_hint": "",
    "standing_hint": "",
    "exterior_visible": False,
}


def _build_humanize_prompt(captions_data: list[dict]) -> str:
    lines: list[str] = []
    for d in captions_data:
        cap = (d.get("caption") or "").strip()
        if cap and cap.lower() != "caption failed":
            lines.append(f"- {cap}")
    captions_block = "\n".join(lines) if lines else "(no captions)"
    keys = ", ".join(_FIELD_DEFAULTS.keys())
    return (
        "You are a professional real-estate copywriter for the Tunisian market.\n\n"
        "Below are English image captions from photos of a SINGLE property. Use them to:\n"
        "1. Write a 2-paragraph property listing in FRENCH, ~80–120 words, prose only — "
        "NO bullets, NO emojis. Use natural Tunisian listing style "
        "(\"appartement\", \"villa\", \"lumineux\", \"haut standing\" when warranted).\n"
        "2. Extract a structured JSON object with EXACTLY these keys (database columns): "
        f"{keys}.\n\n"
        "Rules for the JSON:\n"
        "- All `has_*` values are booleans. Set true ONLY if a caption explicitly supports it.\n"
        "- `salle_de_bain` is an integer count of distinct bathrooms visible.\n"
        "- `pieces_min` is the MIN visible bedrooms (be conservative; never guess).\n"
        "- `type` ∈ {\"Appartement\", \"Villa\", \"Maison\", \"Studio\", \"\"}.\n"
        "- `topology_hint` ∈ {\"S+0\",\"S+1\",\"S+2\",\"S+3\",\"S+4\",\"S+5\",\"\"}. "
        "Leave \"\" unless captions clearly support the count.\n"
        "- `cuisine` is a short French descriptor (e.g. \"équipée\", \"moderne\", \"américaine\") or \"\".\n"
        "- `standing_hint` is \"haut_standing\" only when captions mention luxury/marble/high-end.\n"
        "- `exterior_visible` is true if any caption shows building exterior, garden, pool, driveway, gate.\n\n"
        f"Captions:\n{captions_block}\n\n"
        "Output ONE valid JSON object with EXACTLY two top-level keys: `description_fr`, `fields`. "
        "No markdown fences, no commentary."
    )


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that some LLMs emit despite format=json."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop first line (```json or ```) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()
    return text


def call_ollama(prompt: str, model: str = OLLAMA_MODEL, timeout: int = 180) -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.3},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    raw = (r.json().get("response") or "").strip()
    if not raw:
        raise ValueError("Ollama returned an empty response")
    return json.loads(_strip_fences(raw))


def _english_fallback_description(captions_data: list[dict]) -> str:
    """Plain-text fallback when Ollama is unavailable."""
    lines = [
        d["caption"] for d in captions_data
        if d.get("caption") and d["caption"].lower() != "caption failed"
    ]
    if not lines:
        return ""
    return " ".join(lines[:5])


def _call_openai_compat(prompt: str, base_url: str, api_key: str, model: str, timeout: int = 60) -> dict:
    """Call an OpenAI-compatible chat-completions endpoint and parse JSON from the response."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    r = requests.post(url, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    return json.loads(_strip_fences(content))


def call_llm(prompt: str) -> dict:
    """Try ESPRIT → OpenRouter → Ollama in order, returning the first that succeeds."""
    # 1. ESPRIT (Llama-3.1-70B on university cluster — free, fast)
    if ESPRIT_BASE_URL and ESPRIT_API_KEY:
        try:
            return _call_openai_compat(prompt, ESPRIT_BASE_URL, ESPRIT_API_KEY, ESPRIT_MODEL, timeout=90)
        except Exception:
            pass

    # 2. OpenRouter (rotate through up to 3 keys)
    for key in OPENROUTER_KEYS:
        try:
            return _call_openai_compat(
                prompt,
                "https://openrouter.ai/api/v1",
                key,
                "meta-llama/llama-3.1-8b-instruct:free",
                timeout=60,
            )
        except Exception:
            continue

    # 3. Local Ollama (last resort — may fail when GPU is saturated)
    return call_ollama(prompt)


def humanize_and_extract(captions_data: list[dict]) -> dict:
    try:
        result = call_llm(_build_humanize_prompt(captions_data))
    except Exception as e:
        return {
            "description_fr": _english_fallback_description(captions_data),
            "fields": dict(_FIELD_DEFAULTS),
            "_error": f"{type(e).__name__}: {e}",
        }

    description = (result.get("description_fr") or "").strip()
    raw_fields = result.get("fields") or {}
    fields: dict[str, object] = {}
    for k, default in _FIELD_DEFAULTS.items():
        v = raw_fields.get(k, default)
        if isinstance(default, bool):
            fields[k] = bool(v) if v is not None else False
        elif isinstance(default, int):
            try:
                fields[k] = int(v) if v is not None else 0
            except (TypeError, ValueError):
                fields[k] = 0
        else:
            fields[k] = (str(v).strip() if v is not None else "")
    return {"description_fr": description, "fields": fields}


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end convenience
# ─────────────────────────────────────────────────────────────────────────────
def caption_listing(
    blip: dict,
    images: list[tuple[str, bytes]],
    skip_ollama: bool = False,
) -> dict:
    """One-shot pipeline. Takes [(filename, raw_bytes), ...] and returns the
    full DB-ready record. Set skip_ollama=True to return only English output.
    """
    captions_data: list[dict] = []
    for filename, blob in images:
        try:
            img = Image.open(io.BytesIO(blob))
            cap = caption_image_blip2(blip, img)
        except Exception as e:
            cap = f"Caption failed: {type(e).__name__}"
        captions_data.append({"file": filename, "caption": cap})

    desc_en = assemble_description_blip2(captions_data)
    record: dict[str, object] = {
        "captions_en": captions_data,
        "description_en_html": desc_en["html"],
        "description_en_text": desc_en["text"],
        "model_caption": blip["model_id"],
    }
    if not skip_ollama:
        enriched = humanize_and_extract(captions_data)
        record["description_fr"] = enriched["description_fr"]
        record["fields"] = enriched["fields"]
        record["model_humanizer"] = OLLAMA_MODEL
        if enriched.get("_error"):
            record["humanizer_error"] = enriched["_error"]
    return record
