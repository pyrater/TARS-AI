import sounddevice as sd
import soundfile as sf
from io import BytesIO
from piper.voice import PiperVoice
import asyncio
import wave
import re
import os
import ctypes
import torch
import torchaudio
from pydub import AudioSegment, effects

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

# Load the Piper model globally
script_dir = os.path.dirname(__file__)
model_path = os.path.join(script_dir, 'tts/TARS.onnx')

if CONFIG['TTS']['ttsoption'] == 'piper':
    voice = PiperVoice.load(model_path)

if CONFIG['TTS']['ttsoption'] == 'silero':
    device = torch.device("cpu")
    model, example_texts = torch.hub.load(repo_or_dir="snakers4/silero-models",
                                      model="silero_tts",
                                      language="en",
                                      speaker="v3_en")
    sample_rate = 24000
    speaker = "en_2"


async def synthesize(voice, chunk, sample_rate=48000, length_scale=1.0, noise_scale=0.667, noise_w=0.8):
    """
    Synthesize a chunk of text into a BytesIO buffer with improved audio processing.
    """
    wav_buffer = BytesIO()

    try:
        # Generate speech
        temp_buffer = BytesIO()
        with wave.open(temp_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit samples
            wav_file.setframerate(sample_rate)  # Set sample rate

            # Check if the synthesize function is async and await it
            if callable(getattr(voice, "synthesize", None)):
                result = voice.synthesize(chunk, wav_file, length_scale=length_scale, noise_scale=noise_scale, noise_w=noise_w)
                if result.__class__.__name__ == "coroutine":
                    await result
            else:
                raise TypeError("voice.synthesize is not callable")

        temp_buffer.seek(0)

        # Convert to a higher-quality format using pydub
        audio = AudioSegment.from_wav(temp_buffer)
        audio = audio.set_frame_rate(sample_rate).set_sample_width(2).set_channels(1)
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)

    except TypeError as e:
        print(f"ERROR: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

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

async def text_to_speech_with_pipelining(text):
    """
    Converts text to speech using the specified Piper model and streams audio playback with pipelining.
    """
    # Split text into smaller chunks
    chunks = re.split(r'(?<=\.)\s', text)  # Split at sentence boundaries

    # Process and play chunks sequentially
    for chunk in chunks:
        if chunk.strip():  # Ignore empty chunks
            wav_buffer = await synthesize(voice, chunk.strip())
            await play_audio(wav_buffer)




async def text_to_speech_with_pipelining_silero(text):
    """
    Converts text to speech, applies deeper & faster effects, and plays the audio.
    """
    chunks = re.split(r'(?<=\.)\s', text)

    for chunk in chunks:
        if chunk.strip():
            audio_tensor = model.apply_tts(text=chunk.strip(), speaker=speaker, sample_rate=sample_rate)
            audio_np = audio_tensor.numpy()
            wav_buffer = BytesIO()
            sf.write(wav_buffer, audio_np, sample_rate, format="WAV")
            wav_buffer.seek(0)
            audio = AudioSegment.from_wav(wav_buffer)
            audio = apply_tars_effects(audio, sample_rate)
            processed_wav = BytesIO()
            audio.export(processed_wav, format="wav")
            processed_wav.seek(0)

            await play_audio(processed_wav)

            

def apply_tars_effects(audio, sample_rate):
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