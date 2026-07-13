import json
import sys


def main() -> None:
    from faster_whisper import WhisperModel
    model_path, media, language = sys.argv[1:4]
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(media, language=language, word_timestamps=True)
    words: list[dict[str, object]] = []
    text: list[str] = []
    for segment in segments:
        text.append(segment.text.strip())
        for word in segment.words or []:
            words.append({"text": word.word.strip(), "start": word.start, "end": word.end})
    print(json.dumps({"text": " ".join(text), "words": words}))


if __name__ == "__main__":
    main()
