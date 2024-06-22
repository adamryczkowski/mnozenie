import wave
from pathlib import Path
from pydub import AudioSegment

import numpy as np
import pyaudio


class SoundRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []

    def start_recording(self):
        self.frames = []
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=44100,
                                  input=True,
                                  frames_per_buffer=1024,
                                  stream_callback=self.callback)
        self.stream.start_stream()

    def stop_recording(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.stream = None

    def get_last_recording(self) -> bytes:
        return b''.join(self.frames)

    def get_last_recording_as_whisper_sound(self)->np.ndarray:
        # Converts the sound to np.ndarray, 16kHz, mono as float32 in range [-1, 1]
        # The input sound is 44100Hz, stereo, int16
        sound = self.get_last_recording()
        # Downsample to 16kHz
        audio_segment = AudioSegment(
            sound,
            frame_rate=44100,
            sample_width=2,
            channels=1
        )
        if audio_segment.frame_rate != 16000:  # 16 kHz
            audio_segment = audio_segment.set_frame_rate(16000)
        arr = np.array(audio_segment.get_array_of_samples())
        arr = arr.astype(np.float32) / 32768.0
        return arr







    def save_last_recording(self, filename: Path):
        # Save the last recording as WAV file
        wf = wave.open(str(filename), 'wb')
        wf.setnchannels(2)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()

    def play_last_recording(self):
        # Play the last recording
        stream = self.p.open(format=pyaudio.paInt16,
                             channels=2,
                             rate=44100,
                             output=True)
        stream.write(b''.join(self.frames))
        stream.stop_stream()

    def callback(self, in_data, frame_count, time_info, status):
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)


if __name__ == "__main__":
    sound_recorder = SoundRecorder()
    sound_recorder.start_recording()
    input("Press Enter to stop recording")
    sound_recorder.stop_recording()
    print("Recording done")
    print("Recording length: ", len(sound_recorder.get_last_recording()))
    sound_recorder.save_last_recording("output.wav")
    # Sound playback
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True)
    stream.write(sound_recorder.get_last_recording())
    stream.stop_stream()
    sound_recorder.save_last_recording("output.wav")
