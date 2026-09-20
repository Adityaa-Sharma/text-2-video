"""Turn a shot list into one film: generate each shot with LTX-2, then join them.

Run: uv run film.py shots/kafka.txt

Shot file: one shot per paragraph, separated by blank lines. If the first paragraph starts
with "STYLE:", it is prepended to every shot so the look stays consistent.
"""

import subprocess
import sys
from pathlib import Path

from app import CLI, MODELS, OUTPUTS


def parse(text):
    shots = [" ".join(p.split()) for p in text.split("\n\n") if p.strip()]
    style = ""
    if shots and shots[0].startswith("STYLE:"):
        style = shots.pop(0).removeprefix("STYLE:").strip() + " "
    return [style + s for s in shots]


def main(shot_file):
    src = Path(shot_file)
    out = OUTPUTS / src.stem
    out.mkdir(parents=True, exist_ok=True)
    clips = []
    for i, prompt in enumerate(parse(src.read_text()), 1):
        clip = out / f"{i:02d}.mp4"
        clips.append(clip)
        if clip.exists():  # rerun resumes; delete a clip to redo just that shot
            continue
        print(f"--- shot {i}: {prompt[:80]}...", flush=True)
        cmd = [CLI, "generate", "-p", prompt, "-o", clip, "-m", MODELS[0], "--distilled", "-q"]
        cmd += ["-W", "704", "-H", "448", "-f", "97", "--frame-rate", "24", "-s", str(i)]
        subprocess.run(cmd, check=True)
    listing = out / "clips.txt"
    listing.write_text("".join(f"file '{c.name}'\n" for c in clips))
    film = OUTPUTS / f"{src.stem}.mp4"
    join = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", film]
    subprocess.run(join, check=True)
    print(f"Film saved to {film}")


if __name__ == "__main__":
    assert parse("STYLE: noir.\n\na  cat\nruns\n\na dog") == ["noir. a cat runs", "noir. a dog"]
    assert parse("just one") == ["just one"]
    main(sys.argv[1])
