# -*- coding: utf-8 -*-
"""
GoGo-Translation-Agent — Reference Demo
=======================================
A self-contained illustration of the production system's core idea:

        Translate -> Reflect -> Improve   (a reflection loop)

with a small glossary injected into the prompt.

This is NOT the production system: it uses a single model, with no state
machine, no multi-model gateway, no DingTalk entry, and no TMS write-back.
Those run on proprietary company infrastructure and are documented in the
README.

Run:
    pip install -r requirements.txt
    export OPENAI_API_KEY=sk-...
    python translation_reflection.py
"""
import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "missing-api-key"),
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.environ.get("GOGO_MODEL", "gpt-4o-mini")

# Tiny demo glossary (production uses a managed glossary + RAG style base).
GLOSSARY = {
    "dashboard": "仪表盘",
    "workspace": "工作台",
}

SYSTEM = (
    "You are a professional software localization translator. Follow the "
    "required target language, preserve the tone and any placeholders/HTML, "
    "and use the provided glossary exactly."
)


def _chat(user, system=SYSTEM):
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content.strip()


def translate(text, source="English", target="Simplified Chinese"):
    glossary = "\n".join(f"{k} => {v}" for k, v in GLOSSARY.items())
    return _chat(
        f"Glossary (must follow):\n{glossary}\n\n"
        f"Translate from {source} to {target}. Output ONLY the translation, "
        f"no explanation.\n\nText:\n{text}"
    )


def reflect(text, draft, target="Simplified Chinese"):
    """Review the draft and return concrete issues ('NONE' if it is fine)."""
    return _chat(
        f"Review the translation below. Check: (1) accuracy / missing or added "
        f"meaning, (2) fluency, (3) {target} style, (4) glossary consistency, "
        f"(5) preserved placeholders/HTML. List concrete issues as short "
        f"bullet points, or reply exactly 'NONE' if there are no issues.\n\n"
        f"Source:\n{text}\n\nDraft:\n{draft}"
    )


def improve(text, draft, issues, target="Simplified Chinese"):
    if issues.strip().upper() == "NONE":
        return draft
    return _chat(
        f"Improve the translation using the review. Output ONLY the revised "
        f"translation.\n\nSource:\n{text}\n\nDraft:\n{draft}\n\nIssues:\n{issues}"
    )


def run(text, source="English", target="Simplified Chinese"):
    draft = translate(text, source, target)
    issues = reflect(text, draft, target)
    final = improve(text, draft, issues, target)
    return draft, issues, final


if __name__ == "__main__":
    demo = "Open the dashboard in your workspace to review the report."
    draft, issues, final = run(demo)
    print("Source :", demo)
    print("Draft  :", draft)
    print("Review :", issues)
    print("Final  :", final)
