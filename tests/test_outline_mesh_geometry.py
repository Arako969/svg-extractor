import re
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

        deviations = []

        for p1, c1, c2, p2 in extractor._closed_curve_segments(
            anchors, tension=tension,
        ):
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

    def test_svg_and_mesh_share_segments_with_irregular_and_duplicate_anchors(self):
        extractor = object.__new__(ColoringRegionExtractor)
        anchors = np.asarray([
            [0.0, 0.0], [12.0, 0.0], [12.00000001, 0.0],
            [12.4, 0.8], [8.0, 10.0], [0.0, 8.0], [0.0, 0.0],
        ])
        segments = extractor._closed_curve_segments(anchors)
        self.assertEqual(len(segments), 5)
        self.assertTrue(np.isfinite(np.asarray(segments)).all())
        for previous, current in zip(segments, segments[1:] + segments[:1]):
            np.testing.assert_allclose(previous[3], current[0], atol=0)
        path = extractor._closed_catmull_rom_svg_path(anchors)
        self.assertEqual(path.count(" C "), len(segments))
        sampled = extractor._sample_closed_catmull_rom(anchors)
        self.assertTrue(np.isfinite(sampled).all())
        for start, _, _, _ in segments:
            self.assertLessEqual(_distance_to_closed_polyline(start, sampled), 1e-9)

    def test_straight_supported_corners_are_kept_but_round_arcs_are_not(self):
        extractor = object.__new__(ColoringRegionExtractor)
        rectangle = np.asarray(
            [(x, 0.0) for x in range(0, 41, 2)]
            + [(40.0, y) for y in range(2, 21, 2)]
            + [(x, 20.0) for x in range(38, -1, -2)]
            + [(0.0, y) for y in range(18, 0, -2)],
            dtype=np.float64,
        )
        circle = np.asarray([
            [20.0 + 20.0 * np.cos(a), 20.0 + 20.0 * np.sin(a)]
            for a in np.linspace(0.0, 2.0 * np.pi, 80, endpoint=False)
        ])
        corner_indices = extractor._hard_corner_indices(rectangle)
        self.assertEqual(len(corner_indices), 4)
        self.assertEqual(extractor._hard_corner_indices(circle), [])
        corners = rectangle[corner_indices]
        segments = extractor._closed_curve_segments(
            rectangle, hard_corners=corners,
        )
        for index in corner_indices:
            previous = segments[(index - 1) % len(segments)]
            following = segments[index]
            # The two handles follow their own edge at a deliberate corner.
            self.assertLessEqual(
                extractor._point_segment_distance(previous[2], previous[0], previous[3]),
                1e-9,
            )
            self.assertLessEqual(
                extractor._point_segment_distance(following[1], following[0], following[3]),
                1e-9,
            )

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
                [16.0 * np.cos(theta), 12.0 * np.sin(theta)]
                for theta in np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
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

    def test_svg_and_mesh_rings_start_on_the_same_contours(self):
        line_mask = np.zeros((96, 96), dtype=np.uint8)
        cv2.circle(line_mask, (48, 48), 30, 255, 8, lineType=cv2.LINE_8)
        extractor = _extractor_with_line_mask(line_mask)
        path = extractor._outline_svg_path_data()
        rings, _ = extractor._outline_mesh_rings()
        starts = np.asarray([
            (float(x), float(y))
            for x, y in re.findall(r"\bM (-?\d+\.\d+),(-?\d+\.\d+)", path)
        ])
        self.assertEqual(len(starts), len(rings))
        for start, ring in zip(starts, rings.values()):
            np.testing.assert_allclose(start, ring[0], rtol=0.0, atol=0.01)

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
