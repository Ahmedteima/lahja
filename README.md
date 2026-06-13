# lahja

Replace a video's narration with a **cloned AI voice** — keeping the original
timing, intro/outro music, and pauses between sentences.

The speaker's voice is cloned from the video's own audio (MiniMax voice
cloning), the transcript is optionally polished by an LLM (fixes misheard
names and grammar without changing meaning), and the new voiceover is laid
back onto the original timeline so the result stays in sync with the video.

## Pipeline

```
video.mp4
  │ 1. ffmpeg          extract mono 16 kHz audio
  │ 2. Whisper         transcribe with word-level timestamps
  │ 3. LLM (optional)  fix transcription errors (NVIDIA NIM, batched)
  │ 4. MiniMax         clone the speaker's voice from a 45 s sample
  │ 5. MiniMax TTS     synthesize each segment with the cloned voice
  │ 6. timeline build  one global tempo (stable speed), original audio
  │                    kept in every gap (intro / pauses / outro)
  │ 7. ffmpeg          merge the new audio into the video
  ▼
video_voiceover.mp4
```

Key behaviours:

- **Stable speaking speed** — one global tempo factor for the whole video;
  segments may deviate at most ±8 % from it.
- **Intro/outro & background preserved** — non-speech intervals are copied
  from the original audio, not replaced with silence.
- **Ease-in** — the opening line starts slightly slower, then the voice
  returns to normal speed.
- **Safe refinement** — the LLM step can only fix clear mistakes; anything
  suspicious falls back to the raw Whisper text. No key? The step is skipped.
- **One-time cloning** — the cloned voice id is derived from the video file's
  hash, so re-processing the same video reuses the existing clone.

## Requirements

- Python ≥ 3.10
- **FFmpeg** (the program) on PATH — `winget install Gyan.FFmpeg`
- A CUDA GPU is strongly recommended for Whisper
- API keys:
  - [MiniMax](https://www.minimax.io) — TTS + voice cloning (required)
  - [NVIDIA NIM](https://build.nvidia.com) — transcript refinement (optional)

## Install

```bash
git clone <this repo>
cd lahja

python -m venv .venv
.venv\Scripts\activate            # Windows

# PyTorch first, with the right CUDA build for your machine:
pip install torch --index-url https://download.pytorch.org/whl/cu124

pip install -e .
```

Configure credentials:

```bash
copy .env.example .env            # then edit .env with your real keys
```

`.env` is gitignored. In production, set `MINIMAX_API_KEY`,
`MINIMAX_GROUP_ID` and `NVIDIA_API_KEY` as real environment variables.

## Usage

### Command line

```bash
lahja "lecture.mp4"
# -> lecture_voiceover.mp4

lahja "lecture.mp4" -o result.mp4 --no-refine --keep-workdir -v
```

### Python (e.g. from a web backend)

```python
from lahja import process_video

final = process_video("uploads/lecture.mp4", "results/lecture_voiceover.mp4")
```

`process_video` is self-contained per call: it creates its own temporary
working directory and cleans it up, so concurrent jobs don't collide.
For a server, note that the first call loads the Whisper model (slow);
it stays cached for subsequent calls in the same process.

## Costs & notes

- Voice cloning is charged by MiniMax on the **first synthesis** with a new
  cloned voice; re-running the same video reuses the clone for free.
- Background music *underneath* speech is replaced together with the speech
  (separating it would require source separation, e.g. Demucs).
- Clone samples must be 10 s – 5 min; the pipeline cuts a 45 s slice from
  the start of the video's audio (configurable in `Settings`).
