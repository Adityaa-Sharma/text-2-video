"""Playground UI for LTX-2 on Apple Silicon: text -> video, or text + image -> video.

Run: uv run app.py
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).parent
OUTPUTS = ROOT / "outputs"
CLI = Path(sys.executable).parent / "ltx-2-mlx"

# LTX-2.5 packs are gated and must be a local directory; drop one in models/ and it shows up here.
MODELS = [str(p) for p in sorted((ROOT / "models").glob("*")) if p.is_dir()] + [
    "dgrauet/ltx-2.3-mlx-q8",
]
MODES = {
    "Distilled (fastest)": "--distilled",
    "Two-stage (better quality)": "--two-stage",
    "Two-stage HQ (slowest)": "--two-stages-hq",
    "One-stage": "--one-stage",
}
# Frame counts must be 8n+1. 0 = let the model pick the duration (LTX-2.5 only).
FRAMES = [0, 25, 49, 65, 81, 97, 121, 145, 161]


def build_cmd(prompt, image, model, mode, width, height, frames, seed, audio, low_ram, enhance, out):
    cmd = [str(CLI), "generate", "-p", prompt, "-o", str(out), "-m", model, MODES[mode]]
    cmd += ["-W", str(width), "-H", str(height), "--frame-rate", "24", "-s", str(int(seed))]
    if frames:
        cmd += ["-f", str(frames)]
    if image:
        cmd += ["--image", image]
    if not audio:
        cmd.append("--no-audio")
    if low_ram:
        cmd.append("--low-ram")
    if enhance:
        cmd.append("--enhance-prompt")
    return cmd


def generate(prompt, image, model, mode, width, height, frames, seed, audio, low_ram, enhance):
    if not prompt.strip():
        raise gr.Error("Write a prompt first.")
    OUTPUTS.mkdir(exist_ok=True)
    out = OUTPUTS / f"{time.strftime('%Y%m%d-%H%M%S')}.mp4"
    cmd = build_cmd(prompt, image, model, mode, width, height, frames, seed, audio, low_ram, enhance, out)
    log = "$ " + " ".join(cmd) + "\n"
    start = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        # Read raw chunks, not lines: tqdm progress bars redraw with \r and never emit \n.
        while chunk := os.read(proc.stdout.fileno(), 4096):
            log = (log + chunk.decode(errors="replace").replace("\r", "\n"))[-6000:]
            yield None, log
        if proc.wait() != 0 or not out.exists():
            raise gr.Error(f"Generation failed (exit {proc.returncode}). See the log.")
        yield str(out), log + f"\nDone in {time.time() - start:.0f}s -> {out}"
    finally:
        proc.kill()  # also runs when the Stop button cancels this generator


with gr.Blocks(title="LTX-2 Playground") as demo:
    gr.Markdown("# LTX-2 Playground\nText → video, or add an image to animate it. Runs fully on this Mac.")
    with gr.Row():
        with gr.Column():
            prompt = gr.Textbox(label="Prompt", lines=4, placeholder="A heavy wooden door creaks slowly open...")
            image = gr.Image(label="Start image (optional, makes it image-to-video)", type="filepath")
            model = gr.Dropdown(MODELS, value=MODELS[0], label="Model", allow_custom_value=True)
            mode = gr.Dropdown(list(MODES), value="Distilled (fastest)", label="Pipeline")
            with gr.Row():
                width = gr.Slider(256, 1280, value=704, step=64, label="Width")
                height = gr.Slider(256, 1280, value=448, step=64, label="Height")
            with gr.Row():
                frames = gr.Dropdown(FRAMES, value=97, label="Frames @ 24 fps (0 = auto, LTX-2.5 only)")
                seed = gr.Number(value=-1, precision=0, label="Seed (-1 = random)")
            with gr.Row():
                audio = gr.Checkbox(value=True, label="Audio")
                low_ram = gr.Checkbox(label="Low RAM (slower)")
                enhance = gr.Checkbox(label="Enhance prompt")
            with gr.Row():
                run = gr.Button("Generate", variant="primary")
                stop = gr.Button("Stop")
        with gr.Column():
            video = gr.Video(label="Result")
            log = gr.Textbox(label="Log", lines=18, max_lines=18, autoscroll=True)
    inputs = [prompt, image, model, mode, width, height, frames, seed, audio, low_ram, enhance]
    event = run.click(generate, inputs, [video, log], concurrency_limit=1)  # one run at a time: memory
    stop.click(None, cancels=[event])

if __name__ == "__main__":
    cmd = build_cmd("p", "i.png", "m", "One-stage", 704, 448, 0, -1, False, True, False, "o.mp4")
    assert "-f" not in cmd and cmd[-4:] == ["--image", "i.png", "--no-audio", "--low-ram"], cmd
    demo.launch(inbrowser=True)
