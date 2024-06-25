from __future__ import annotations

import base64
import wave
from pathlib import Path

import numpy as np
import pyaudio
from pydantic import BaseModel, EncoderProtocol, EncodedBytes
from pydub import AudioSegment
from typing_extensions import Annotated


class MyBytesEncoder(EncoderProtocol):
    @classmethod
    def encode(cls, value):
        return base64.b85encode(value).decode()

    @classmethod
    def decode(cls, value):
        return base64.b85decode(value)


class VoiceSample(BaseModel):
    data: Annotated[bytes, EncodedBytes(encoder=MyBytesEncoder)]
    frame_rate: int
    sample_width: int = 2

    def get_sample_as_np_array(self) -> np.ndarray:
        audio_segment = AudioSegment(
            self.data,
            frame_rate=self.frame_rate,
            sample_width=self.sample_width,
            channels=1
        )

        if self.frame_rate != 16000:  # 16 kHz
            audio_segment = audio_segment.set_frame_rate(16000)
        arr = np.array(audio_segment.get_array_of_samples())
        arr = arr.astype(np.float32) / 32768.0
        return arr

    def ResampledClone(self, frame_rate: int = 16000) -> VoiceSample:
        audio_segment = AudioSegment(
            self.data,
            frame_rate=self.frame_rate,
            sample_width=self.sample_width,
            channels=1
        )

        audio_segment = audio_segment.set_frame_rate(frame_rate)
        return VoiceSample(data=audio_segment.raw_data, frame_rate=frame_rate, sample_width=self.sample_width)

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
        p = pyaudio.PyAudio()
        if self.sample_width== 2:
            p_format = pyaudio.paInt16
        else:
            raise ValueError("Unsupported sample width")
        stream = p.open(format=p_format,
                        channels=1,
                        rate=self.frame_rate,
                        output=True)
        stream.write(self.data)
        stream.stop_stream()


def test_voice_sample() -> VoiceSample:
    data = "ala ma kota".encode()
    frame_rate = 44100
    sample_width = 2
    voice_sample = VoiceSample(data=data, frame_rate=frame_rate, sample_width=sample_width)
    return voice_sample


if __name__ == '__main__':
    pass
    json_txt = test_voice_sample().json()
    with open("test.json", "w") as f:
        f.write(json_txt)
