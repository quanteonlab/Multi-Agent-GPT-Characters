import wave
import pyaudio
import pygame
from pydub import AudioSegment
from mutagen.mp3 import MP3
import time
import os
import asyncio
import subprocess
import threading
import sounddevice as sd
import soundfile as sf
import keyboard
import numpy as np


class AudioManager:
    def __init__(self):
        pass

    def play_audio(self, audio_path, block=True, fade_in=False, use_pygame=True):
        """
        Play an audio file using pygame or another method.
        """
        if use_pygame:
            import pygame.mixer
            pygame.mixer.init()
            sound = pygame.mixer.Sound(audio_path)
            if fade_in:
                sound.play(fade_ms=1000)
            else:
                sound.play()
            if block:
                while pygame.mixer.get_busy():
                    time.sleep(0.1)
        else:
            # Implement other playback methods if needed
            pass

    def record_audio(self, end_recording_key='num 8', agent_name=None, audio_number=None, subdirectory=""):
        """
        Record audio from the microphone and save it to a file with improved naming.
        """
        samplerate = 44100
        channels = 1
        print("[green]Recording... Press {} to stop.".format(end_recording_key))
        recording = []
        while not keyboard.is_pressed(end_recording_key):
            data = sd.rec(int(samplerate * 0.5), samplerate=samplerate, channels=channels, dtype='float32')
            sd.wait()
            recording.append(data)
        audio = np.concatenate(recording, axis=0)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        agent_str = agent_name if agent_name else "agent"
        audio_num_str = str(audio_number) if audio_number is not None else "audio"
        file_name = f"{agent_str}_audio_{audio_num_str}_{timestamp}.wav"
        audio_path = os.path.join(os.path.abspath(os.curdir), subdirectory, file_name)
        sf.write(audio_path, audio, samplerate)
        print(f"[green]Audio recorded and saved as: {file_name}")
        return audio_path
        # else:
        #     # Pygame Sound lets you play multiple sounds simultaneously
        #     pygame_sound = pygame.mixer.Sound(file_path) 
        #     pygame_sound.play()

        # if sleep_during_playback:
        #     # Sleep until file is done playing
        #     file_length = self.get_audio_length(file_path)
        #     time.sleep(file_length)
        #     # Delete the file
        #     if delete_file:
        #         # Stop Pygame so file can be deleted
        #         # Note: this will stop the audio on other threads as well, so it's not good if you're playing multiple sounds at once
        #         pygame.mixer.music.stop()
        #         pygame.mixer.quit()
        #         try:  
        #             os.remove(file_path)
        #             if converted:
        #                 os.remove(converted_wav) # Remove the converted wav if it was created
        #         except PermissionError:
        #             print(f"Couldn't remove {file_path} because it is being used by another process.")

    async def play_audio_async(self, file_path):
        """
        Parameters:
        file_path (str): path to the audio file
        """
        if not pygame.mixer.get_init(): # Reinitialize mixer if needed
            pygame.mixer.init(frequency=48000, buffer=1024) 
        pygame_sound = pygame.mixer.Sound(file_path) 
        pygame_sound.play()

        # Sleep for the duration of the audio.
        # Must use asyncio.sleep() because time.sleep() will block the thread, even if it's in an async function
        file_length = self.get_audio_length(file_path)
        await asyncio.sleep(file_length)
    
    def get_audio_length(self, file_path):
        # Calculate length of the file based on the file format
        _, ext = os.path.splitext(file_path) # Get the extension of this file
        if ext.lower() == '.wav':
            wav_file = sf.SoundFile(file_path)
            file_length = wav_file.frames / wav_file.samplerate
            wav_file.close()
        elif ext.lower() == '.mp3':
            mp3_file = MP3(file_path)
            file_length = mp3_file.info.length
        else:
            print("Unknown audio file type. Returning 0 as file length")
            file_length = 0
        return file_length
    
    def combine_audio_files(self, input_files):
        # input_files is an array of file paths
        output_file = os.path.join(os.path.abspath(os.curdir), f"___Msg{str(hash(' '.join(input_files)))}.wav")
        combined = None
        for file in input_files:
            audio = AudioSegment.from_file(file)
            if combined is None:
                combined = audio
            else:
                combined += audio
        if combined:
            combined.export(output_file, format=os.path.splitext(output_file)[1][1:])
            print(f"Combined file saved as: {output_file}")
        else:
            print("No files to combine.")
        return output_file
    
    def start_recording(self, stream):
        self.audio_frames = []
        while self.is_recording:
            data = stream.read(self.chunk)
            self.audio_frames.append(data)
        print("[red]DONE RECORDING!")

    def record_audio(self, end_recording_key='=', audio_device=None):
        # Records audio from an audio input device.
        # Example device names are "Line In (Realtek(R) Audio)", "Sample (TC-Helicon GoXLR)", or just leave empty to use default mic
        # For some reason this doesn't work on the Broadcast GoXLR Mix, the other 3 GoXLR audio inputs all work fine.
        # Both Azure Speech-to-Text AND this script have issues listening to Broadcast Stream Mix, so just ignore it.
        audio = pyaudio.PyAudio()
        
        if audio_device is None:
            # If no audio_device is provided, use the default mic
            audio_stream = audio.open(format=self.audio_format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk)
        else:
            # If an audio device was provided, find its index
            device_index = None
            for i in range(audio.get_device_count()):
                dev_info = audio.get_device_info_by_index(i)
                # print(dev_info['name'])
                if audio_device in dev_info['name']:
                    device_index = i
                    # Some audio devices only support specific sample rates, so make sure to find a sample rate that's compatible with the device
                    # This was necessary on certain GoXLR input but only sometimes. But this fixes the issues so w/e.
                    supported_rates = [96000, 48000, 44100, 32000, 22050, 16000, 11025, 8000]
                    for rate in supported_rates:
                        try:
                            if audio.is_format_supported(rate, input_device=device_index, input_channels=self.channels, input_format=self.audio_format):
                                self.rate = rate
                                break
                        except ValueError:
                            continue
            if device_index is None:
                raise ValueError(f"Device '{audio_device}' not found")
            if self.rate is None:
                raise ValueError(f"No supported sample rate found for device '{audio_device}'")
            audio_stream = audio.open(format=self.audio_format, channels=self.channels, rate=self.rate, input=True, input_device_index=device_index, frames_per_buffer=self.chunk)
                    
        # Start recording an a second thread
        self.is_recording = True
        threading.Thread(target=self.start_recording, args=(audio_stream,)).start()

        # Wait until end key is pressed
        while True:
            if keyboard.is_pressed(end_recording_key):
                break
            time.sleep(0.05) # Add this to reduce CPU usage
        
        self.is_recording = False
        time.sleep(0.1) # Just for safety, no clue if this is needed

        filename = f"mic_recording_{int(time.time())}.wav"
        wave_file = wave.open(filename, 'wb')
        wave_file.setnchannels(self.channels)
        wave_file.setsampwidth(audio.get_sample_size(self.audio_format))
        wave_file.setframerate(self.rate)
        wave_file.writeframes(b''.join(self.audio_frames))
        wave_file.close()

        # Close the stream and PyAudio
        audio_stream.stop_stream()
        audio_stream.close()
        audio.terminate()

        return filename
        
