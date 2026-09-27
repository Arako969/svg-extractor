import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from coloring_region_extractor_gui import ColoringRegionExtractor


class _Value:
    """Minimaler Ersatz fuer eine Tkinter-Variable in Headless-Tests."""

    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


def _extractor_with_line_mask(line_mask, tolerance=0.60):
    extractor = object.__new__(ColoringRegionExtractor)
    extractor.line_mask = line_mask
    extractor.svg_outline_tolerance_var = _Value(tolerance)
    return extractor


def _signed_double_area(a, b, c):
    return (
        (b[0] - a[0]) * (c[1] - a[1])
        - (b[1] - a[1]) * (c[0] - a[0])
    )


def _point_in_triangle(point, a, b, c, epsilon=1e-9):
    d1 = _signed_double_area(point, a, b)
    d2 = _signed_double_area(point, b, c)
    d3 = _signed_double_area(point, c, a)

    has_negative = d1 < -epsilon or d2 < -epsilon or d3 < -epsilon
    has_positive = d1 > epsilon or d2 > epsilon or d3 > epsilon
    return not (has_negative and has_positive)


def _mesh_covers_point(vertices, triangles, point):
    point = np.asarray(point, dtype=np.float64)
    return any(
        _point_in_triangle(
            point,
            vertices[a],
            vertices[b],
            vertices[c],
        )
        for a, b, c in triangles
    )


def _point_segment_distance(point, start, end):
    segment = end - start
    denominator = float(np.dot(segment, segment))

    if denominator <= 1e-12:
        return float(np.linalg.norm(point - start))

    position = float(np.dot(point - start, segment) / denominator)
    position = max(0.0, min(1.0, position))
    projection = start + position * segment
    return float(np.linalg.norm(point - projection))


def _distance_to_closed_polyline(point, polyline):
    return min(
        _point_segment_distance(
            point,
            polyline[index],
            polyline[(index + 1) % len(polyline)],
        )
        for index in range(len(polyline))
    )


