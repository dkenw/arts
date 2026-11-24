"""Regressions for developing Edition 19 and replacing a harbour capture."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

import render
import surface_guides
from capture_passes import HALL_PASSES, print_passes
from concrete_wear import RELIEF_SITES, SITES, apply_surfaces
from harbour_plate import capture
from pixel import resolve


class PrintCapture(unittest.TestCase):
    def test_incomplete_capture_cannot_publish_edition_19(self):
        for large, missing_suffix in ((False, ".berth-concrete.npz"), (True, ".harbour-depth.npz")):
            with self.subTest(large=large), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                source = root / "exposure.png"
                output = root / "prints"
                for suffix in print_passes(large=large):
                    if suffix != missing_suffix:
                        source.with_suffix(suffix).touch()
                with self.assertRaisesRegex(ValueError, "Edition 19 capture is missing camera passes") as error:
                    resolve(source, output, large=large)
                self.assertIn(source.with_suffix(missing_suffix).name, str(error.exception))
                self.assertFalse(output.exists())

    def test_concrete_pass_with_only_relief_sites_is_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "exposure.concrete.npz"
            fields = dict(size=(1, 1), samples=1)
            for site in RELIEF_SITES:
                fields[site.name] = np.zeros((1, 1, 2), np.int16)
                fields[site.name + "_origin"] = (0, 0)
            np.savez(path, **fields)
            paint = mock.Mock()
            with self.assertRaisesRegex(ValueError, "missing surface fields .*ticket_fascia"):
                apply_surfaces(np.zeros((1, 1, 3), np.float32), path, SITES, paint)
            paint.assert_not_called()


class SurfaceRegistration(unittest.TestCase):
    def test_concrete_shows_through_the_clear_parts_of_an_existing_mark(self):
        from concrete_wear import Site

        with tempfile.TemporaryDirectory() as temp:
            site = Site("patch", 0, (0,0,0), (1,1,1), (0,1,0,1), (), 0)
            path = Path(temp)/"exposure.berth-concrete.npz"
            np.savez(path, size=(3,1), samples=1, patch=np.full((1,3,2), 500, dtype=np.int16),
                     patch_origin=(0,0), patch_through=np.array([[255,128,0]], dtype=np.uint8))
            rgb = np.full((1,3,3),100,dtype=np.float32)
            apply_surfaces(rgb,path,[site],lambda _: (np.full((2,2),20.), np.zeros((2,2))))
            delta = rgb[0,:,1]-100
            self.assertGreater(delta[0], 0)
            self.assertAlmostEqual(float(delta[1]/delta[0]),128/255,places=5)
            self.assertEqual(delta[2], 0)


class BatchPrinting(unittest.TestCase):
    def test_output_directory_by_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cases = (
                ([], "renders"),
                (["--proof"], "build/proof"),
                (["--from-exposures"], "build/archive-reprint"),
                (["--proof", "--output", str(root / "custom")], "custom"),
            )
            for flags, directory in cases:
                argv = ["render.py", "--blender", "blender", *flags]
                with (
                    self.subTest(flags=flags),
                    mock.patch.object(render, "HERE", root),
                    mock.patch.object(render, "expose"),
                    mock.patch.object(render, "write_prints", return_value=[]),
                    mock.patch.object(sys, "argv", argv),
                ):
                    render.main()
                    self.assertTrue((root / directory).is_dir())

    def test_failed_large_finish_preserves_the_previous_set(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            native = "No-Further-Sailings-19-528.png"
            tonal = "No-Further-Sailings-19-2112-tonal.png"
            indexed = "No-Further-Sailings-19-2112-80-colours.png"
            original = {name: name.encode() for name in (native, tonal, indexed)}
            for name, data in original.items():
                (folder / name).write_bytes(data)

            def interrupted(source, stage, *, large):
                if large:
                    (stage / tonal).write_bytes(b"incomplete large print")
                    raise ValueError("failed second finish")
                (stage / native).write_bytes(b"new native print")
                return [native]

            argv = ["render.py", "--from-exposures", "--output", str(folder)]
            with mock.patch("sys.argv", argv), mock.patch("render.write_prints", side_effect=interrupted):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    render.main()
            self.assertEqual({p.name: p.read_bytes() for p in folder.glob("*.png")}, original)


class CameraExposure(unittest.TestCase):
    def test_missing_guide_cannot_reuse_a_previous_render(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "exposure.png"
            previous = (target, target.with_suffix(".normal.png"), target.with_suffix(".albedo.png"))
            for path in previous:
                Image.new("RGB", (12, 8), (40, 40, 40)).save(path)
            approved = {path: path.read_bytes() for path in previous}

            def partial_render(bpy, scene, pending):
                for path in (pending, pending.with_suffix(".normal.png")):
                    Image.new("RGB", (12, 8), (150, 150, 150)).save(path)

            scene = mock.Mock()
            with mock.patch.dict(sys.modules, bpy=mock.Mock()), \
                 mock.patch.object(surface_guides, "_render_with_guides", side_effect=partial_render):
                with self.assertRaisesRegex(ValueError, r"Blender render .*exposure\.albedo\.png"):
                    surface_guides.expose(scene, target, large=True)
            self.assertEqual({path: path.read_bytes() for path in previous}, approved)


class HarbourRetakes(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.room = self.root / "room.png"
        self.retake = self.root / "harbour.png"
        self.output = self.root / "registered" / "exposure.png"
        for base, level in ((self.room, 40), (self.retake, 150)):
            for suffix in (".png", ".albedo.png", ".normal.png"):
                Image.new("RGB", (12, 8), (level, level, level)).save(base.with_suffix(suffix))
        aperture = np.zeros((8, 12), bool)
        aperture[2:6, 6:10] = True
        np.savez(self.retake.with_suffix(".aperture.npz"), aperture=aperture)
        # Registration carries these passes verbatim. Pixel development reads their contents.
        for suffix in (*HALL_PASSES, ".direct.png"):
            self.room.with_suffix(suffix).write_bytes(suffix.encode())
        self.retake.with_suffix(".harbour-depth.npz").write_bytes(b"registered distances")

    def snapshot(self):
        return {f.name: f.read_bytes() for f in self.output.parent.glob("exposure.*")}

    def capture(self, *, large=True):
        capture(self.room, self.retake, self.output, large=large)

    def test_failed_update_preserves_last_complete_take(self):
        self.capture()
        approved = self.snapshot()
        for source, suffix, label in ((self.room, ".drawdown.npz", "Hall capture"),
                                      (self.retake, ".harbour-depth.npz", "Harbour retake")):
            with self.subTest(suffix=suffix):
                path = source.with_suffix(suffix)
                data = path.read_bytes()
                path.unlink()
                with self.assertRaisesRegex(ValueError, rf"{label} .*{path.name}"):
                    self.capture()
                self.assertEqual(self.snapshot(), approved)
                path.write_bytes(data)

    def test_failed_publish_rolls_back_installed_channels(self):
        self.capture()
        approved = self.snapshot()
        self.room.with_suffix(".glass.png").write_bytes(b"next reflection")
        replace = Path.replace
        def fail_at_main(source, target):
            if source.name == self.output.name and source.parent.name != ".previous":
                raise OSError("simulated write failure")
            return replace(source, target)
        with mock.patch.object(Path, "replace", fail_at_main), self.assertRaises(OSError):
            self.capture()
        self.assertEqual(self.snapshot(), approved)

    def test_reused_stem_drops_only_its_obsolete_passes(self):
        self.capture()
        other = self.output.with_name("another.concrete.npz")
        other.write_bytes(b"another capture")
        self.capture(large=False)
        for suffix in (".normal.png", ".albedo.png", ".direct.png", ".harbour-depth.npz"):
            self.assertFalse(self.output.with_suffix(suffix).exists())
        for suffix in HALL_PASSES:
            self.assertTrue(self.output.with_suffix(suffix).exists())
        self.assertTrue(self.output.with_suffix(".frame.npz").exists())
        self.assertEqual(other.read_bytes(), b"another capture")
        with Image.open(self.output) as im:
            self.assertEqual(im.getpixel((0, 0)), (40, 40, 40))
            self.assertEqual(im.getpixel((8, 3)), (150, 150, 150))

    def test_inputs_cannot_be_overwritten_in_place(self):
        for existing in (self.room, self.retake):
            with self.subTest(existing=existing), self.assertRaisesRegex(ValueError, "both input"):
                capture(self.room, self.retake, existing, large=False)


if __name__ == "__main__":
    unittest.main()
