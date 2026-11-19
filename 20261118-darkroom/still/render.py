"""Render the native still and export a 3× nearest-neighbour enlargement."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

SRC = Path(__file__).resolve().parent / 'src'
sys.path.insert(0, str(SRC))
from plates import build as draw_photographs
from color import grade


def render(work, output, width, samples):
    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    compiler = os.environ.get('CXX') or shutil.which('c++')
    if not compiler:
        raise SystemExit('Install a C++17 compiler, or set CXX to its executable.')
    program = work / 'draw'
    subprocess.run([compiler, '-std=c++17', '-O3', '-ffast-math', '-pthread',
                    str(SRC / 'draw.cpp'), '-o', str(program)], check=True)
    draw_photographs(work)
    subprocess.run([str(program), str(work), str(width), str(samples), 'final'], check=True)
    grade(work, 'final', 'print', scale=3)
    shutil.copyfile(work / 'print.png', output / 'Still-Running-native.png')
    shutil.copyfile(work / 'print-large.png', output / 'Still-Running.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path.cwd())
    parser.add_argument('--work', type=Path, help='Keep intermediate plates and radiance buffers here.')
    parser.add_argument('--width', type=int, default=528)
    parser.add_argument('--samples', type=int, choices=[1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 144], default=144)
    args = parser.parse_args()
    if args.width < 16:
        parser.error('Width must be at least 16 pixels.')
    if args.work:
        render(args.work.resolve(), args.output.resolve(), args.width, args.samples)
    else:
        with TemporaryDirectory(prefix='still-running-') as temp:
            render(Path(temp), args.output.resolve(), args.width, args.samples)


if __name__ == '__main__':
    main()
