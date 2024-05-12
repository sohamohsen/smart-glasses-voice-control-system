# Smart Glasses Voice Control System

This project implements a voice-controlled system for smart glasses, enabling users to interact with various features using voice commands.

## Key Features
-Voice activation with a wake-up word.
-Navigation between features using voice commands.
-Communication with a server to retrieve information.
-Converting server responses from text to speech for display.

## Technologies Used
- Raspberry Pi, Raspberry Pi camera v3 and headphones with mic for hardware.
- Python: Programming language used for development.
- pvporcupine: Library for wake word detection.
- pvrecorder: Library for recording audio.
- pvleopard: Library for processing voice commands.
- PyAudio: Library for audio input/output.
- requests: Library for making HTTP requests.
- picamera2: Library for controlling the Raspberry Pi camera.
- pygame: Library for audio playback.
- gtts: Google Text-to-Speech library for converting text to speech.

## How to Use
1. Install dependencies using `pip install -r requirements.txt`.
2. Set up the Raspberry Pi and smart glasses according to the provided instructions.
3. Run the main script using `python main.py`.
4. Follow the on-screen prompts and interact with the system using voice commands.

## License
This project is licensed under the Picovoice License.

## Contribution Guidelines
Contributions are welcome! Please feel free to report bugs, suggest new features, or submit pull requests.
