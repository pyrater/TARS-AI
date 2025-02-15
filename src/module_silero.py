"""
Enhanced Silero TTS with TARS Effects, Audio Normalization, and Better Playback
"""

import wave
import sounddevice as sd
import soundfile as sf
from io import BytesIO
import torch
import torchaudio
import asyncio
import re
import ctypes
import os
from pydub import AudioSegment, effects

# Set relative path for model storage
model_dir = os.path.join(os.path.dirname(__file__), "stt")  # Relative to script location
torch.hub.set_dir(model_dir)  # Set PyTorch hub directory

# === Custom Modules ===
from module_config import load_config
CONFIG = load_config()

# Define the error handler function type
ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
    None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p
)

# Define the custom error handler function
def py_error_handler(filename, line, function, err, fmt):
    pass  # Suppress the error message

# Create a C-compatible function pointer
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

# Load the ALSA library
asound = ctypes.cdll.LoadLibrary('libasound.so')

# Load Silero model globally
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if CONFIG['TTS']['ttsoption'] == 'silero':
    model, example_texts = torch.hub.load(
        repo_or_dir="snakers4/silero-models",
        model="silero_tts",
        language="en",
        speaker="v3_en"  # Model version, not speaker ID
    )
    model.to(device)
    sample_rate = 24000  # Set to Silero's recommended sample rate
    speaker = "en_2"  # Use a valid speaker ID

def apply_tars_effects(audio):
    """
    Apply TARS-like effects: pitch change, speed up, reverb, and echo.
    """
    lower_rate = int(sample_rate * 0.88)
    audio = audio._spawn(audio.raw_data, overrides={"frame_rate": lower_rate})
    audio = audio.set_frame_rate(sample_rate)
    audio = audio.speedup(playback_speed=1.42)
    reverb_decay = -2
    delay_ms = 3
    echo1 = audio - reverb_decay
    echo2 = echo1 - 1
    audio = audio.overlay(echo1, position=delay_ms)
    audio = audio.overlay(echo2, position=delay_ms * 1)
    return audio

async def synthesize(text):
    """
    Synthesize a chunk of text into an AudioSegment using Silero TTS.
    """
    with torch.no_grad():
        audio_tensor = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)

    # Convert tensor to WAV buffer
    wav_buffer = BytesIO()
    torchaudio.save(wav_buffer, audio_tensor.unsqueeze(0), sample_rate, format="wav")
    wav_buffer.seek(0)

    # Load audio into Pydub
    audio = AudioSegment.from_file(wav_buffer, format="wav")
    audio = apply_tars_effects(audio)  # Apply TARS-like effects
    return audio

async def play_audio(audio):
    """
    Play audio from a Pydub AudioSegment.
    """
    wav_buffer = BytesIO()
    audio.export(wav_buffer, format="wav")
    wav_buffer.seek(0)

    data, samplerate = sf.read(wav_buffer, dtype='float32')
    # Set the custom error handler
    asound.snd_lib_error_set_handler(c_error_handler)
    sd.play(data, samplerate)
    await asyncio.sleep(len(data) / samplerate)  # Wait until playback finishes
    # Reset to the default error handler
    asound.snd_lib_error_set_handler(None)

async def text_to_speech_with_pipelining_silero(text):
    """
    Converts text to speech using Silero TTS, applies TARS effects, and streams playback.
    """
    # Split text into smaller chunks
    chunks = re.split(r'(?<=\.)\s', text)  # Split at sentence boundaries

    # Process and play chunks sequentially
    for chunk in chunks:
        if chunk.strip():  # Ignore empty chunks
            audio = await synthesize(chunk.strip())
            await play_audio(audio)