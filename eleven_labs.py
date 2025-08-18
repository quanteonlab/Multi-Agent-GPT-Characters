from elevenlabs.client import ElevenLabs
from elevenlabs import play, stream, save, Voice, VoiceSettings
import time
import os

class ElevenLabsManager:

    def __init__(self):
        self.client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY')) # Defaults to ELEVEN_API_KEY)
        self.voices = self.client.voices.get_all().voices
        # Create a map of Names->IDs, so that we can easily grab a voice's ID later on 
        self.voice_to_id = {}
        for voice in self.voices:
           self.voice_to_id[voice.name] = voice.voice_id
        
        # Print available voices for debugging
        print("[cyan]Available ElevenLabs voices:")
        for voice_name in self.voice_to_id.keys():
            print(f"[cyan]  - {voice_name}")
        
        self.voice_to_settings = {}

    # Convert text to speech, then save it to file. Returns the file path.
    # Current model options (that I would use) are eleven_monolingual_v1 or eleven_turbo_v2
    # eleven_turbo_v2 takes about 60% of the time that eleven_monolingual_v1 takes
    # However eleven_monolingual_v1 seems to produce more variety and emphasis, whereas turbo feels more monotone. Turbo still sounds good, just a little less interesting
    def text_to_audio(self, input_text, voice="Doug VO Only", save_as_wave=True, subdirectory="", model_id="eleven_monolingual_v1"):
        # Check if voice exists
        if voice not in self.voice_to_id:
            print(f"[red]ERROR: Voice '{voice}' not found in ElevenLabs account!")
            print(f"[red]Available voices: {list(self.voice_to_id.keys())}")
            raise ValueError(f"Voice '{voice}' not found. Available voices: {list(self.voice_to_id.keys())}")
            
        # Use the current ElevenLabs API - try multiple method patterns for compatibility
        try:
            # Try the newer API method
            audio_saved = self.client.text_to_speech.convert(
                voice_id=self.voice_to_id[voice],
                text=input_text,
                model_id=model_id
            )
        except AttributeError:
            try:
                # Try alternative method
                audio_saved = self.client.generate(
                    text=input_text,
                    voice=Voice(voice_id=self.voice_to_id[voice]),
                    model=model_id
                )
            except AttributeError:
                # Fallback to direct voice ID
                from elevenlabs import generate
                audio_saved = generate(
                    text=input_text,
                    voice=self.voice_to_id[voice],
                    model=model_id,
                    api_key=os.getenv('ELEVENLABS_API_KEY')
                )
        if save_as_wave:
            file_name = f"___Msg{str(hash(input_text))}{time.time()}_{model_id}.wav"
        else:
            file_name = f"___Msg{str(hash(input_text))}{time.time()}_{model_id}.mp3"
        tts_file = os.path.join(os.path.abspath(os.curdir), subdirectory, file_name)
        save(audio_saved,tts_file)
        return tts_file