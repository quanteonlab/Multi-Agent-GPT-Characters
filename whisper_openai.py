import os
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from rich import print

class WhisperManager:
    """
    Uses Whisper on HF: https://huggingface.co/openai/whisper-large-v3
    - Safe on machines without CUDA (falls back to CPU).
    - You can override model via env: WHISPER_MODEL=openai/whisper-small
    """

    def __init__(self, language="en", multilingual=False):
        use_cuda = torch.cuda.is_available()
        print(f"[bold cyan]CUDA available:[/bold cyan] {use_cuda}")
        if use_cuda:
            try:
                print(f"[bold green]GPU:[/bold green] {torch.cuda.get_device_name(0)}")
            except Exception as e:
                print(f"[yellow]Warning:[/yellow] could not query GPU name: {e}")

        # Device & dtype
        self.device = torch.device("cuda:0") if use_cuda else torch.device("cpu")
        torch_dtype = torch.float16 if use_cuda else torch.float32

        # Choose model (you can downshift on CPU to speed things up)
        default_model = "openai/whisper-large-v3"
        model_id = os.getenv("WHISPER_MODEL", default_model)
        if not use_cuda and model_id.endswith("large-v3"):
            print("[yellow]CPU detected; loading a large model may be slow. "
                  "Set WHISPER_MODEL=openai/whisper-small (or medium) for faster CPU runs.[/yellow]")

        # Load model & processor
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        ).to(self.device)

        # Basic generation prefs
        model.generation_config.is_multilingual = multilingual
        if not multilingual:
            # lock language for faster decoding
            model.generation_config.language = language

        processor = AutoProcessor.from_pretrained(model_id)

        # Pipeline device arg: int GPU index for CUDA, or "cpu"
        device_arg = 0 if use_cuda else "cpu"

        # Batch/Chunk sizing tuned per device
        batch_size = 8 if use_cuda else 1
        chunk_length_s = 30 if use_cuda else 15

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=256,
            chunk_length_s=chunk_length_s,
            batch_size=batch_size,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device_arg,
        )

    def audio_to_text(self, audio_file, timestamps=None):
        """
        timestamps: None | "sentence" | "word"
        Returns text if timestamps=None, else a list of dicts with text/start_time/end_time
        """
        if timestamps is None:
            result = self.pipe(audio_file, return_timestamps=False)
            return result["text"]

        if timestamps == "sentence":
            result = self.pipe(audio_file, return_timestamps=True)
        elif timestamps == "word":
            result = self.pipe(audio_file, return_timestamps="word")
        else:
            return " "

        # normalize chunked timestamps
        out = []
        for ch in result.get("chunks", []):
            out.append({
                "text": ch.get("text", ""),
                "start_time": (ch.get("timestamp") or [None, None])[0],
                "end_time":   (ch.get("timestamp") or [None, None])[1],
            })
        return out
