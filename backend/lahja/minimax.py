"""MiniMax TTS + voice cloning client."""
from __future__ import annotations

import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://api.minimax.io/v1"


class MiniMaxError(RuntimeError):
    pass


class MiniMaxClient:
    def __init__(self, api_key: str, group_id: str,
                tts_model: str = "speech-2.8-turbo") -> None:
        self.api_key = api_key
        self.group_id = group_id
        self.tts_model = tts_model

    # ------------------------------------------------------------------
    def _headers(self, json_content: bool = True) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if json_content:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _check(data: dict, action: str) -> dict:
        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code", 0) != 0:
            raise MiniMaxError(f"MiniMax {action} failed: {base_resp}")
        return data

    # ------------------------------------------------------------------
    def list_voices(self) -> dict:
        response = requests.post(
            f"{API_BASE}/get_voice",
            headers=self._headers(),
            json={"voice_type": "all"},
            timeout=60,
        )
        response.raise_for_status()
        return self._check(response.json(), "voice list")

    def voice_exists(self, voice_id: str) -> bool:
        try:
            data = self.list_voices()
        except Exception as exc:  # noqa: BLE001 - never block on the existence check
            logger.warning("Could not list voices (%s); will attempt clone.", exc)
            return False
        for entry in data.get("voice_cloning", []) or []:
            if entry.get("voice_id") == voice_id:
                return True
        return False

    # ------------------------------------------------------------------
    def upload_clone_sample(self, audio_path: Path) -> int:
        if not audio_path.exists():
            raise FileNotFoundError(f"Clone sample not found: {audio_path}")
        with audio_path.open("rb") as handle:
            response = requests.post(
                f"{API_BASE}/files/upload?GroupId={self.group_id}",
                headers=self._headers(json_content=False),
                data={"purpose": "voice_clone"},
                files={"file": (audio_path.name, handle, "audio/mpeg")},
                timeout=300,
            )
        response.raise_for_status()
        data = self._check(response.json(), "file upload")
        file_id = data.get("file", {}).get("file_id")
        if not file_id:
            raise MiniMaxError(f"No file_id returned from upload: {data}")
        # Keep the API's native type: /voice_clone expects file_id as a
        # NUMBER and rejects a string with 2013 "invalid params".
        return file_id

    def clone_voice(self, file_id: int, voice_id: str) -> str:
        response = requests.post(
            f"{API_BASE}/voice_clone?GroupId={self.group_id}",
            headers=self._headers(),
            json={"file_id": file_id, "voice_id": voice_id},
            timeout=300,
        )
        response.raise_for_status()
        self._check(response.json(), "voice clone")
        return voice_id

    def ensure_cloned_voice(self, sample_path: Path, voice_id: str) -> str:
        """Clone once; reuse the existing cloned voice on later runs."""
        if self.voice_exists(voice_id):
            logger.info("Cloned voice '%s' already exists - skipping upload/clone.",
                        voice_id)
            return voice_id
        logger.info("Uploading clone sample %s ...", sample_path.name)
        file_id = self.upload_clone_sample(sample_path)
        logger.info("Cloning voice '%s' ...", voice_id)
        return self.clone_voice(file_id, voice_id)

    # ------------------------------------------------------------------
    def synthesize(self, text: str, voice_id: str, output_path: Path,
                speed: float = 1.0, sample_rate: int = 32000) -> Path:
        if not text.strip():
            raise ValueError("Cannot generate audio from empty text.")
        payload = {
            "model": self.tts_model,
            "text": text,
            "stream": False,
            "language_boost": "auto",
            "output_format": "hex",
            "voice_setting": {
                "voice_id": voice_id,
                "speed": speed,
                "vol": 1,
                "pitch": 0,
            },
            "audio_setting": {
                "sample_rate": sample_rate,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1,
            },
        }
        response = requests.post(
            f"{API_BASE}/t2a_v2?GroupId={self.group_id}",
            headers=self._headers(),
            json=payload,
            timeout=180,
        )
        response.raise_for_status()
        data = self._check(response.json(), "TTS")
        audio_hex = data.get("data", {}).get("audio")
        if not audio_hex:
            raise MiniMaxError(f"MiniMax response did not contain audio: {data}")
        output_path.write_bytes(bytes.fromhex(audio_hex))
        if output_path.stat().st_size == 0:
            raise MiniMaxError(f"Generated audio is empty: {output_path}")
        return output_path