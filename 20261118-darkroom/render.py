"""Render Still Running from its procedural scene and photographic plates."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target", nargs="?", choices=("both", "still"), default="both",
        help="Render the still and animation (default), or the still alone.",
    )
    parser.add_argument("--work", type=Path, default=ROOT / "build",
                        help="Directory for compiled renderers, scene buffers, and motion passes.")
    parser.add_argument("--output", type=Path, default=ROOT / "renders",
                        help="Directory for finished PNGs and animation files.")
    args = parser.parse_args()
    work = args.work.resolve()
    output = args.output.resolve()
    still = work / "still"

    print("Rendering the still image", flush=True)
    subprocess.run([
        sys.executable, str(ROOT / "still" / "render.py"),
        "--width", "528", "--samples", "144", "--work", str(still),
        "--output", str(output),
    ], check=True)

    if args.target == "both":
        print("Rendering the running-water animation", flush=True)
        subprocess.run([
            sys.executable, str(ROOT / "animation" / "animate.py"),
            "--master", str(still), "--work", str(work / "animation"),
            "--output", str(output),
        ], check=True)


if __name__ == "__main__":
    main()
