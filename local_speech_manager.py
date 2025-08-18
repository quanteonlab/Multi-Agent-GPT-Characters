import threading
import queue
import time
import os
import re
from gtts import gTTS
import pygame.mixer
from pydub import AudioSegment


class SpeechManager:
    """
    message_queue      ← 由外部(Flask)压入整段文本  
    process_queue()    ← 在 pygame 主循环里持续调用  
    speak()            ← 内部使用，把文本拆块并并行生成 MP3
    """

    def __init__(self, avatar_manager=None, chunk_size: int = 10):
        self.message_queue: "queue.Queue[str]" = queue.Queue()

        self.avatar_manager = avatar_manager
        self.chunk_size = chunk_size
        self._ready_mp3 = {}               
        self._ready_lock = threading.Lock()
        self._next_play_idx = 0            
        self._total_chunks = 0             
        self._generated_cnt = 0            
        self._generating = False           

        pygame.mixer.init()

    @property
    def is_speaking(self) -> bool:
        return pygame.mixer.get_busy()

    def process_queue(self):
        if self.is_speaking:
            return

        finished_idx = self._next_play_idx - 1
        if finished_idx >= 0:
            old_path = f"tts_{finished_idx}.mp3"
            temp_old_path = f"temp_tts_{finished_idx}.mp3"
            if os.path.exists(old_path):
                os.remove(old_path)

            if os.path.exists(temp_old_path):
                os.remove(temp_old_path)

        with self._ready_lock:
            path = self._ready_mp3.pop(self._next_play_idx, None)

        if path:
            print(f"Playing audio: {path}")
            pygame.mixer.Sound(path).play()
            self._next_play_idx += 1
            return

        pipeline_idle = (
            not self._generating and
            not self._ready_mp3 and
            not self.is_speaking
        )
        if pipeline_idle and not self.message_queue.empty():
            self.speak(self.message_queue.get())

    def text_to_audio(self, input_text, voice="default", save_as_wave=True, subdirectory="", model_id="gtts"):
        """
        Compatibility method for the existing codebase.
        Generates audio file and returns the path (to match ElevenLabs interface)
        """
        # Generate filename similar to ElevenLabs format
        if save_as_wave:
            file_name = f"___Msg{str(hash(input_text))}{time.time()}_{model_id}.wav"
        else:
            file_name = f"___Msg{str(hash(input_text))}{time.time()}_{model_id}.mp3"
            
        tts_file = os.path.join(os.path.abspath(os.curdir), subdirectory, file_name)
        
        try:
            # Use gTTS to generate the audio
            if save_as_wave:
                # Generate as MP3 first, then convert to WAV
                temp_mp3 = tts_file.replace('.wav', '_temp.mp3')
                gTTS(text=input_text, lang="en", tld="us").save(temp_mp3)
                
                # Convert MP3 to WAV using pydub
                audio = AudioSegment.from_file(temp_mp3, format="mp3")
                audio.export(tts_file, format="wav")
                
                # Clean up temp file
                if os.path.exists(temp_mp3):
                    os.remove(temp_mp3)
            else:
                # Direct MP3 generation
                gTTS(text=input_text, lang="en", tld="us").save(tts_file)
            
            print(f"[green]Local TTS (gTTS) saved: {file_name}")
            return tts_file
            
        except Exception as e:
            print(f"[red]TTS Error: {e}")
            # Return a dummy file path to prevent crashes
            return tts_file

    def speak(self, text: str):
        """把整段文本切块、并行生成 MP3，并重置播放管线"""
        words = text.split()
        chunks = []
        i = 0
        size = self.chunk_size

        # Define all separators we care about
        SEPARATORS = r"[.,;:?!]"
        LAST_SEPARATOR_REGEX = SEPARATORS + r"(?!.*" + SEPARATORS + ")"

        while i < len(words):
            end = min(i + size, len(words))
            chunk_words = words[i:end]
            chunk_text = " ".join(chunk_words)

            # Look for the last punctuation mark within the current chunk
            match = re.search(LAST_SEPARATOR_REGEX, chunk_text)
            if match:
                punct_index = chunk_text[:match.end()].count(" ")
                end = min(i + punct_index + 1, i + size)
                # print("end", end,"start", i, "size", size, chunk_text, match.group(0))
                chunk_words = words[i:end]
            
            chunk = " ".join(chunk_words)
            chunks.append(chunk)

            i = end
            size *= 2
        
        # 重置流水线
        self._ready_mp3.clear()
        self._next_play_idx = 0
        self._total_chunks = len(chunks)
        self._generated_cnt = 0
        self._generating = True

        # 并行生成
        for idx, chunk in enumerate(chunks):
            threading.Thread(
                target=self._tts_worker,
                args=(idx, chunk),
                daemon=True,
            ).start()
            time.sleep(0.1)  # Avoid overwhelming the system with threads

    def _tts_worker(self, idx: int, text: str):
        try:
            temp_path = f"temp_tts_{idx}.mp3"
            path = f"tts_{idx}.mp3"
            
            # Generate TTS audio for all chunks
            gTTS(text=text, lang="en", tld="us").save(temp_path)
            
            # Apply speed-up to all chunks
            speed_to_use = 1.5
            print(f"[green]Speeding up audio {temp_path} by {speed_to_use}x")
            audio = AudioSegment.from_file(temp_path, format="mp3")
            final = audio.speedup(playback_speed=speed_to_use)
            final.export(path, format="mp3")
            
            print('created audio', idx + 1, 'of', self._total_chunks)
            with self._ready_lock:
                self._ready_mp3[idx] = path
                
        except Exception as e:
            print(f"[TTS ERROR] {e}")
        finally:
            with self._ready_lock:
                self._generated_cnt += 1
                if self._generated_cnt >= self._total_chunks:
                    self._generating = False


# Compatibility alias for the main application
LocalSpeechManager = SpeechManager


if __name__ == "__main__":
    sm = SpeechManager(chunk_size=5)
    msg = (
        "Este es un mensaje muy largo que debe ser dividido "
        "automáticamente en partes de diez palabras para ser procesado "
        "correctamente por el sistema de síntesis de voz."
    )
    sm.speak(msg)

    # keep main thread alive until playback ends
    while sm.is_speaking or sm._generating:
        sm.process_queue()
        time.sleep(0.1)
        
