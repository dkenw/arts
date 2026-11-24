"""Print No Further Sailings, Edition 19, from the industrial harbour scene."""

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from output_files import staged_output
from paint import make
from pixel import write_prints

HERE = Path(__file__).resolve().parent
# Camera exposure width and maximum Cycles samples. The original exposure is
# resolved onto its own 528 × 396 drawing grid after rendering.
FULL = {"original": (1056, 560), "large": (2112, 224)}
PROOF = {"original": (528, 56), "large": (1056, 48)}


def expose(profile, executable, threads, work, proof):
    folder = work / profile / ("proof" if proof else "full")
    folder.mkdir(parents=True, exist_ok=True)
    maps = folder / "maps"
    make(maps, large=(profile == "large"))
    source = folder / "exposure.png"
    width, samples = (PROOF if proof else FULL)[profile]
    command = [executable, "-b"]
    if threads:
        command += ["-t", str(threads)]
    command += [
        "--python-exit-code", "1", "-P", str(HERE / "terminal.py"), "--",
        "--profile", profile, "--maps", str(maps), "--output", str(source),
        "--width", str(width), "--samples", str(samples),
    ]
    subprocess.run(command, check=True)
    return source


def main():
    build = HERE / "build"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("all", "original", "large"), default="all")
    parser.add_argument("--output", type=Path, help="Output directory. Full renders default to renders/.")
    parser.add_argument("--work", type=Path, default=build, help="Working directory for Blender captures.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--from-exposures", action="store_true", help="Develop the archived Blender 4 exposures. Defaults to build/archive-reprint/.")
    mode.add_argument("--proof", action="store_true", help="Render with fewer samples. Defaults to build/proof/.")
    parser.add_argument("--blender", help="Path to Blender.")
    parser.add_argument("--threads", type=int, default=0, help="CPU threads. Zero uses Blender's default.")
    args = parser.parse_args()
    if args.threads < 0:
        parser.error("--threads must be zero or positive.")
    executable = None
    if not args.from_exposures:
        executable = args.blender or os.environ.get("BLENDER") or shutil.which("blender")
        if not executable:
            mac = Path("/Applications/Blender.app/Contents/MacOS/Blender")
            if not mac.is_file():
                parser.error("Install Blender 5.2 LTS, pass its path with --blender, or use --from-exposures.")
            executable = str(mac)
    profiles = tuple(FULL) if args.profile == "all" else (args.profile,)
    if args.proof:
        default_output = build / "proof"
    elif args.from_exposures:
        default_output = build / "archive-reprint"
    else:
        default_output = HERE / "renders"
    output = (args.output or default_output).resolve()
    files = []
    try:
        with staged_output(output) as stage:
            for profile in profiles:
                if args.from_exposures:
                    source = HERE / "archive" / "exposures" / profile / "exposure.png"
                else:
                    source = expose(profile, executable, args.threads, args.work.resolve(), args.proof)
                files.extend(write_prints(source, stage, large=(profile == "large")))
    except ValueError as error:
        parser.error(str(error))
    for name in files:
        print(output / name, flush=True)


if __name__ == "__main__":
    main()
