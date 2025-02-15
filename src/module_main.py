# === Standard Libraries ===
import os
import threading
import json
import re
import concurrent.futures
import sys
import time

# === Custom Modules ===
from module_config import load_config
from module_btcontroller import start_controls
from module_tts import generate_tts_audio
from module_discord import *
from module_llm import process_completion
from module_ui import UIManager

# === Constants and Globals ===
character_manager = None
memory_manager = None
stt_manager = None
ui_manager = None

CONFIG = load_config()

# Global Variables (if needed)
stop_event = threading.Event()
executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)

def initialize_ui(ui_mgr):
    """
    Initialize the UI manager reference.
    
    Parameters:
    - ui_mgr: The UIManager instance from app.py
    """
    global ui_manager
    ui_manager = ui_mgr

# === Threads ===
def start_bt_controller_thread():
    """
    Wrapper to start the BT Controller functionality in a thread.
    """
    try:
        print(f"LOAD: Starting BT Controller thread...")
        ui_manager.update_data("BT Controller", "Starting controller thread", "INFO")
        while not stop_event.is_set():
            start_controls()
    except Exception as e:
        error_msg = f"BT Controller error: {e}"
        print(f"ERROR: {error_msg}")
        ui_manager.update_data("BT Controller", error_msg, "ERROR")

def stream_text_nonblocking(text, delay=0.03):
    """
    Streams text character by character in a non-blocking way.
    """
    # Log to UI console after complete message
    if text.startswith("USER: "):
        ui_manager.update_data("Chat", text, "INFO")
    elif text.startswith("TARS: "):
        ui_manager.update_data("Chat", text, "SYSTEM")

    def stream():
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        
        if not text.endswith("\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()

    threading.Thread(target=stream, daemon=True).start()

def process_discord_message_callback(user_message):
    """
    Processes the user's message and generates a response.
    """
    try:
        match = re.match(r"<@(\d+)> ?(.*)", user_message)
        if match:
            mentioned_user_id = match.group(1)
            message_content = match.group(2).strip()
            ui_manager.update_data("Discord", f"Message from {mentioned_user_id}: {message_content}", "INFO")

        reply = process_completion(message_content)
        ui_manager.update_data("Discord", f"TARS Reply: {reply}", "SYSTEM")
        
    except Exception as e:
        error_msg = f"Discord processing error: {e}"
        print(f"ERROR: {error_msg}")
        ui_manager.update_data("Discord", error_msg, "ERROR")

    return reply

def wake_word_callback(wake_response):
    """
    Play initial response when wake word is detected.
    """
    ui_manager.update_data("Wake Word", "Wake word detected", "INFO")
    generate_tts_audio(wake_response, CONFIG['TTS']['ttsoption'], CONFIG['TTS']['azure_api_key'], 
                      CONFIG['TTS']['azure_region'], CONFIG['TTS']['ttsurl'], 
                      CONFIG['TTS']['toggle_charvoice'], CONFIG['TTS']['tts_voice'])
    

def utterance_callback(message):
    """
    Process the recognized message from STTManager.
    """
    try:
        message_dict = json.loads(message)
        if not message_dict.get('text'):
            return
        
        stream_text_nonblocking(f"USER: {message_dict['text']}")

        if "shutdown pc" in message_dict['text'].lower():
            shutdown_msg = "Shutting down the PC..."
            print(f"SHUTDOWN: {shutdown_msg}")
            ui_manager.update_data("System", shutdown_msg, "SYSTEM")
            os.system('shutdown /s /t 0')
            return

        reply = process_completion(message_dict['text'])

        try:
            match = re.search(r"<think>(.*?)</think>", reply, re.DOTALL)
            thoughts = match.group(1).strip() if match else ""
            reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
            
            if thoughts:
                ui_manager.update_data("Thoughts", thoughts, "DEBUG")
        except Exception:
            thoughts = ""

        stream_text_nonblocking(f"TARS: {reply}")
        reply = re.sub(r'[^a-zA-Z0-9\s.,?!;:"\'-]', '', reply)
        
        generate_tts_audio(
            reply,
            CONFIG['TTS']['ttsoption'],
            CONFIG['TTS']['azure_api_key'],
            CONFIG['TTS']['azure_region'],
            CONFIG['TTS']['ttsurl'],
            CONFIG['TTS']['toggle_charvoice'],
            CONFIG['TTS']['tts_voice']
        )

    except json.JSONDecodeError:
        error_msg = "Invalid JSON format. Could not process user message."
        print(f"ERROR: {error_msg}")
        ui_manager.update_data("JSON", error_msg, "ERROR")
    except Exception as e:
        error_msg = f"Error processing message: {e}"
        print(f"ERROR: {error_msg}")
        ui_manager.update_data("Processing", error_msg, "ERROR")

def post_utterance_callback():
    """
    Restart listening for another utterance after handling the current one.
    """
    global stt_manager
    ui_manager.update_data("STT", "Ready for next utterance", "INFO")
    stt_manager._transcribe_utterance()

# === Initialization ===
def initialize_managers(mem_manager, char_manager, stt_mgr):
    """
    Pass in the shared instances for managers.
    """
    global memory_manager, character_manager, stt_manager
    memory_manager = mem_manager
    character_manager = char_manager
    stt_manager = stt_mgr
    ui_manager.update_data("System", "All managers initialized", "SYSTEM")