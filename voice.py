import os
import speech_recognition as sr
from pydub import AudioSegment


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FFMPEG_BIN = os.path.join(BASE_DIR, "ffmpeg", "bin")

FFMPEG_EXE = os.path.join(FFMPEG_BIN, "ffmpeg.exe")
FFPROBE_EXE = os.path.join(FFMPEG_BIN, "ffprobe.exe")


if os.path.exists(FFMPEG_EXE):
    os.environ["PATH"] += os.pathsep + FFMPEG_BIN

    AudioSegment.converter = FFMPEG_EXE
    AudioSegment.ffmpeg = FFMPEG_EXE
    AudioSegment.ffprobe = FFPROBE_EXE

    print("FFMPEG найден:", FFMPEG_EXE)
else:
    print("FFMPEG НЕ НАЙДЕН:", FFMPEG_EXE)


def recognize_voice(file_path: str):
    wav_path = None

    try:
        wav_path = file_path.replace(".ogg", ".wav")

        audio = AudioSegment.from_file(file_path, format="ogg")
        audio.export(wav_path, format="wav")

        recognizer = sr.Recognizer()

        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(
            audio_data,
            language="ru-RU"
        )

        return text

    except Exception as e:
        print("VOICE ERROR:", e)
        return None

    finally:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)