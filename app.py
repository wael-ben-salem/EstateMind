"""
Apartment Listing Generator — Streamlit UI
Run: streamlit run app.py
"""
import os
import io
import json
import time
import shutil
import socket
from pathlib import Path

import requests  # Ollama HTTP client (transitive Streamlit dep, no extra install)

import streamlit as st
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

# ─────────────────────────────────────────────────────────────────────────────
# Page config — must be first Streamlit command
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Apartment Listing Generator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — minimal, real-estate themed
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide Streamlit default chrome */
    #MainMenu, header, footer {visibility: hidden;}

    /* Main content padding */
    .main .block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px;}

    /* Headline */
    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        color: #1a3a52;
        margin-bottom: 0.3rem;
        letter-spacing: -0.02em;
    }
    .hero-sub {
        color: #6b7280;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }

    /* Upload area */
    [data-testid="stFileUploader"] {
        background: #f8fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 12px;
        padding: 1.5rem;
        transition: all 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #1a3a52;
        background: #f1f5f9;
    }

    /* Caption cards */
    .caption-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.8rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .caption-text {
        color: #1a3a52;
        font-size: 0.95rem;
        font-weight: 500;
        margin: 0.5rem 0 0;
        line-height: 1.4;
    }
    .filename {
        color: #94a3b8;
        font-size: 0.75rem;
        font-family: monospace;
    }

    /* Description box */
    .description-box {
        background: linear-gradient(135deg, #f0f7ff 0%, #f8fafc 100%);
        border-left: 4px solid #1a3a52;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        font-size: 1.05rem;
        line-height: 1.7;
        color: #1f2937;
    }

    /* Stats badges */
    .stat-badge {
        display: inline-block;
        background: #1a3a52;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }
    .stat-badge-light {
        background: #e2e8f0;
        color: #475569;
    }

    /* Buttons */
    .stButton > button {
        background: #1a3a52;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #2563eb;
        transform: translateY(-1px);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SAT Model architecture (must match training notebook)
# ─────────────────────────────────────────────────────────────────────────────
class Attention(nn.Module):
    def __init__(self, encoder_dim=512, decoder_dim=512, attention_dim=512):
        super().__init__()
        self.encoder_linear = nn.Linear(encoder_dim, attention_dim)
        self.decoder_linear = nn.Linear(decoder_dim, attention_dim)
        self.score_linear = nn.Linear(attention_dim, 1)

    def forward(self, encoder_features, decoder_hidden):
        enc_part = self.encoder_linear(encoder_features)
        dec_part = self.decoder_linear(decoder_hidden).unsqueeze(1)
        energy = self.score_linear(torch.tanh(enc_part + dec_part)).squeeze(2)
        alpha = torch.softmax(energy, dim=1)
        context = (encoder_features * alpha.unsqueeze(2)).sum(dim=1)
        return context, alpha


class Encoder(nn.Module):
    def __init__(self, encoded_dim=512):
        super().__init__()
        resnet = models.resnet50(weights=None)
        self.resnet = nn.Sequential(*list(resnet.children())[:-2])
        self.pool = nn.AdaptiveAvgPool2d((14, 14))
        self.linear = nn.Linear(2048, encoded_dim)

    def forward(self, images):
        feat = self.pool(self.resnet(images))
        B = feat.shape[0]
        return self.linear(feat.permute(0, 2, 3, 1).reshape(B, 196, 2048))


class BaselineEncoder(nn.Module):
    def __init__(self, encoded_dim=512):
        super().__init__()
        resnet = models.resnet50(weights=None)
        self.resnet = nn.Sequential(*list(resnet.children())[:-1])
        self.linear = nn.Linear(2048, encoded_dim)

    def forward(self, images):
        return self.linear(self.resnet(images).view(images.size(0), -1))


class ViTEncoder(nn.Module):
    def __init__(self, encoded_dim=512):
        super().__init__()
        from torchvision.models import vit_b_16
        vit = vit_b_16(weights=None)
        self.conv_proj = vit.conv_proj
        self.class_token = vit.class_token
        self.encoder = vit.encoder
        self.project = nn.Linear(768, encoded_dim)

    def forward(self, images):
        B = images.shape[0]
        x = self.conv_proj(images).reshape(B, 768, -1).permute(0, 2, 1)
        cls = self.class_token.expand(B, -1, -1)
        x = self.encoder(torch.cat([cls, x], dim=1))
        return self.project(x[:, 1:, :])


class CLIPEncoder(nn.Module):
    def __init__(self, encoded_dim=512):
        super().__init__()
        import clip as _clip_lib
        clip_model, _ = _clip_lib.load("ViT-B/32", device="cpu")
        self.visual = clip_model.visual.float()
        self.encoded_dim = encoded_dim
        self.project = nn.Linear(512, encoded_dim)
        self.register_buffer("in_mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer("in_std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))
        self.register_buffer("cl_mean", torch.tensor([0.48145466, 0.4578275, 0.40821073]).view(1, 3, 1, 1))
        self.register_buffer("cl_std", torch.tensor([0.26862954, 0.26130258, 0.27577711]).view(1, 3, 1, 1))

    def _renorm(self, x):
        return (x * self.in_std + self.in_mean - self.cl_mean) / self.cl_std

    def forward(self, images):
        images = self._renorm(images)
        v, B = self.visual, images.shape[0]
        x = v.conv1(images).reshape(B, v.conv1.out_channels, -1).permute(0, 2, 1)
        cls = v.class_embedding.view(1, 1, -1).expand(B, -1, -1)
        x = v.ln_pre(torch.cat([cls, x], dim=1) + v.positional_embedding)
        x = v.transformer(x.permute(1, 0, 2)).permute(1, 0, 2)
        patches = v.ln_post(x[:, 1:, :])
        if v.proj is not None:
            patches = patches @ v.proj
        patches = self.project(patches)
        feat = patches.reshape(B, 7, 7, self.encoded_dim).permute(0, 3, 1, 2)
        feat = F.interpolate(feat, size=(14, 14), mode="bilinear", align_corners=False)
        return feat.permute(0, 2, 3, 1).reshape(B, 196, self.encoded_dim)


class Decoder(nn.Module):
    def __init__(self, embed_dim, decoder_dim, vocab_size, pad_idx,
                 encoder_dim=512, attention_dim=512, dropout=0.5):
        super().__init__()
        self.decoder_dim = decoder_dim
        self.vocab_size = vocab_size
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.attention = Attention(encoder_dim, decoder_dim, attention_dim)
        self.lstm_cell = nn.LSTMCell(embed_dim + encoder_dim, decoder_dim)
        self.init_h = nn.Linear(encoder_dim, decoder_dim)
        self.init_c = nn.Linear(encoder_dim, decoder_dim)
        self.beta_gate = nn.Linear(decoder_dim, encoder_dim)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(decoder_dim, vocab_size)

    def init_hidden_state(self, feats):
        mean = feats.mean(dim=1)
        return torch.tanh(self.init_h(mean)), torch.tanh(self.init_c(mean))

    def generate_caption(self, encoder_features, start_idx, end_idx, pad_idx, unk_idx,
                         idx_to_word, max_len=50, beam_size=3):
        h, c = self.init_hidden_state(encoder_features)
        beams, completed = [(0.0, [start_idx], h, c)], []
        for _ in range(max_len):
            new_beams = []
            for score, seq, hp, cp in beams:
                last = torch.tensor([seq[-1]], device=encoder_features.device)
                emb = self.embedding(last)
                ctx, alpha = self.attention(encoder_features, hp)
                beta = torch.sigmoid(self.beta_gate(hp))
                ctx = beta * ctx
                hn, cn = self.lstm_cell(torch.cat([emb, ctx], dim=1), (hp, cp))
                lp = torch.log_softmax(self.fc(hn), dim=1)
                topk_s, topk_w = lp[0].topk(beam_size)
                for s, w in zip(topk_s.tolist(), topk_w.tolist()):
                    entry = (score + s, seq + [w], hn, cn)
                    (completed if w == end_idx else new_beams).append(entry)
            if not new_beams:
                break
            new_beams.sort(key=lambda x: x[0], reverse=True)
            beams = new_beams[:beam_size]
        if not completed:
            completed = [(b[0], b[1], b[2], b[3]) for b in beams]
        best = max(completed, key=lambda x: x[0])
        words = [idx_to_word[w] for w in best[1][1:]
                 if w not in (end_idx, pad_idx, start_idx, unk_idx)
                 and idx_to_word.get(w, "<unk>") not in ("<pad>", "<start>", "<end>", "<unk>")]
        return words


class BaselineDecoder(nn.Module):
    def __init__(self, embed_dim, decoder_dim, vocab_size, pad_idx,
                 encoder_dim=512, dropout=0.5):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.lstm_cell = nn.LSTMCell(embed_dim, decoder_dim)
        self.init_h = nn.Linear(encoder_dim, decoder_dim)
        self.init_c = nn.Linear(encoder_dim, decoder_dim)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(decoder_dim, vocab_size)

    def generate_caption(self, feat, start_idx, end_idx, pad_idx, unk_idx,
                         idx_to_word, max_len=50, beam_size=3):
        h = torch.tanh(self.init_h(feat))
        c = torch.tanh(self.init_c(feat))
        beams, completed = [(0.0, [start_idx], h, c)], []
        for _ in range(max_len):
            new_beams = []
            for score, seq, hp, cp in beams:
                last = torch.tensor([seq[-1]], device=feat.device)
                emb = self.embedding(last)
                hn, cn = self.lstm_cell(emb, (hp, cp))
                lp = torch.log_softmax(self.fc(hn), dim=1)
                topk_s, topk_w = lp[0].topk(beam_size)
                for s, w in zip(topk_s.tolist(), topk_w.tolist()):
                    entry = (score + s, seq + [w], hn, cn)
                    (completed if w == end_idx else new_beams).append(entry)
            if not new_beams:
                break
            new_beams.sort(key=lambda x: x[0], reverse=True)
            beams = new_beams[:beam_size]
        if not completed:
            completed = [(b[0], b[1], b[2], b[3]) for b in beams]
        best = max(completed, key=lambda x: x[0])
        words = [idx_to_word[w] for w in best[1][1:]
                 if w not in (end_idx, pad_idx, start_idx, unk_idx)
                 and idx_to_word.get(w, "<unk>") not in ("<pad>", "<start>", "<end>", "<unk>")]
        return words


# ─────────────────────────────────────────────────────────────────────────────
# SAT model loading and inference
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_sat_model(bundle_path: str) -> dict:
    """Load the trained SAT model bundle. Cached across reruns."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bundle = torch.load(bundle_path, map_location=device)

    word_to_idx = bundle["word_to_idx"]
    idx_to_word = {int(k): v for k, v in bundle["idx_to_word"].items()}
    VOCAB_SIZE = bundle["vocab_size"]
    PAD_IDX = word_to_idx["<pad>"]
    START_IDX = word_to_idx["<start>"]
    END_IDX = word_to_idx["<end>"]
    UNK_IDX = word_to_idx["<unk>"]

    has_att = bundle["has_attention"]
    model_name = bundle["model_name"]

    if "ViT" in model_name:
        ENC_CLS = ViTEncoder
    elif "CLIP" in model_name:
        ENC_CLS = CLIPEncoder
    elif has_att:
        ENC_CLS = Encoder
    else:
        ENC_CLS = BaselineEncoder

    enc = ENC_CLS(512).to(device)
    dec = (Decoder(256, 512, VOCAB_SIZE, PAD_IDX) if has_att
           else BaselineDecoder(256, 512, VOCAB_SIZE, PAD_IDX)).to(device)

    enc.load_state_dict(bundle["encoder_state"])
    dec.load_state_dict(bundle["decoder_state"])
    enc.eval()
    dec.eval()

    return {
        "encoder": enc,
        "decoder": dec,
        "device": device,
        "has_att": has_att,
        "model_name": model_name,
        "bleu4": bundle.get("bleu4", 0),
        "vocab_size": VOCAB_SIZE,
        "PAD_IDX": PAD_IDX,
        "START_IDX": START_IDX,
        "END_IDX": END_IDX,
        "UNK_IDX": UNK_IDX,
        "idx_to_word": idx_to_word,
    }


def preprocess_image(img: Image.Image) -> torch.Tensor:
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    return transform(img.convert("RGB")).unsqueeze(0)


def caption_image_sat(model_dict: dict, img: Image.Image, beam_size: int = 3) -> str:
    tensor = preprocess_image(img).to(model_dict["device"])
    with torch.no_grad():
        feat = model_dict["encoder"](tensor)
        words = model_dict["decoder"].generate_caption(
            feat,
            model_dict["START_IDX"], model_dict["END_IDX"],
            model_dict["PAD_IDX"], model_dict["UNK_IDX"],
            model_dict["idx_to_word"], beam_size=beam_size,
        )
    return " ".join(words).strip()


# ─────────────────────────────────────────────────────────────────────────────
# BLIP-2 / BLIP model loading
# ─────────────────────────────────────────────────────────────────────────────
# FLAN-T5 BLIP-2 follows short question-style prompts far better than long
# instructions. Asking several focused questions and stitching the answers
# produces richer, more reliable output than one giant prompt.
_BLIP2_FLAN_QUESTIONS = [
    # Neutral: works for indoor rooms AND outdoor / exterior shots.
    # "What room is this?" forced outdoor photos to hallucinate as bedrooms.
    "Question: What does this photo show? Answer:",
    "Question: What are the main features and materials visible? Answer:",
]
# OPT BLIP-2 doesn't follow instructions; it works best as a captioner with a
# short noun-phrase prefix that gets echoed back and stripped.
_BLIP2_OPT_PROMPT = "a photo of"

# Stopwords used by phrase-overlap dedup. Keep tiny — only the most generic.
_DEDUP_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "with", "in", "on", "is", "are",
    "was", "were", "this", "that", "has", "have", "to", "for", "from", "by",
    "at", "it", "its", "be", "very", "some", "there", "here",
}


def _content_words(s: str) -> set[str]:
    """Lowercased content tokens (stopwords / single chars stripped)."""
    out = set()
    for w in s.lower().split():
        w = w.strip(".,;:!?\"'()[]")
        if len(w) > 1 and w not in _DEDUP_STOPWORDS:
            out.add(w)
    return out


def _filter_overlapping(parts: list[str]) -> list[str]:
    """Drop a sentence when another sentence in the list is a strict superset
    of its content words. Preserves the most informative phrasing.

    Example — input:
        ["a house with a swimming pool",
         "the house is white and has a swimming pool"]
    {house, swimming, pool} ⊂ {house, white, swimming, pool}, so the first
    sentence is dropped and we keep the version that mentions "white".
    """
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


@st.cache_resource(show_spinner="Loading BLIP-2 (first time downloads ~15 GB)...")
def load_blip2_model(model_id: str) -> dict:
    """Load BLIP-2 from HuggingFace Hub. Raises RuntimeError with actionable message on failure."""
    from transformers import Blip2Processor, Blip2ForConditionalGeneration

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float16 if device.type == "cuda" else torch.float32

    try:
        processor = Blip2Processor.from_pretrained(model_id)
        if device.type == "cuda":
            model = Blip2ForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                device_map="auto",
            )
        else:
            model = Blip2ForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=torch.float32,
            )
        model.eval()
        return {
            "processor": processor,
            "model": model,
            "model_id": model_id,
            "device": device,
            "dtype": dtype,
            "model_family": "blip2",
        }
    except Exception as e:
        raise RuntimeError(
            f"Failed to load BLIP-2: {type(e).__name__}: {e}\n\n"
            "Common fixes:\n"
            "  1. Check internet connection (first download is ~15 GB)\n"
            "  2. Run `huggingface-cli login` in terminal\n"
            "  3. Make sure you have ~20 GB free on C: drive\n"
            "  4. If GPU OOM, try a smaller model: 'Salesforce/blip2-opt-2.7b' → 'Salesforce/blip-image-captioning-large'"
        ) from e


@st.cache_resource(show_spinner="Loading BLIP fallback model (downloads ~1 GB)...")
def load_blip_fallback() -> dict:
    """Load the smaller BLIP-1 model as a fallback when BLIP-2 fails."""
    from transformers import BlipProcessor, BlipForConditionalGeneration

    model_id = "Salesforce/blip-image-captioning-large"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float16 if device.type == "cuda" else torch.float32

    try:
        processor = BlipProcessor.from_pretrained(model_id)
        model = BlipForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=dtype,
        ).to(device)
        model.eval()
        return {
            "processor": processor,
            "model": model,
            "model_id": model_id,
            "device": device,
            "dtype": dtype,
            "model_family": "blip1",
        }
    except Exception as e:
        raise RuntimeError(
            f"Failed to load BLIP fallback: {type(e).__name__}: {e}"
        ) from e


def _strip_prompt_echo(text: str, prompt: str) -> str:
    """OPT prepends the prompt to the output; strip it (case-insensitive)."""
    if text.lower().startswith(prompt.lower()):
        return text[len(prompt):].strip(" .,:;-")
    return text


def _dedupe_repeats(text: str) -> str:
    """Collapse repeated sentences and back-to-back phrase repeats."""
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
    # Collapse "X X" where the first half equals the second half (4+ words)
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
    """True when the output is essentially just the prompt repeated."""
    if not text:
        return True
    cleaned = text.lower().replace(prompt.lower(), "")
    cleaned = cleaned.replace("question:", "").replace("answer:", "")
    cleaned = cleaned.strip(" .,;:?!-")
    return len(cleaned) < 4


def _generate_caption(blip_dict: dict, img: Image.Image, prompt: str | None,
                       max_new_tokens: int = 60) -> str:
    """Run a single generate() call; returns decoded text (prompt prefix stripped for OPT)."""
    processor = blip_dict["processor"]
    model = blip_dict["model"]
    device = blip_dict["device"]
    dtype = blip_dict["dtype"]
    model_id = blip_dict["model_id"]
    model_family = blip_dict.get("model_family", "blip2")
    is_opt = model_family == "blip2" and "opt" in model_id.lower()

    if prompt is None:
        raw = processor(images=img.convert("RGB"), return_tensors="pt")
    else:
        raw = processor(images=img.convert("RGB"), text=prompt, return_tensors="pt")

    inputs = {}
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


def caption_image_blip2(blip_dict: dict, img: Image.Image) -> str:
    """
    Generate a real-estate caption.
      - FLAN-T5: ask several short questions, concatenate answers (no echo).
      - OPT: short noun-phrase prompt; echoed prefix stripped.
      - BLIP-1 fallback: unconditional caption.
    Empty / prompt-echo results trigger a simpler retry. Ultimate failures
    return "Caption failed" so they're visible instead of silently empty.
    """
    model_id = blip_dict["model_id"]
    model_family = blip_dict.get("model_family", "blip2")
    is_flan = model_family == "blip2" and "flan" in model_id.lower()
    is_opt = model_family == "blip2" and "opt" in model_id.lower()

    # ── FLAN-T5: multi-question approach ─────────────────────────────────────
    if is_flan:
        answers: list[str] = []
        for q in _BLIP2_FLAN_QUESTIONS:
            try:
                ans = _generate_caption(blip_dict, img, q, max_new_tokens=60)
            except Exception:
                continue
            if ans and not _is_prompt_echo(ans, q):
                answers.append(ans.rstrip("."))
        # Dedupe exact duplicates first, then drop paraphrased overlaps.
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
        # Retry with one simple prompt
        try:
            simple_q = "Question: Describe this room. Answer:"
            ans = _generate_caption(blip_dict, img, simple_q, max_new_tokens=60)
            if ans and not _is_prompt_echo(ans, simple_q):
                return ans
        except Exception:
            pass
        return "Caption failed"

    # ── OPT: short noun-phrase prompt ───────────────────────────────────────
    if is_opt:
        try:
            text = _generate_caption(blip_dict, img, _BLIP2_OPT_PROMPT, max_new_tokens=50)
            if text and not _is_prompt_echo(text, _BLIP2_OPT_PROMPT):
                return text
        except Exception:
            pass
        # Retry with a barer prompt
        try:
            text = _generate_caption(blip_dict, img, "a", max_new_tokens=50)
            if text and not _is_prompt_echo(text, "a"):
                return text
        except Exception:
            pass
        return "Caption failed"

    # ── BLIP-1 fallback: unconditional captioning ───────────────────────────
    try:
        text = _generate_caption(blip_dict, img, None, max_new_tokens=60)
        if text:
            return text
    except Exception:
        pass
    return "Caption failed"


# ─────────────────────────────────────────────────────────────────────────────
# Ollama-powered humanization + DB-aligned field extraction
# ─────────────────────────────────────────────────────────────────────────────
# Column names mirror bigfinal_realestate_Cleaned.csv so the JSON can be
# inserted into the listings table without remapping. Defaults are returned
# when Ollama is unavailable or the LLM omits a key.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:8b")

_FIELD_DEFAULTS: dict[str, object] = {
    "has_piscine": False,
    "has_climatisation": False,
    "has_balcon": False,
    "has_terrasse": False,
    "has_jardin": False,
    "has_garage": False,
    "has_parking": False,
    "has_chaffage": False,         # column name typo retained from CSV
    "has_ascenseur": False,
    "has_gardien": False,
    "cuisine": "",                  # short style descriptor in French
    "salle_de_bain": 0,             # bathroom count
    "pieces_min": 0,                # MIN visible bedrooms — user confirms topology
    "type": "",                     # Appartement / Villa / Maison / Studio
    "topology_hint": "",            # S+0..S+5 — empty if uncertain
    "standing_hint": "",            # standard / haut_standing
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
    return json.loads(r.json().get("response", "").strip())


def humanize_and_extract(captions_data: list[dict]) -> dict:
    """End-to-end: captions → {description_fr, fields, _error?}.

    Always returns a dict with all expected keys; missing/bad fields fall back to
    `_FIELD_DEFAULTS`. Errors are reported via `_error` rather than raised so the
    UI can show them inline.
    """
    try:
        result = call_ollama(_build_humanize_prompt(captions_data))
    except Exception as e:
        return {
            "description_fr": "",
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
# Description assembly — SAT mode
# ─────────────────────────────────────────────────────────────────────────────
def assemble_description_sat(captions: list[str]) -> str:
    seen, unique = set(), []
    for c in captions:
        c = c.strip().rstrip(".").strip()
        if c and c not in seen:
            seen.add(c)
            unique.append(c)
    if not unique:
        return "No description could be generated from the uploaded photos."
    sentences = [c[0].upper() + c[1:] + "." if len(c) > 1 else c.upper() + "."
                 for c in unique]
    return " ".join(sentences)


# ─────────────────────────────────────────────────────────────────────────────
# Description assembly — BLIP-2 mode (room grouping + structured output)
# ─────────────────────────────────────────────────────────────────────────────
# Order matters: outdoor / exterior / parking are checked first because BLIP-2
# captions for those scenes often contain incidental room words ("bedroom view"
# of a backyard, etc.). Specific outdoor signals win over generic room words.
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


def _detect_room(caption: str) -> str:
    cl = caption.lower()
    for room, keywords in _ROOM_KEYWORDS.items():
        if any(kw in cl for kw in keywords):
            return room
    return "general"


# Friendly section labels — internal detector keys → display names.
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
    """
    Return {"html": ..., "text": ...} — HTML for display, plain text for download.
    Captions are grouped by detected room type; ungrouped captions go to
    'Additional Features'.
    """
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
            f"This property features "
            f"{', '.join(room_names[:-1])}, and {room_names[-1]}."
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

    return {
        "html": "".join(html_parts),
        "text": "\n".join(text_parts).strip(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Session state initialization
# ─────────────────────────────────────────────────────────────────────────────
for _key, _default in {
    "switch_to_sat": False,
    "blip2_error": None,
    "diagnostics_result": None,
}.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default

# Redirect to SAT radio before the widget renders (set by the "switch" button below)
if st.session_state.switch_to_sat:
    st.session_state["_model_radio"] = "My SAT model (academic comparison)"
    st.session_state.switch_to_sat = False


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    model_choice = st.radio(
        "Caption model",
        ["BLIP-2 (recommended for quality)", "My SAT model (academic comparison)"],
        key="_model_radio",
        help=(
            "BLIP-2 generates rich, real-estate-style descriptions. "
            "The SAT model is the Xu et al. 2015 academic project artifact."
        ),
    )
    use_blip2 = model_choice.startswith("BLIP-2")

    blip2_dict = None
    model_dict = None
    model_loaded = False
    beam_size = 3
    bundle_path = "best_model_bundle.pth"
    _blip2_primary_error = None
    _blip2_fallback_used = False

    # ── BLIP-2 branch ─────────────────────────────────────────────────────────
    if use_blip2:
        blip2_model_id = st.selectbox(
            "BLIP-2 variant",
            ["Salesforce/blip2-flan-t5-xl", "Salesforce/blip2-opt-2.7b"],
            index=0,
            help=(
                "flan-t5-xl (recommended): ~7 GB download, ~6 GB VRAM in fp16. "
                "Better at following question-style prompts.  "
                "opt-2.7b: ~15 GB download, ~3.5 GB VRAM in fp16. "
                "Used as automatic fallback if FLAN-T5-XL fails to load."
            ),
        )

        # Auto-fallback chain: selected variant → OPT-2.7b (if FLAN failed) → BLIP-1
        try:
            blip2_dict = load_blip2_model(blip2_model_id)
            st.session_state.blip2_error = None
            model_loaded = True
        except Exception as _e:
            _blip2_primary_error = _e
            fallback_loaded = False
            # If FLAN-T5-XL failed, try OPT-2.7b before dropping to BLIP-1
            if "flan" in blip2_model_id.lower():
                try:
                    with st.spinner("FLAN-T5-XL failed — trying OPT-2.7b..."):
                        blip2_dict = load_blip2_model("Salesforce/blip2-opt-2.7b")
                    st.session_state.blip2_error = None
                    model_loaded = True
                    _blip2_fallback_used = True
                    fallback_loaded = True
                except Exception:
                    pass
            # Last resort: BLIP-1 (~1 GB)
            if not fallback_loaded:
                try:
                    with st.spinner("BLIP-2 failed — trying smaller fallback (~1 GB)..."):
                        blip2_dict = load_blip_fallback()
                    _blip2_fallback_used = True
                    model_loaded = True
                    st.session_state.blip2_error = None
                except Exception as _e2:
                    st.session_state.blip2_error = (
                        f"BLIP-2 ({type(_blip2_primary_error).__name__}): {_blip2_primary_error}"
                        f"\n\nFallback ({type(_e2).__name__}): {_e2}"
                    )
                    model_loaded = False

        st.markdown("---")
        st.markdown("### 📊 Model info")

        if model_loaded:
            if _blip2_fallback_used:
                st.warning("BLIP-2 unavailable. Using BLIP fallback (smaller, ~1 GB).")
            display_name = blip2_dict["model_id"].split("/")[-1]
            st.success(f"**{display_name}**")
            device_label = "CUDA" if blip2_dict["device"].type == "cuda" else "CPU"
            precision_label = "float16" if blip2_dict["dtype"] == torch.float16 else "float32"
            st.metric("Device", device_label)
            st.metric("Precision", precision_label)

            # ── Model status expander ──────────────────────────────────────────
            with st.expander("📦 Model status"):
                st.write(f"**Loaded:** `{blip2_dict['model_id']}`")
                _cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
                st.write(f"**Cache:** `{_cache_dir}`")
                if torch.cuda.is_available():
                    _vram_gb = torch.cuda.memory_allocated() / 1e9
                    st.write(f"**VRAM used:** {_vram_gb:.2f} GB")
                else:
                    st.write("**VRAM:** N/A (CPU mode)")
                if st.button("🔄 Clear cache and retry", key="clear_cache_btn"):
                    st.cache_resource.clear()
                    st.rerun()
        else:
            st.error("Both BLIP-2 and the fallback model failed to load.")

    # ── SAT branch ────────────────────────────────────────────────────────────
    else:
        bundle_path = st.text_input(
            "Model bundle path",
            value="best_model_bundle.pth",
            help="Path to your trained .pth bundle from the training notebook.",
        )
        beam_size = st.slider(
            "Beam size",
            min_value=1, max_value=5, value=3,
            help="Higher = better captions but slower. 1 = greedy decoding.",
        )

        st.markdown("---")
        st.markdown("### 📊 Model info")

        if os.path.isfile(bundle_path):
            try:
                with st.spinner("Loading SAT model..."):
                    model_dict = load_sat_model(bundle_path)
                st.success(f"**{model_dict['model_name']}**")
                st.metric("Validation BLEU-4", f"{model_dict['bleu4']:.4f}")
                st.metric("Vocabulary size", f"{model_dict['vocab_size']:,}")
                st.metric("Device", str(model_dict["device"]).upper())
                model_loaded = True
            except Exception as e:
                st.error(f"Failed to load: {type(e).__name__}")
                st.caption(str(e)[:200])
                model_loaded = False
        else:
            st.warning(f"File not found: `{bundle_path}`")
            st.caption("Train the model first, or switch to BLIP-2 above.")
            model_loaded = False

    # ── Diagnostics — always visible ──────────────────────────────────────────
    st.markdown("---")
    if st.button("🔬 Run diagnostics", key="run_diag_btn"):
        _diag: dict = {}
        _diag["cuda"] = torch.cuda.is_available()
        if _diag["cuda"]:
            try:
                _diag["gpu"] = torch.cuda.get_device_name(0)
            except Exception:
                _diag["gpu"] = "unknown"

        _cache_p = os.path.expanduser("~/.cache/huggingface/hub")
        try:
            _drive = str(Path(_cache_p).anchor) or _cache_p
            _, _, _free = shutil.disk_usage(_drive)
            _diag["disk_free_gb"] = round(_free / 1e9, 1)
        except Exception as _de:
            _diag["disk_free_gb"] = f"error: {_de}"

        try:
            import transformers as _tf_mod
            _diag["transformers"] = _tf_mod.__version__
        except ImportError:
            _diag["transformers"] = "not installed"

        try:
            from huggingface_hub import HfFolder
            _diag["hf_token"] = HfFolder.get_token() is not None
        except Exception:
            _diag["hf_token"] = False

        try:
            _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _sock.settimeout(5)
            _sock.connect(("huggingface.co", 443))
            _sock.close()
            _diag["hf_reachable"] = True
        except Exception:
            _diag["hf_reachable"] = False

        st.session_state.diagnostics_result = _diag

    if st.session_state.get("diagnostics_result"):
        _d = st.session_state.diagnostics_result
        with st.expander("🔬 Diagnostics", expanded=True):
            st.write(f"**CUDA:** {'✅ available' if _d['cuda'] else '❌ not available'}")
            if _d.get("gpu"):
                st.write(f"**GPU:** {_d['gpu']}")
            st.write(f"**Disk free (cache drive):** {_d['disk_free_gb']} GB")
            st.write(f"**transformers:** {_d['transformers']}")
            if _d["hf_token"]:
                st.write("**HF token:** ✅ set")
            else:
                st.write("**HF token:** ❌ not set — run `huggingface-cli login`")
            if _d["hf_reachable"]:
                st.write("**huggingface.co:** ✅ reachable")
            else:
                st.write("**huggingface.co:** ❌ unreachable — check firewall/VPN")

    st.markdown("---")
    if use_blip2:
        st.caption("BLIP-2 · Salesforce Research (2023)")
    else:
        st.caption("Show, Attend and Tell · Xu et al. (2015)")


# ─────────────────────────────────────────────────────────────────────────────
# Main area
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">🏠 Apartment Listing Generator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Upload photos of an apartment — the AI will describe each one and assemble a draft listing.</div>',
    unsafe_allow_html=True,
)

if not model_loaded:
    if use_blip2:
        _err_text = st.session_state.get("blip2_error") or ""
        st.error("**BLIP-2 failed to load** — both the primary model and the automatic fallback are unavailable.")
        if _err_text:
            with st.expander("Error details", expanded=True):
                st.code(_err_text, language=None)
        st.markdown("""
**Try these fixes in order:**

1. **Check your internet connection** — the first download is ~15 GB
2. **Authenticate with HuggingFace** — run this in your terminal:
   ```
   huggingface-cli login
   ```
   Or set the environment variable: `HF_TOKEN=<your_token>`
3. **Accept the model license** — visit the model page on HuggingFace and click "Access repository"
4. **Check disk space** — you need ~20 GB free on the cache drive (`~/.cache/huggingface/hub`)
5. **Try the smaller variant** — select `blip2-flan-t5-xl` in the sidebar (~7 GB download)
6. **Run diagnostics** — click "🔬 Run diagnostics" in the sidebar to pinpoint the issue
""")
        if st.button("Use SAT model instead (no download required)", type="primary"):
            st.session_state.switch_to_sat = True
            st.rerun()
    else:
        st.info("👈 Configure the model bundle path in the sidebar to get started.")
    st.stop()

# Upload area
uploaded = st.file_uploader(
    "Drop photos here or click to browse",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if not uploaded:
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem; color: #94a3b8;'>
            <div style='font-size: 3rem;'>📸</div>
            <div>No photos uploaded yet</div>
            <div style='font-size: 0.85rem; margin-top: 0.5rem;'>
                Best results: 5–15 photos covering different rooms
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# Generate / options row
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
with col_btn1:
    generate_clicked = st.button(f"🪄 Generate ({len(uploaded)} photos)", type="primary")
with col_btn2:
    show_captions = st.checkbox("Show per-photo captions", value=True)

# Initialize cached caption state (persists across button clicks within a session).
if "captions_data" not in st.session_state:
    st.session_state.captions_data = None
    st.session_state.captions_elapsed = 0.0
    st.session_state.captions_signature = None

# Signature changes when the user uploads a different set of files — invalidates cache.
_sig = tuple(sorted(f.name for f in uploaded)) if uploaded else ()
if _sig != st.session_state.captions_signature:
    st.session_state.captions_data = None
    st.session_state.ollama_result = None  # clear stale Ollama output too
    st.session_state.captions_signature = _sig

# Run captioning only when the user clicks Generate. Otherwise, fall through to
# whatever's cached so other buttons (Ollama, downloads) don't wipe the page.
if generate_clicked and uploaded:
    _captions: list[dict] = []
    progress = st.progress(0, text="Captioning photos...")
    t_start = time.time()
    for i, file in enumerate(uploaded):
        try:
            img = Image.open(io.BytesIO(file.read()))
            if use_blip2:
                caption = caption_image_blip2(blip2_dict, img)
            else:
                caption = caption_image_sat(model_dict, img, beam_size=beam_size)
            _captions.append({"file": file.name, "image": img, "caption": caption})
        except Exception as e:
            st.warning(f"Skipped {file.name}: {e}")
        progress.progress((i + 1) / len(uploaded), text=f"Captioning... ({i+1}/{len(uploaded)})")
    progress.empty()
    st.session_state.captions_data = _captions
    st.session_state.captions_elapsed = time.time() - t_start
    st.session_state.ollama_result = None  # fresh captions invalidate prior LLM output

# Show the upload preview (and stop) only when no captions are ready.
if not st.session_state.captions_data:
    if uploaded:
        st.markdown("#### Preview")
        n_preview_cols = max(1, min(4, len(uploaded)))
        cols = st.columns(n_preview_cols)
        for i, file in enumerate(uploaded[:8]):
            with cols[i % n_preview_cols]:
                st.image(file, use_container_width=True)
        if len(uploaded) > 8:
            st.caption(f"...and {len(uploaded) - 8} more")
    st.stop()

captions_data = st.session_state.captions_data
elapsed = st.session_state.captions_elapsed

# ── Results ───────────────────────────────────────────────────────────────────
st.markdown("---")

unique_captions = len(set(d["caption"] for d in captions_data))
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown(f'<span class="stat-badge">{len(captions_data)} photos</span>', unsafe_allow_html=True)
with col_b:
    st.markdown(f'<span class="stat-badge">{unique_captions} unique captions</span>', unsafe_allow_html=True)
with col_c:
    st.markdown(f'<span class="stat-badge stat-badge-light">{elapsed:.1f}s</span>', unsafe_allow_html=True)

# Description
st.markdown("### 📝 Generated listing description")

if use_blip2:
    desc = assemble_description_blip2(captions_data)
    st.markdown(f'<div class="description-box">{desc["html"]}</div>', unsafe_allow_html=True)
    description_text = desc["text"]
else:
    description_text = assemble_description_sat([d["caption"] for d in captions_data])
    st.markdown(f'<div class="description-box">{description_text}</div>', unsafe_allow_html=True)

# Download .txt
col_dl1, col_dl2 = st.columns([1, 4])
with col_dl1:
    st.download_button(
        "⬇️ Download .txt",
        data=description_text,
        file_name="listing_description.txt",
        mime="text/plain",
    )

# ── Humanized French listing + DB-aligned field extraction (Ollama) ──────────
if use_blip2:
    st.markdown("---")
    st.markdown("### ✨ Humanized listing + database fields")
    st.caption(
        "Uses local Ollama (`llama3:8b`) to rewrite the captions as a French "
        "real-estate description and extract fields aligned with the listings DB. "
        "First call may take 5–30s on CPU."
    )

    if "ollama_result" not in st.session_state:
        st.session_state.ollama_result = None
        st.session_state.ollama_elapsed = 0.0

    if st.button("🪄 Generate French description + extract fields", key="ollama_btn"):
        with st.spinner("Calling Ollama..."):
            t0 = time.time()
            st.session_state.ollama_result = humanize_and_extract(captions_data)
            st.session_state.ollama_elapsed = time.time() - t0

    _ollama = st.session_state.ollama_result
    if _ollama:
        if _ollama.get("_error"):
            st.error(f"Ollama call failed: {_ollama['_error']}")
            st.caption(
                "Check that Ollama is running (`ollama serve`) and the model is "
                f"pulled (`ollama pull {OLLAMA_MODEL}`)."
            )
        else:
            st.caption(f"Generated in {st.session_state.ollama_elapsed:.1f}s")
            description_fr = st.text_area(
                "Description (FR) — review/edit before saving",
                value=_ollama["description_fr"],
                height=180,
                key="desc_fr_edit",
            )

            with st.expander("📊 Extracted fields — review & edit before saving", expanded=True):
                f = _ollama["fields"]
                _types = ["", "Appartement", "Villa", "Maison", "Studio"]
                _topos = ["", "S+0", "S+1", "S+2", "S+3", "S+4", "S+5"]
                _stand = ["", "standard", "haut_standing"]

                def _idx(opts: list[str], val: str) -> int:
                    return opts.index(val) if val in opts else 0

                cc1, cc2, cc3 = st.columns(3)
                edited: dict[str, object] = {}
                with cc1:
                    edited["has_piscine"] = st.checkbox("Piscine", f["has_piscine"])
                    edited["has_jardin"] = st.checkbox("Jardin", f["has_jardin"])
                    edited["has_balcon"] = st.checkbox("Balcon", f["has_balcon"])
                    edited["has_terrasse"] = st.checkbox("Terrasse", f["has_terrasse"])
                    edited["has_garage"] = st.checkbox("Garage", f["has_garage"])
                    edited["has_parking"] = st.checkbox("Parking", f["has_parking"])
                with cc2:
                    edited["has_climatisation"] = st.checkbox("Climatisation", f["has_climatisation"])
                    edited["has_chaffage"] = st.checkbox("Chauffage", f["has_chaffage"])
                    edited["has_ascenseur"] = st.checkbox("Ascenseur", f["has_ascenseur"])
                    edited["has_gardien"] = st.checkbox("Gardien", f["has_gardien"])
                    edited["exterior_visible"] = st.checkbox("Extérieur visible", f["exterior_visible"])
                    edited["cuisine"] = st.text_input("Cuisine (style)", value=f["cuisine"])
                with cc3:
                    edited["type"] = st.selectbox("Type", _types, index=_idx(_types, f["type"]))
                    edited["topology_hint"] = st.selectbox(
                        "Topologie (S+N) — vérifier",
                        _topos,
                        index=_idx(_topos, f["topology_hint"]),
                        help="Cannot be inferred from photos alone — confirm manually.",
                    )
                    edited["standing_hint"] = st.selectbox(
                        "Standing", _stand, index=_idx(_stand, f["standing_hint"])
                    )
                    edited["salle_de_bain"] = st.number_input(
                        "Salle de bain", min_value=0, max_value=10, value=int(f["salle_de_bain"])
                    )
                    edited["pieces_min"] = st.number_input(
                        "Pieces (min visibles)", min_value=0, max_value=10, value=int(f["pieces_min"])
                    )

            export_record = {
                "description_fr": description_fr,
                "fields": edited,
                "captions_en": [{"file": d["file"], "caption": d["caption"]} for d in captions_data],
                "model_caption": blip2_dict["model_id"],
                "model_humanizer": OLLAMA_MODEL,
            }
            st.download_button(
                "⬇️ Download listing record (JSON, DB-ready)",
                data=json.dumps(export_record, indent=2, ensure_ascii=False),
                file_name="listing_record.json",
                mime="application/json",
            )

# Per-photo captions grid
if show_captions and captions_data:
    st.markdown("### 🔍 Per-photo captions")
    n_cols = max(1, min(3, len(captions_data)))
    cols = st.columns(n_cols)
    for i, d in enumerate(captions_data):
        with cols[i % n_cols]:
            st.image(d["image"], use_container_width=True)
            st.markdown(
                f'<div class="caption-card">'
                f'<div class="filename">{d["file"]}</div>'
                f'<div class="caption-text">{d["caption"] or "<em>(no caption)</em>"}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# Download structured JSON
if use_blip2:
    model_meta = {"model": blip2_dict["model_id"], "model_type": "BLIP-2"}
else:
    model_meta = {
        "model": model_dict["model_name"],
        "model_type": "SAT",
        "model_bleu4": model_dict["bleu4"],
    }

json_data = {
    **model_meta,
    "n_photos": len(captions_data),
    "n_unique_captions": unique_captions,
    "elapsed_seconds": round(elapsed, 2),
    "per_photo": [{"file": d["file"], "caption": d["caption"]} for d in captions_data],
    "description": description_text,
}
st.download_button(
    "⬇️ Download structured JSON",
    data=json.dumps(json_data, indent=2),
    file_name="listing.json",
    mime="application/json",
)
