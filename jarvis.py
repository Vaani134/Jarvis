import speech_recognition as sr
import pyttsx3
import requests
import json
import threading
import time
import os
from datetime import datetime
import webbrowser
import subprocess
import sys
import openai

class JARVIS:
    def __init__(self):
        # Initialize speech recognition and text-to-speech
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        
        # OpenRouter API configuration
        self.api_key = "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"  # Replace with your actual API key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Language settings
        self.current_language = "en"  # Default to English
        self.languages = {
            "english": {"code": "en", "voice": "english"},
            "hindi": {"code": "hi", "voice": "hindi"},
            "chinese": {"code": "zh", "voice": "chinese"},
            "japanese": {"code": "ja", "voice": "japanese"},
            "russian": {"code": "ru", "voice": "russian"},
            "spanish": {"code": "es", "voice": "spanish"}
        }
        
        # Voice settings
        self.setup_voice()
        
        # Conversation history
        self.conversation_history = []
        
        # Wake word
        self.wake_word = "jarvis"
        self.listening = False
        
        print("JARVIS is initializing...")
        self.speak("Hello! I am JARVIS, your personal AI assistant. I can communicate in multiple languages including English, Hindi, Chinese, Japanese, Russian, and Spanish.")
        print("JARVIS is ready! Say 'Hey JARVIS' to activate me.")

    def setup_voice(self):
        """Setup text-to-speech voice properties"""
        voices = self.tts_engine.getProperty('voices')
        self.tts_engine.setProperty('rate', 150)  # Speed of speech
        self.tts_engine.setProperty('volume', 0.9)  # Volume level
        
        # Set voice (use first available voice)
        if voices:
            self.tts_engine.setProperty('voice', voices[0].id)

    def speak(self, text):
        """Convert text to speech"""
        print(f"JARVIS: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self):
        """Listen for audio input and convert to text"""
        try:
            with self.microphone as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("Processing speech...")
            
            # Try to recognize speech in current language
            if self.current_language == "en":
                text = self.recognizer.recognize_google(audio, language="en-US")
            elif self.current_language == "hi":
                text = self.recognizer.recognize_google(audio, language="hi-IN")
            elif self.current_language == "zh":
                text = self.recognizer.recognize_google(audio, language="zh-CN")
            elif self.current_language == "ja":
                text = self.recognizer.recognize_google(audio, language="ja-JP")
            elif self.current_language == "ru":
                text = self.recognizer.recognize_google(audio, language="ru-RU")
            elif self.current_language == "es":
                text = self.recognizer.recognize_google(audio, language="es-ES")
            else:
                text = self.recognizer.recognize_google(audio)
            
            return text.lower()
        
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return None
        except sr.WaitTimeoutError:
            return None

    def call_openrouter_api(self, message):
        """Make API call to OpenRouter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",  # Optional: for OpenRouter analytics
            "X-Title": "JARVIS Assistant"  # Optional: for OpenRouter analytics
        }
        
        # Add language instruction to the system prompt
        language_instruction = self.get_language_instruction()
        
        # Prepare conversation with system message
        messages = [
            {
                "role": "system", 
                "content": f"You are JARVIS, a helpful AI assistant. {language_instruction} Keep responses concise and helpful. You can help with general questions, provide information, tell time, open applications, and have conversations."
            }
        ]
        
        # Add conversation history (last 10 messages to avoid token limits)
        messages.extend(self.conversation_history[-10:])
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": "anthropic/claude-3.5-sonnet",  # You can change this to other models
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            assistant_message = result['choices'][0]['message']['content']
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return "I'm sorry, I'm having trouble connecting to my knowledge base right now."
        except KeyError as e:
            print(f"Response parsing error: {e}")
            return "I received an unexpected response format."

    def get_language_instruction(self):
        """Get language-specific instruction for the AI"""
        instructions = {
            "en": "Respond in English.",
            
            "hi": "Respond in English.",
            "zh": "Respond in English.",
            "ja": "Respond in English.",
            "ru": "Respond in English.",
            "es": "Respond in English."
        }
        return instructions.get(self.current_language, "Respond in English.")

    def change_language(self, command):
        """Change the current language"""
        for lang_name, lang_info in self.languages.items():
            if lang_name in command:
                self.current_language = lang_info["code"]
                self.speak(f"Language changed to {lang_name.capitalize()}")
                return True
        return False

    def handle_system_commands(self, command):
        """Handle system-level commands"""
        command = command.lower()
        
        # Language change commands
        if "change language" in command or "switch language" in command:
            return self.change_language(command)
        
        # Time command
        if "what time" in command or "current time" in command:
            current_time = datetime.now().strftime("%I:%M %p")
            response = f"The current time is {current_time}"
            self.speak(response)
            return True
        
        # Date command
        if "what date" in command or "today's date" in command:
            current_date = datetime.now().strftime("%B %d, %Y")
            response = f"Today's date is {current_date}"
            self.speak(response)
            return True
        
        # Open applications
        if "open" in command:
            if "browser" in command or "chrome" in command:
                webbrowser.open("https://www.google.com")
                self.speak("Opening web browser")
                return True
            elif "notepad" in command:
                try:
                    subprocess.run(["notepad.exe"])
                    self.speak("Opening Notepad")
                except:
                    self.speak("I couldn't open Notepad")
                return True
            elif "calculator" in command:
                try:
                    subprocess.run(["calc.exe"])
                    self.speak("Opening Calculator")
                except:
                    self.speak("I couldn't open Calculator")
                return True
        
        # Exit commands
        if any(word in command for word in ["goodbye", "exit", "quit", "stop", "shutdown"]):
            self.speak("Goodbye! It was nice talking to you.")
            return "exit"
        
        return False

    def process_command(self, command):
        """Process user command"""
        if not command:
            return
        
        print(f"You said: {command}")
        
        # Handle system commands first
        system_result = self.handle_system_commands(command)
        if system_result == "exit":
            return "exit"
        elif system_result:
            return
        
        # If not a system command, send to OpenRouter API
        response = self.call_openrouter_api(command)
        self.speak(response)

    def continuous_listen(self):
        """Continuously listen for wake word and commands"""
        print("Starting continuous listening mode...")
        
        while True:
            try:
                # Listen for wake word
                if not self.listening:
                    audio_input = self.listen()
                    if audio_input and self.wake_word in audio_input:
                        self.speak("Yes, how can I help you?")
                        self.listening = True
                        continue
                
                # If in listening mode, process commands
                if self.listening:
                    command = self.listen()
                    if command:
                        result = self.process_command(command)
                        if result == "exit":
                            break
                    else:
                        # If no command heard, stop listening after a few seconds
                        self.listening = False
                        print("Listening timeout. Say 'Hey JARVIS' to activate me again.")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\nShutting down JARVIS...")
                self.speak("Goodbye!")
                break
            except Exception as e:
                print(f"Error in continuous listen: {e}")
                time.sleep(1)

    def run(self):
        """Main run method"""
        try:
            self.continuous_listen()
        except Exception as e:
            print(f"Error running JARVIS: {e}")
            self.speak("I encountered an error and need to shut down.")

def install_requirements():
    """Install required packages"""
    required_packages = [
        "speechrecognition",
        "pyttsx3",
        "requests",
        "pyaudio"
    ]
    
    print("Installing required packages...")
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f" {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f" Failed to install {package}")
            if package == "pyaudio":
                print("For PyAudio installation issues, try:")
                print("Windows: pip install pipwin && pipwin install pyaudio")
                print("macOS: brew install portaudio && pip install pyaudio")
                print("Linux: sudo apt-get install python3-pyaudio")

if __name__ == "__main__":
    print("=" * 50)
    print("JARVIS - Multilingual AI Assistant")
    print("=" * 50)
    
    # Check if this is the first run
    try:
        import speech_recognition
        import pyttsx3
        import requests
    except ImportError:
        print("Installing required packages...")
        install_requirements()
        print("Please restart the program after installation completes.")
        sys.exit(1)
    
   
    
    # Check if API key is set
    if "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" in open(__file__).read():
        print("\n WARNING: Please set your OpenRouter API key before running!")
        api_key = input("Enter your OpenRouter API key (or press Enter to exit): ").strip()
        if not api_key:
            print("API key is required. Exiting...")
            sys.exit(1)
        
        # Update the API key in the JARVIS instance
        jarvis = JARVIS()
        jarvis.api_key = api_key
    else:
        jarvis = JARVIS()
    
    # Start JARVIS
    jarvis.run()