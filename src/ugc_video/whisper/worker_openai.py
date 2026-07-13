import json
import sys


def main() -> None:
    import whisper

    model_root, media, language = sys.argv[1:4]
    model = whisper.load_model("small", download_root=model_root)
    result = model.transcribe(media, language=language, word_timestamps=True)
    words = [word for segment in result.get("segments", []) for word in segment.get("words", [])]
    print(json.dumps({"text": result.get("text", ""), "words": words}))


if __name__ == "__main__":
    main()
