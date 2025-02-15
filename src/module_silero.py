"""
Contribution from atomikspace for Silero TTS
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
    speaker = "en_1"  # Use a valid speaker ID

async def synthesize(text):
    """
    Synthesize a chunk of text into a BytesIO buffer using Silero TTS.
    """
    with torch.no_grad():
        audio_tensor = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)

    # Convert tensor to WAV buffer
    wav_buffer = BytesIO()
    torchaudio.save(wav_buffer, audio_tensor.unsqueeze(0), sample_rate, format="wav")
    wav_buffer.seek(0)
    return wav_buffer

async def play_audio(wav_buffer):
    """
    Play audio from a BytesIO buffer.
    """
    data, samplerate = sf.read(wav_buffer, dtype='float32')
    # Set the custom error handler
    asound.snd_lib_error_set_handler(c_error_handler)
    sd.play(data, samplerate)
    await asyncio.sleep(len(data) / samplerate)  # Wait until playback finishes
    # Reset to the default error handler
    asound.snd_lib_error_set_handler(None)

async def text_to_speech_with_pipelining_silero(text):
    """
    Converts text to speech using Silero TTS and streams audio playback with pipelining.
    """
    # Split text into smaller chunks
    chunks = re.split(r'(?<=\.)\s', text)  # Split at sentence boundaries

    # Process and play chunks sequentially
    for chunk in chunks:
        if chunk.strip():  # Ignore empty chunks
            wav_buffer = await synthesize(chunk.strip())
            await play_audio(wav_buffer)