class OutlineMeshGeometryTests(unittest.TestCase):
    def test_catmull_rom_sampling_is_deterministic_and_finite(self):
        extractor = object.__new__(ColoringRegionExtractor)
        anchors = np.asarray(
            [
                [0.0, 0.0],
                [16.0, 1.0],
                [14.0, 11.0],
                [2.0, 14.0],
            ],
            dtype=np.float64,
        )

        first = extractor._sample_closed_catmull_rom(anchors, tension=0.44)
        second = extractor._sample_closed_catmull_rom(anchors, tension=0.44)

        self.assertGreaterEqual(len(first), len(anchors))
        self.assertTrue(np.isfinite(first).all())
        np.testing.assert_allclose(first, second, rtol=0.0, atol=0.0)

    def test_adaptive_sampling_stays_within_zoom_error_budget(self):
        extractor = object.__new__(ColoringRegionExtractor)
        anchors = np.asarray(
            [
                [0.0, 0.0],
                [16.0, 1.0],
                [14.0, 11.0],
                [2.0, 14.0],
            ],
            dtype=np.float64,
        )
        tension = 0.44
        sampled = extractor._sample_closed_catmull_rom(
            anchors,
            tension=tension,
            max_error=0.02,
        )

        factor = tension / 6.0
        deviations = []

        for index in range(len(anchors)):
            p0 = anchors[(index - 1) % len(anchors)]
            p1 = anchors[index]
            p2 = anchors[(index + 1) % len(anchors)]
            p3 = anchors[(index + 2) % len(anchors)]
            c1 = p1 + (p2 - p0) * factor
            c2 = p2 - (p3 - p1) * factor

            for parameter in np.linspace(0.0, 1.0, 201):
                inverse = 1.0 - parameter
                curve_point = (
                    (inverse ** 3) * p1
                    + 3.0 * (inverse ** 2) * parameter * c1
                    + 3.0 * inverse * (parameter ** 2) * c2
                    + (parameter ** 3) * p2
                )
                deviations.append(
                    _distance_to_closed_polyline(curve_point, sampled)
                )

        self.assertLessEqual(max(deviations), 0.02)

    def test_adaptive_sampling_uses_more_points_for_curved_segments(self):
        extractor = object.__new__(ColoringRegionExtractor)

        straight = extractor._sample_cubic_bezier_adaptive(
            [0.0, 0.0],
            [3.0, 0.0],
            [7.0, 0.0],
            [10.0, 0.0],
            max_error=0.02,
        )
        curved = extractor._sample_cubic_bezier_adaptive(
            [0.0, 0.0],
            [0.0, 10.0],
            [10.0, 10.0],
            [10.0, 0.0],
            max_error=0.02,
        )

        self.assertEqual(len(straight), 2)
        self.assertGreater(len(curved), len(straight))
        np.testing.assert_allclose(straight[0], [0.0, 0.0])
        np.testing.assert_allclose(straight[-1], [10.0, 0.0])

    def test_smaller_error_budget_increases_sampling_density(self):
        extractor = object.__new__(ColoringRegionExtractor)
        anchors = np.asarray(
            [
                [0.0, 0.0],
                [16.0, 1.0],
                [14.0, 11.0],
                [2.0, 14.0],
            ],
            dtype=np.float64,
        )

        loose = extractor._sample_closed_catmull_rom(
            anchors,
            max_error=0.10,
        )
        strict = extractor._sample_closed_catmull_rom(
            anchors,
            max_error=0.02,
        )

        self.assertGreater(len(strict), len(loose))

    def test_empty_line_mask_creates_no_mesh(self):
        line_mask = np.zeros((64, 64), dtype=np.uint8)
        extractor = _extractor_with_line_mask(line_mask)

        mesh = extractor._outline_mesh_data()

        self.assertEqual(mesh["vertices"], [])
        self.assertEqual(mesh["indices"], [])

    def test_ring_mesh_is_valid_and_preserves_its_hole(self):
        line_mask = np.zeros((96, 96), dtype=np.uint8)
        cv2.circle(
            line_mask,
            (48, 48),
            30,
            255,
            8,
            lineType=cv2.LINE_8,
        )
        extractor = _extractor_with_line_mask(line_mask)

        mesh = extractor._outline_mesh_data()
        vertices = np.asarray(mesh["vertices"], dtype=np.float64)
        indices = np.asarray(mesh["indices"], dtype=np.int64)

        self.assertGreater(len(vertices), 0)
        self.assertGreater(len(indices), 0)
        self.assertEqual(len(indices) % 3, 0)
        self.assertTrue(np.isfinite(vertices).all())
        self.assertGreaterEqual(int(indices.min()), 0)
        self.assertLess(int(indices.max()), len(vertices))

        triangles = indices.reshape(-1, 3)
        for a, b, c in triangles:
            double_area = abs(
                _signed_double_area(
                    vertices[a],
                    vertices[b],
                    vertices[c],
                )
            )
            self.assertGreater(double_area, 1e-8)

        self.assertFalse(
            _mesh_covers_point(vertices, triangles, (48.0, 48.0)),
            "Die freie Mitte der Ringkontur darf nicht trianguliert werden.",
        )
        self.assertTrue(
            _mesh_covers_point(vertices, triangles, (48.0, 18.0)),
            "Die schwarze Ringkontur muss von Dreiecken abgedeckt werden.",
        )

    def test_binary_writer_matches_lcsm_v1_layout(self):
        extractor = object.__new__(ColoringRegionExtractor)
        known_mesh = {
            "vertices": [
                (1.25, 2.5),
                (8.0, 2.5),
                (1.25, 9.75),
            ],
            "indices": [0, 1, 2],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            json_path = Path(temporary_directory) / "sample_game.json"

            with patch.object(
                ColoringRegionExtractor,
                "_outline_mesh_data",
                return_value=known_mesh,
            ):
                metadata = extractor._write_outline_mesh_binary(json_path)

            mesh_path = Path(temporary_directory) / metadata["file"]
            payload = mesh_path.read_bytes()

        magic, version, vertex_count, index_count = struct.unpack_from(
            "<4sIII",
            payload,
            0,
        )
        vertices = struct.unpack_from("<6f", payload, 16)
        indices = struct.unpack_from("<3I", payload, 16 + 3 * 8)

        self.assertEqual(magic, b"LCSM")
        self.assertEqual(version, 1)
        self.assertEqual(vertex_count, 3)
        self.assertEqual(index_count, 3)
        self.assertEqual(indices, (0, 1, 2))
        np.testing.assert_allclose(
            np.asarray(vertices).reshape(-1, 2),
            np.asarray(known_mesh["vertices"]),
            rtol=0.0,
            atol=1e-7,
        )
        self.assertEqual(metadata["triangle_count"], 1)
        self.assertEqual(metadata["size_bytes"], len(payload))


if __name__ == "__main__":
    unittest.main()
