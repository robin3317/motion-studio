"""Shared helpers for motion-studio scripts (stdlib only)."""
import json
import os
import shutil
import subprocess
import sys


def which(name):
    """Return the executable path for name, honouring MS_FFMPEG / MS_FFPROBE overrides."""
    env = {"ffmpeg": "MS_FFMPEG", "ffprobe": "MS_FFPROBE"}.get(name)
    if env and os.environ.get(env):
        return os.environ[env]
    return shutil.which(name)


def run(cmd, check=True, capture=True, timeout=None):
    """Run a command list and return CompletedProcess (text mode)."""
    return subprocess.run(cmd, check=check, capture_output=capture, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def need(name):
    path = which(name)
    if not path:
        sys.exit(f"[motion-studio] '{name}' not found on PATH. Run scripts/preflight.py and see references/setup.md.")
    return path


def ffprobe_json(path):
    out = run([need("ffprobe"), "-v", "error", "-show_format", "-show_streams", "-of", "json", path]).stdout
    return json.loads(out)


def decode_audio(path, sr=48000, channels=2):
    """Decode any audio/video file to float32 numpy array shape (n, channels) via ffmpeg."""
    import numpy as np
    cmd = [need("ffmpeg"), "-v", "error", "-i", path, "-vn", "-f", "f32le",
           "-acodec", "pcm_f32le", "-ac", str(channels), "-ar", str(sr), "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    data = np.frombuffer(raw, dtype=np.float32)
    return data.reshape(-1, channels).copy()


def write_wav(path, data, sr=48000):
    """Write float array (n, ch) or (n,) to 16-bit PCM WAV with the stdlib wave module."""
    import numpy as np
    import wave
    a = np.asarray(data, dtype=np.float32)
    if a.ndim == 1:
        a = a[:, None]
    a = np.clip(a, -1.0, 1.0)
    pcm = (a * 32767.0).astype("<i2")
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(a.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def db_to_gain(db):
    return 10.0 ** (db / 20.0)


def dump(obj, path=None):
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    return text
