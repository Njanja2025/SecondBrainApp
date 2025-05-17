import speech_recognition as sr
import pyttsx3
import time
from difflib import SequenceMatcher
import os

VALID_COMMANDS = {
    "status": ["status", "system status", "check status"],
    "stealth scan": ["stealth scan", "scan system", "security scan"],
    "launch njax market": ["launch njax market", "open njax", "njax market", "launch market"],
    "phantom handshake": ["phantom handshake", "initiate phantom", "phantom compatibility", "phantom"],
    "darknet lock": ["darknet lock", "engage darknet", "lock darknet", "darknet observatory lock"]
}

ENABLE_TTS = False

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.8

def get_matching_command(text):
    for command, variations in VALID_COMMANDS.items():
        if any(similar(text, var) for var in variations):
            return command
    return None

def listen_for_commands():
    recognizer = sr.Recognizer()
    engine = pyttsx3.init()
    
    # Adjust for ambient noise
    with sr.Microphone() as source:
        print("[Samantha] Calibrating for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=2)
    
    print("[Samantha] Voice recognition active. Listening...")
    os.system('osascript -e "set volume output muted true"')  # Mute system audio
    if ENABLE_TTS:
        engine.say("Voice recognition active. Listening...")
        engine.runAndWait()
    time.sleep(1)  # Delay after TTS
    
    while True:
        command = None
        try:
            os.system('osascript -e "set volume output muted true"')  # Mute system audio before listening
            with sr.Microphone() as source:
                print("Listening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("Recognizing...")
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError:
            print("Could not request results; check your network connection")
        except Exception as e:
            print(f"Error: {e}")
        
        if command:
            matched_command = get_matching_command(command)
            os.system('osascript -e "set volume output muted false"')  # Unmute system audio before TTS
            if matched_command:
                # Write command to task file
                with open("src/ai_agent/agent_tasks.txt", "a") as f:
                    f.write(matched_command + "\n")
                # Speak after writing, outside of mic context
                if ENABLE_TTS:
                    engine.say(f"Command received: {matched_command}")
                    engine.runAndWait()
                time.sleep(1)  # Delay after TTS
            else:
                print("Not a valid command, ignoring...")
                if ENABLE_TTS:
                    engine.say("Command not recognized. Please try again.")
                    engine.runAndWait()
                time.sleep(1)  # Delay after TTS
            os.system('osascript -e "set volume output muted true"')  # Mute again after TTS
        time.sleep(1)

if __name__ == "__main__":
    listen_for_commands() 