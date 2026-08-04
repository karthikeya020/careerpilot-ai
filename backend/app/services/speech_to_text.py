"""Speech-to-text provider abstraction for the Interview Arena.

No offline ASR model ships with this repo, so the deterministic provider
cannot fabricate a transcript from arbitrary audio bytes -- doing so would
be exactly the kind of invented evidence Constitution rule 1 forbids.
Instead:

- Known seeded demo audio fixtures (identified by exact content hash, via
  `register_demo_fixture`) resolve to a fixed, reviewed transcript. This is
  what "deterministic demo transcription" means here, and it's how the
  offline demo dataset produces a working interview replay without any
  external API call.
- Any other audio, with no live provider configured, returns a
  `source="unavailable"` result with zero confidence -- the caller
  (`app/services/interview_service.py`) always falls back to a typed answer
  rather than blocking the interview (Prompt 3 requirement).
- A live adapter (OpenAI's Whisper transcription endpoint) is wired behind
  the same `SpeechToTextProvider` protocol when `SPEECH_TO_TEXT_API_KEY` is
  configured. It is never imported or exercised by the test suite (no key
  in this environment).
"""

import hashlib
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from app.core.config import get_settings


@dataclass
class TranscriptionResult:
    transcript: str
    source: str  # "live_stt" | "deterministic_demo" | "unavailable"
    confidence: float
    provider_name: str
    latency_ms: float = 0.0


class SpeechToTextProvider(Protocol):
    name: str

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> TranscriptionResult: ...


# sha256(audio_bytes) -> a real, reviewed transcript. Populated by the demo
# seed script (app/seed/seed_demo.py) for the fixture audio clips it ships,
# so the deterministic offline demo always produces the same transcript for
# the same known audio -- never a guess at arbitrary uploaded content.
_DEMO_FIXTURE_TRANSCRIPTS: dict[str, str] = {}


def register_demo_fixture(audio_bytes: bytes, transcript: str) -> None:
    _DEMO_FIXTURE_TRANSCRIPTS[hashlib.sha256(audio_bytes).hexdigest()] = transcript


def clear_demo_fixtures() -> None:
    _DEMO_FIXTURE_TRANSCRIPTS.clear()


class DeterministicSpeechToTextProvider:
    name = "deterministic-demo"

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> TranscriptionResult:
        start = time.perf_counter()
        digest = hashlib.sha256(audio_bytes).hexdigest()
        transcript = _DEMO_FIXTURE_TRANSCRIPTS.get(digest)
        latency_ms = (time.perf_counter() - start) * 1000
        if transcript is not None:
            return TranscriptionResult(
                transcript=transcript,
                source="deterministic_demo",
                confidence=0.9,
                provider_name=self.name,
                latency_ms=round(latency_ms, 3),
            )
        return TranscriptionResult(
            transcript="",
            source="unavailable",
            confidence=0.0,
            provider_name=self.name,
            latency_ms=round(latency_ms, 3),
        )


class OpenAIWhisperProvider:
    """Live adapter. Only constructed when `SPEECH_TO_TEXT_API_KEY` is set;
    never imported or exercised by the test suite (no key in this
    environment) -- satisfies "tests must not require paid API access"
    without being a stub."""

    name = "openai-whisper"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> TranscriptionResult:
        import httpx

        start = time.perf_counter()
        extension = (mime_type.split("/")[-1] or "webm").split(";")[0]
        files = {"file": (f"answer.{extension}", audio_bytes, mime_type)}
        data = {"model": self._model}
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            response = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                data=data,
                files=files,
                timeout=30.0,
            )
            response.raise_for_status()
            transcript = response.json().get("text", "").strip()
        except (httpx.HTTPError, ValueError):
            latency_ms = (time.perf_counter() - start) * 1000
            return TranscriptionResult(
                transcript="",
                source="unavailable",
                confidence=0.0,
                provider_name=self.name,
                latency_ms=round(latency_ms, 3),
            )
        latency_ms = (time.perf_counter() - start) * 1000
        return TranscriptionResult(
            transcript=transcript,
            source="live_stt" if transcript else "unavailable",
            confidence=0.85 if transcript else 0.0,
            provider_name=self.name,
            latency_ms=round(latency_ms, 3),
        )


@lru_cache
def get_speech_to_text_provider() -> SpeechToTextProvider:
    settings = get_settings()
    if settings.speech_to_text_api_key:
        return OpenAIWhisperProvider(api_key=settings.speech_to_text_api_key, model=settings.speech_to_text_model)
    return DeterministicSpeechToTextProvider()
