"""Batched LLM refinement of the transcript (NVIDIA NIM).

Fixes ONLY clear transcription mistakes (misheard names, spelling, grammar)
WITHOUT changing meaning or length, so per-segment timing - and therefore
audio/video sync - is preserved.

Segments are sent in batches of numbered lines (a handful of API calls
instead of one per segment - reasoning models on NIM have a large per-call
overhead). Any segment the LLM fails to return, or rewrites too
aggressively, falls back to the original Whisper text.
"""
from __future__ import annotations

import logging
import re
import time

from openai import OpenAI

from .config import Settings
from .transcribe import clean_text

logger = logging.getLogger(__name__)

REFINE_INSTRUCTIONS = (
    "You correct speech-to-text transcription errors in lecture transcripts. "
    "Fix ONLY clear problems: misspelled or misheard proper names "
    "(e.g. 'Bayane Strout-Strup' -> 'Bjarne Stroustrup'), wrong or ambiguous "
    "words, and grammar mistakes. Do NOT rephrase, do NOT add or remove "
    "information, keep the same meaning, tone and approximately the same "
    "word count. If a line is already correct, return it unchanged.\n"
    "Input: numbered lines in the format N|text\n"
    "Output: ALL lines, same numbers, same N|text format, one per line, "
    "in the same order. No explanations, no extra text."
)

THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
NUMBERED_LINE = re.compile(r"^\s*(\d+)\s*\|\s*(.+?)\s*$")


def _refine_batch(client: OpenAI, model: str, items: list[tuple[int, str]]) -> dict[int, str]:
    prompt = "\n".join(f"{number}|{text}" for number, text in items)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": REFINE_INSTRUCTIONS},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,  # low temperature: faithful editing, no creativity
        top_p=0.95,
        max_tokens=8192,
        stream=False,
    )
    content = THINK_BLOCK.sub("", response.choices[0].message.content or "")
    refined: dict[int, str] = {}
    for line in content.splitlines():
        match = NUMBERED_LINE.match(line)
        if match:
            refined[int(match.group(1))] = match.group(2).strip().strip('"')
    return refined


def refine_segments(segments: list[dict], settings: Settings) -> int:
    """Set seg["refined_text"] on every segment. Returns count of changes.

    Safe to call without an NVIDIA key: every segment then simply keeps the
    cleaned Whisper text.
    """
    # Default: cleaned original text (overwritten below when refined).
    numbered: list[tuple[int, str]] = []
    for index, segment in enumerate(segments, start=1):
        text = clean_text(segment.get("text", ""))
        segment["refined_text"] = text
        if text:
            numbered.append((index, text))

    if not settings.nvidia_api_key:
        logger.warning("NVIDIA_API_KEY not set - skipping LLM refinement.")
        return 0

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=settings.nvidia_api_key,
        timeout=settings.refine_timeout,
        max_retries=0,  # we do our own retry with logging below
    )

    batches = [
        numbered[i:i + settings.refine_batch_size]
        for i in range(0, len(numbered), settings.refine_batch_size)
    ]

    refined_map: dict[int, str] = {}
    started = time.time()
    for batch_number, batch in enumerate(batches, start=1):
        logger.info("Refining batch %d/%d (%d segments) ...",
                    batch_number, len(batches), len(batch))
        for attempt in range(1, settings.refine_batch_retries + 1):
            try:
                refined_map.update(_refine_batch(client, settings.llm_model, batch))
                break
            except Exception as exc:  # noqa: BLE001 - refinement must never break the pipeline
                logger.warning("  attempt %d/%d failed: %s",
                            attempt, settings.refine_batch_retries, exc)
                if attempt == settings.refine_batch_retries:
                    logger.warning("  keeping original text for this batch")

    # Apply with safety guards; fall back to the original on anything suspicious.
    changed = 0
    for index, original in numbered:
        refined = refined_map.get(index, "").strip()
        if not refined:
            continue
        ratio = len(refined) / max(1, len(original))
        if not (0.6 <= ratio <= 1.5):
            logger.warning("[%02d] rejected LLM rewrite (length ratio %.2f)",
                        index, ratio)
            continue
        if refined != original:
            changed += 1
            logger.info("[%02d] %s\n  -> %s", index, original, refined)
        segments[index - 1]["refined_text"] = refined

    logger.info("Refined %d of %d segments in %.1fs.",
                changed, len(numbered), time.time() - started)
    return changed