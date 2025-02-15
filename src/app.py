# === Standard Libraries ===
import os
import sys
import threading
from datetime import datetime
from queue import Queue
import time

# === Custom Modules ===
from module_config import load_config
from module_character import CharacterManager
from module_memory import MemoryManager
from module_stt import STTManager
from module_tts import update_tts_settings
from module_btcontroller import *
from module_main import initialize_managers, wake_word_callback, utterance_callback, post_utterance_callback, start_bt_controller_thread, start_discord_bot, process_discord_message_callback, initialize_ui  
from module_vision import initialize_blip
from module_llm import initialize_manager_llm
from module_ui import UIManager

# === Constants and Globals ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)
sys.path.append(os.getcwd())
CONFIG = load_config()

# Create global UI manager instance
ui_manager = None

# === Helper Functions ===
def init_app():
    """
    Performs initial setup for the application
    """
    global ui_manager
    
    print(f"LOAD: Script running from: {BASE_DIR}")
    ui_manager.update_data("System", f"Script running from: {BASE_DIR}", "INFO")
    
    print(f"DEBUG: init_app() called")
    ui_manager.update_data("System", "Initializing application...", "DEBUG")
    
    # Load the configuration
    CONFIG = load_config()
    if CONFIG['TTS']['ttsoption'] == 'xttsv2':
        ui_manager.update_data("System", "TTS settings updated", "INFO")

def start_discord_in_thread():
    """
    Start the Discord bot in a separate thread to prevent blocking.
    """
    discord_thread = threading.Thread(target=start_discord_bot, args=(process_discord_message_callback,), daemon=True)
    discord_thread.start()
    print("INFO: Discord bot started in a separate thread.")
    ui_manager.update_data("System", "Discord bot started in separate thread", "INFO")

# === Main Application Logic ===
if __name__ == "__main__":
    # Initialize UI Manager first
    ui_manager = UIManager()
    #ui_manager.start()
    ui_manager.update_data("System", "UI Manager initialized", "SYSTEM")
    initialize_ui(ui_manager)
    # Perform initial setup
    init_app()
    
    # Create a shutdown event for global threads
    shutdown_event = threading.Event()
    
    try:
        # Initialize CharacterManager, MemoryManager
        char_manager = CharacterManager(config=CONFIG)
        ui_manager.update_data("System", f"Character Manager initialized: {char_manager.char_name}", "SYSTEM")
        
        memory_manager = MemoryManager(config=CONFIG, char_name=char_manager.char_name, char_greeting=char_manager.char_greeting)
        ui_manager.update_data("Memory", "Memory Manager initialized", "SYSTEM")
        
        # Initialize STTManager
        stt_manager = STTManager(config=CONFIG, shutdown_event=shutdown_event)
        stt_manager.set_wake_word_callback(wake_word_callback)
        stt_manager.set_utterance_callback(utterance_callback)
        stt_manager.set_post_utterance_callback(post_utterance_callback)
        ui_manager.update_data("STT", "STT Manager initialized", "SYSTEM")
        
        # DISCORD Callback
        if CONFIG['DISCORD']['enabled'] == 'True':
            start_discord_in_thread()
        
        # Pass managers to main module
        initialize_managers(memory_manager, char_manager, stt_manager)
        initialize_manager_llm(memory_manager, char_manager)
        
        # Start necessary threads
        bt_controller_thread = threading.Thread(target=start_bt_controller_thread, name="BTControllerThread", daemon=True)
        bt_controller_thread.start()
        ui_manager.update_data("System", "Bluetooth controller thread started", "SYSTEM")
        
        # Initialize BLIP to speed up initial image capture
        if not CONFIG['VISION']['server_hosted']:
            initialize_blip()
            ui_manager.update_data("System", "BLIP initialized", "SYSTEM")
        
        print(f"LOAD: TARS-AI v1.01 running.")
        ui_manager.update_data("System", "TARS-AI v1.01 running", "SYSTEM")
        
        # Start the STT thread
        stt_manager.start()
        ui_manager.update_data("STT", "STT Manager started", "SYSTEM")
        
        while not shutdown_event.is_set():
            time.sleep(0.1)  # Sleep to reduce CPU usage
            
    except KeyboardInterrupt:
        print(f"INFO: Stopping all threads and shutting down executor...")
        ui_manager.update_data("System", "Shutting down...", "SYSTEM")
        shutdown_event.set()  # Signal global threads to shutdown
        ui_manager.stop()  # Stop the UI thread
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        ui_manager.update_data("System", f"Error: {str(e)}", "ERROR")
        shutdown_event.set()
        ui_manager.stop()
        
    finally:
        stt_manager.stop()
        bt_controller_thread.join()
        ui_manager.join()  # Wait for the UI thread to finish
        print(f"INFO: All threads and executor stopped gracefully.")