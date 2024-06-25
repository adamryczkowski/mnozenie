import numpy as np
import wave
from pathlib import Path
from pydantic import BaseModel
from pydub import AudioSegment


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


if __name__ == '__main__':
    pass