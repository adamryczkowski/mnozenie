import pyaudio
import numpy as np
import wave
from pathlib import Path
from pydantic import BaseModel
from pydub import AudioSegment
import base64

class VoiceSample(BaseModel):
    data: bytes
    frame_rate: int
    sample_width: int = 2

    def get_sample_as_np_array(self) -> np.ndarray:
        audio_segment = AudioSegment(
            self.data,
            frame_rate=44100,
            sample_width=2,
            channels=1
        )

        if self.frame_rate != 16000:  # 16 kHz
            audio_segment = self.set_frame_rate(16000)
        arr = np.array(audio_segment.get_array_of_samples())
        arr = arr.astype(np.float32) / 32768.0
        return arr

    def save(self, filename: Path):
        # Save the last recording as WAV file
        wf = wave.open(str(filename), 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.sample_width)
        wf.setframerate(self.frame_rate)
        wf.writeframes(self.data)
        wf.close()

    def __len__(self):
        return len(self.data)

    @property
    def data(self):
        return self.data

    def play(self):
        # Play the last recording
        stream = self.p.open(format=pyaudio.paInt16,
                             channels=2,
                             rate=44100,
                             output=True)
        stream.write(self.data)
        stream.stop_stream()


    def __getstate__(self):
        # Encodes data as base64
        return {
            "data": base64.b64encode(self.data).decode(),
            "frame_rate": self.frame_rate,
            "sample_width": self.sample_width
        }

    def __setstate__(self, state):
        # Encodes data as base64
        self.data = base64.b64decode(state["data"])
        self.frame_rate = state["frame_rate"]
        self.sample_width = state["sample_width"]


if __name__ == '__main__':
    pass