# text-2-video

A local playground for generating video from text, or from text plus a start image, on an Apple Silicon Mac. It runs [LTX-2](https://github.com/dgrauet/ltx-2-mlx) on MLX, so nothing leaves your machine.

## Run

```bash
uv sync
uv run app.py
```

The UI opens in your browser. Write a prompt, optionally drop in a start image, and press Generate. Videos are saved to `outputs/`.

## Get the model

Download the weights into `models/` before the first run. This fetches only what the "Distilled" pipeline needs (about 30 GB instead of the full 87 GB):

```bash
uv run hf download dgrauet/ltx-2.3-mlx-q8 --local-dir models/ltx-2.3-mlx-q8 \
  --exclude "transformer-dev.safetensors" --exclude "transformer-distilled.safetensors" \
  --exclude "*distilled-lora*" --exclude "spatial_upscaler_x1_5*"
```

Each pattern needs its own `--exclude`; extra values after one flag are treated as files to download.

The Gemma text encoder (about 8 GB) downloads by itself on the first generation, into `~/.cache/huggingface`.

The two-stage and one-stage pipelines also need the dev transformer and the distilled LoRA. To add them later, run the same command without the `--exclude` flags; files you already have are skipped.

Any folder inside `models/` appears in the Model dropdown. `models/` is git-ignored.

## Requirements

- Apple Silicon Mac with 32 GB+ memory for the int8 (`q8`) model. With 16 GB, pick the `q4` model or tick "Low RAM".
- [uv](https://docs.astral.sh/uv/) and `ffmpeg`.

## Settings that matter

- **Pipeline**: "Distilled" is the fastest. "Two-stage" gives better quality and takes longer.
- **Size and frames**: memory use grows steeply with resolution and length. On 48 GB, stay around 704×448 and 97–121 frames (4–5 seconds). Generate small and upscale afterwards.
- **Seed**: set a fixed number to reproduce a result.

## Using LTX-2.5

The LTX-2.5 weights are gated on Hugging Face and must be a local folder:

1. Accept the licence at https://huggingface.co/dgrauet/ltx-2.5-mlx-q8 and run `uv run hf auth login`.
2. `uv run hf download dgrauet/ltx-2.5-mlx-q8 --local-dir models/ltx-2.5-mlx-q8` (about 75 GB).

Any folder inside `models/` appears in the Model dropdown. With LTX-2.5 you can set Frames to 0 and the model picks the clip length from the prompt.
