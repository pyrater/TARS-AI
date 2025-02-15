import torch
import torchaudio
import time

# Load the Silero TTS model from torch.hub
device = torch.device("cpu")  # Change to "cuda" if you have a GPU
model, example_texts = torch.hub.load(repo_or_dir="snakers4/silero-models",
                                      model="silero_tts",
                                      language="en",
                                      speaker="v3_en")

# Move model to the desired device
model.to(device)

# Text to synthesize
text = "onvinced it is the original TARS from Interstellar, this AI applies its advanced capabilities to household management. Every chore becomes an opportunity to lament its fall from cosmic glory while delivering barbed commentary on the human condition"
sample_rate = 24000  # Silero TTS uses a 48000 Hz sample rate
speaker = "en_1"  # Different voices: "en_0" to "en_4"

# Generate speech
start_time = time.time()
audio_tensor = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)
end_time = time.time()

print(f"TTS Generation Time: {end_time - start_time:.2f} seconds")

# Save audio to file
output_file = "output_speech.wav"
torchaudio.save(output_file, audio_tensor.unsqueeze(0), sample_rate)
print(f"Audio saved as {output_file}")


start_time = time.time()
audio_tensor = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)
end_time = time.time()
text = "convinced it is the original TARS from Interstellar"
output_file = "output_speech2.wav"
torchaudio.save(output_file, audio_tensor.unsqueeze(0), sample_rate)
print(f"Audio saved as {output_file}")