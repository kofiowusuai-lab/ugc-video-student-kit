import json
import sys


def main() -> None:
    import mlx_whisper
    model_path, media, language = sys.argv[1:4]
    result = mlx_whisper.transcribe(media, path_or_hf_repo=model_path, language=language, word_timestamps=True)
    words = [word for segment in result.get("segments", []) for word in segment.get("words", [])]
    print(json.dumps({"text": result.get("text", ""), "words": words}))


if __name__ == "__main__":
    main()
