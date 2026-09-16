#!/usr/bin/env python3
"""
Coloring Region Extractor
GUI tool for detecting closed coloring-book regions and exporting them as SVG.

Requirements:
    pip install opencv-python pillow numpy

Run:
    python3 coloring_region_extractor_gui.py
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageTk


class ColoringRegionExtractor(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Coloring Region Extractor")
        self.geometry("1320x860")
        self.minsize(980, 700)

        self.image_path: Path | None = None
        self.original_bgr: np.ndarray | None = None
        self.gray: np.ndarray | None = None

        self.line_mask: np.ndarray | None = None
        self.labels: np.ndarray | None = None
        self.regions: list[dict] = []

        self.preview_rgb: np.ndarray | None = None
        self.preview_photo: ImageTk.PhotoImage | None = None

        self.display_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0

        self.threshold_var = tk.IntVar(value=190)
        self.close_size_var = tk.IntVar(value=3)
        self.min_area_var = tk.IntVar(value=150)
        self.simplify_var = tk.DoubleVar(value=1.5)

        self.show_numbers_var = tk.BooleanVar(value=True)
        self.show_inactive_var = tk.BooleanVar(value=True)

        self.status_var = tk.StringVar(value="Bitte ein Bild öffnen.")
        self.region_count_var = tk.StringVar(value="Regionen: 0")
        self.active_count_var = tk.StringVar(value="Aktiv: 0")

        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        left = ttk.Frame(root, width=300)
        left.pack(side="left", fill="y", padx=(0, 10))

        right = ttk.Frame(root)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="Coloring Region Extractor",
                  font=("Helvetica", 17, "bold")).pack(anchor="w", pady=(0, 12))

        ttk.Button(left, text="Bild öffnen", command=self.open_image).pack(fill="x", pady=4)
        ttk.Button(left, text="Neu analysieren", command=self.analyze).pack(fill="x", pady=4)

        ttk.Separator(left).pack(fill="x", pady=12)

        self._add_slider(
            left,
            "Schwarz/Weiß-Schwelle",
            self.threshold_var,
            50,
            245,
            1,
        )

        self._add_slider(
            left,
            "Lücken schließen",
            self.close_size_var,
            1,
            15,
            2,
        )

        self._add_slider(
            left,
            "Min. Flächengröße",
            self.min_area_var,
            10,
            5000,
            10,
        )

        self._add_slider(
            left,
            "Pfad-Vereinfachung",
            self.simplify_var,
            0.2,
            8.0,
            0.1,
        )

        ttk.Checkbutton(
            left,
            text="Regionsnummern anzeigen",
            variable=self.show_numbers_var,
            command=self.refresh_preview,
        ).pack(anchor="w", pady=(10, 2))

        ttk.Checkbutton(
            left,
            text="Deaktivierte Regionen anzeigen",
            variable=self.show_inactive_var,
            command=self.refresh_preview,
        ).pack(anchor="w", pady=2)

        ttk.Separator(left).pack(fill="x", pady=12)

        ttk.Label(left, textvariable=self.region_count_var).pack(anchor="w")
        ttk.Label(left, textvariable=self.active_count_var).pack(anchor="w", pady=(2, 10))

        ttk.Label(
            left,
            text=(
                "Bedienung:\n"
                "• Vorschau anklicken: Region an/aus\n"
                "• Regler ändern\n"
                "• Neu analysieren\n"
                "• SVG exportieren"
            ),
            justify="left",
        ).pack(anchor="w", pady=(4, 12))

        ttk.Button(left, text="Alle aktivieren", command=self.activate_all).pack(fill="x", pady=3)
        ttk.Button(left, text="Alle deaktivieren", command=self.deactivate_all).pack(fill="x", pady=3)

        ttk.Separator(left).pack(fill="x", pady=12)

        ttk.Button(left, text="SVG exportieren", command=self.export_svg).pack(fill="x", pady=4)
        ttk.Button(left, text="Vorschau speichern", command=self.export_preview).pack(fill="x", pady=4)
        ttk.Button(left, text="JSON speichern", command=self.export_json).pack(fill="x", pady=4)

        ttk.Label(
            left,
            textvariable=self.status_var,
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(18, 0))

        canvas_frame = ttk.Frame(right)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#2b2b2b",
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", lambda _event: self.refresh_preview())

    def _add_slider(self, parent, label, variable, minimum, maximum, resolution):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=6)

        header = ttk.Frame(frame)
        header.pack(fill="x")

        ttk.Label(header, text=label).pack(side="left")
        value_label = ttk.Label(header, width=7, anchor="e")
        value_label.pack(side="right")

        scale = ttk.Scale(
            frame,
            from_=minimum,
            to=maximum,
            variable=variable,
            orient="horizontal",
        )
        scale.pack(fill="x", pady=(3, 0))

        def update_value(*_):
            value = variable.get()
            if isinstance(variable, tk.DoubleVar):
                value_label.configure(text=f"{value:.1f}")
            else:
                # Keep odd kernel sizes for morphology
                if variable is self.close_size_var:
                    value = int(round(value))
                    if value < 1:
                        value = 1
                    if value % 2 == 0:
                        value += 1
                    variable.set(value)
                value_label.configure(text=str(int(round(value))))

        variable.trace_add("write", update_value)
        update_value()

    def open_image(self):
        file_name = filedialog.askopenfilename(
            title="Coloring-Bild öffnen",
            filetypes=[
                ("Bilder", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if not file_name:
            return

        image_path = Path(file_name)
        bgr = cv2.imread(str(image_path))
        if bgr is None:
            messagebox.showerror("Fehler", "Das Bild konnte nicht geöffnet werden.")
            return

        self.image_path = image_path
        self.original_bgr = bgr
        self.gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        self.status_var.set(f"Geladen: {image_path.name}")
        self.analyze()

    def analyze(self):
        if self.gray is None:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Bild öffnen.")
            return

        threshold = int(self.threshold_var.get())
        close_size = int(self.close_size_var.get())
        min_area = int(self.min_area_var.get())
        simplify = float(self.simplify_var.get())

        if close_size < 1:
            close_size = 1
        if close_size % 2 == 0:
            close_size += 1
            self.close_size_var.set(close_size)

        # Black pixels become the line mask.
        line = (self.gray < threshold).astype(np.uint8) * 255

        if close_size > 1:
            kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (close_size, close_size),
            )
            line = cv2.morphologyEx(line, cv2.MORPH_CLOSE, kernel)

        self.line_mask = line

        white = cv2.bitwise_not(line)
        binary = (white > 0).astype(np.uint8)

        count, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary,
            connectivity=8,
        )
        self.labels = labels

        border_labels = set(
            np.unique(
                np.concatenate(
                    [
                        labels[0, :],
                        labels[-1, :],
                        labels[:, 0],
                        labels[:, -1],
                    ]
                )
            ).tolist()
        )

        old_states = {
            r["source_label"]: r.get("active", True)
            for r in self.regions
        }

        regions = []

        for label_id in range(1, count):
            area = int(stats[label_id, cv2.CC_STAT_AREA])

            if area < min_area:
                continue

            # Regions touching the image edge are treated as open background.
            if label_id in border_labels:
                continue

            region_mask = np.zeros_like(binary, dtype=np.uint8)
            region_mask[labels == label_id] = 255

            contours, _ = cv2.findContours(
                region_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            if not contours:
                continue

            contour = max(contours, key=cv2.contourArea)
            approx = cv2.approxPolyDP(contour, simplify, True)
            points = approx.reshape(-1, 2)

            if len(points) < 3:
                continue

            x = int(stats[label_id, cv2.CC_STAT_LEFT])
            y = int(stats[label_id, cv2.CC_STAT_TOP])
            w = int(stats[label_id, cv2.CC_STAT_WIDTH])
            h = int(stats[label_id, cv2.CC_STAT_HEIGHT])

            regions.append(
                {
                    "source_label": label_id,
                    "area": area,
                    "bbox": [x, y, w, h],
                    "centroid": [
                        float(centroids[label_id][0]),
                        float(centroids[label_id][1]),
                    ],
                    "points": points.tolist(),
                    "active": old_states.get(label_id, True),
                }
            )

        regions.sort(key=lambda item: item["area"], reverse=True)

        for index, region in enumerate(regions, start=1):
            region["id"] = index

        self.regions = regions

        self.status_var.set(
            f"Analyse abgeschlossen: {len(regions)} Regionen erkannt."
        )
        self._update_counts()
        self.refresh_preview()

    def _update_counts(self):
        total = len(self.regions)
        active = sum(1 for r in self.regions if r["active"])
        self.region_count_var.set(f"Regionen: {total}")
        self.active_count_var.set(f"Aktiv: {active}")

    @staticmethod
    def _region_color(index):
        palette = [
            (246, 189, 96),
            (132, 165, 157),
            (242, 132, 130),
            (108, 138, 228),
            (184, 199, 122),
            (167, 139, 250),
            (100, 181, 166),
            (233, 163, 193),
            (230, 194, 41),
            (127, 176, 105),
            (244, 162, 97),
            (141, 153, 174),
        ]
        return palette[index % len(palette)]

    def make_preview(self):
        if self.original_bgr is None or self.labels is None or self.line_mask is None:
            return None

        height, width = self.labels.shape
        preview = np.full((height, width, 3), 255, dtype=np.uint8)

        for index, region in enumerate(self.regions):
            mask = self.labels == region["source_label"]

            if region["active"]:
                color = self._region_color(index)
                preview[mask] = np.array(color, dtype=np.uint8)
            elif self.show_inactive_var.get():
                preview[mask] = (235, 235, 235)

        # Original/detected line work on top
        preview[self.line_mask > 0] = (25, 25, 25)

        if self.show_numbers_var.get():
            for region in self.regions:
                if not region["active"]:
                    continue

                # Keep labels readable by not numbering tiny areas.
                if region["area"] < max(500, int(self.min_area_var.get()) * 2):
                    continue

                cx, cy = map(int, region["centroid"])
                text = str(region["id"])

                cv2.circle(preview, (cx, cy), 13, (255, 255, 255), -1)
                cv2.circle(preview, (cx, cy), 13, (30, 30, 30), 1)

                size = cv2.getTextSize(
                    text,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.42,
                    1,
                )[0]

                cv2.putText(
                    preview,
                    text,
                    (cx - size[0] // 2, cy + size[1] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.42,
                    (25, 25, 25),
                    1,
                    cv2.LINE_AA,
                )

        self.preview_rgb = preview
        return preview

    def refresh_preview(self):
        preview = self.make_preview()
        if preview is None:
            self.canvas.delete("all")
            return

        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())

        image_h, image_w = preview.shape[:2]

        scale = min(
            canvas_w / image_w,
            canvas_h / image_h,
        )
        scale = max(scale, 0.01)

        display_w = max(1, int(image_w * scale))
        display_h = max(1, int(image_h * scale))

        pil = Image.fromarray(preview)
        pil = pil.resize(
            (display_w, display_h),
            Image.Resampling.LANCZOS,
        )

        self.preview_photo = ImageTk.PhotoImage(pil)

        self.display_scale = scale
        self.display_offset_x = (canvas_w - display_w) // 2
        self.display_offset_y = (canvas_h - display_h) // 2

        self.canvas.delete("all")
        self.canvas.create_image(
            self.display_offset_x,
            self.display_offset_y,
            image=self.preview_photo,
            anchor="nw",
        )

    def on_canvas_click(self, event):
        if self.labels is None or self.display_scale <= 0:
            return

        image_x = int(
            (event.x - self.display_offset_x) / self.display_scale
        )
        image_y = int(
            (event.y - self.display_offset_y) / self.display_scale
        )

        height, width = self.labels.shape

        if not (0 <= image_x < width and 0 <= image_y < height):
            return

        clicked_label = int(self.labels[image_y, image_x])

        for region in self.regions:
            if region["source_label"] == clicked_label:
                region["active"] = not region["active"]
                state = "aktiviert" if region["active"] else "deaktiviert"
                self.status_var.set(
                    f"Region {region['id']} {state}, Fläche: {region['area']} px."
                )
                self._update_counts()
                self.refresh_preview()
                return

        self.status_var.set("An dieser Stelle gibt es keine exportierbare Region.")

    def activate_all(self):
        for region in self.regions:
            region["active"] = True
        self._update_counts()
        self.refresh_preview()

    def deactivate_all(self):
        for region in self.regions:
            region["active"] = False
        self._update_counts()
        self.refresh_preview()

    def export_svg(self):
        if not self.regions or self.labels is None:
            messagebox.showinfo("Hinweis", "Es gibt noch keine Regionen zum Exportieren.")
            return

        initial = (
            f"{self.image_path.stem}_game_areas.svg"
            if self.image_path
            else "game_areas.svg"
        )

        file_name = filedialog.asksaveasfilename(
            title="SVG speichern",
            defaultextension=".svg",
            initialfile=initial,
            filetypes=[("SVG", "*.svg")],
        )
        if not file_name:
            return

        height, width = self.labels.shape

        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}">',
            '<g id="game_areas">',
        ]

        export_index = 1

        for region in self.regions:
            if not region["active"]:
                continue

            points = region["points"]

            d = (
                "M "
                + " ".join(
                    f"{float(x):.2f},{float(y):.2f}"
                    for x, y in points
                )
                + " Z"
            )

            parts.append(
                f'<path '
                f'id="region_{export_index:03d}" '
                f'data-region-id="{export_index:03d}" '
                f'data-source-region="{region["id"]}" '
                f'data-area="{region["area"]}" '
                f'd="{d}" fill="#d9d9d9" stroke="none"/>'
            )

            export_index += 1

        parts.extend(["</g>", "</svg>"])

        Path(file_name).write_text(
            "\n".join(parts),
            encoding="utf-8",
        )

        self.status_var.set(
            f"SVG gespeichert: {Path(file_name).name}"
        )

    def export_preview(self):
        preview = self.make_preview()
        if preview is None:
            messagebox.showinfo("Hinweis", "Noch keine Vorschau vorhanden.")
            return

        initial = (
            f"{self.image_path.stem}_preview.png"
            if self.image_path
            else "region_preview.png"
        )

        file_name = filedialog.asksaveasfilename(
            title="Vorschau speichern",
            defaultextension=".png",
            initialfile=initial,
            filetypes=[("PNG", "*.png")],
        )
        if not file_name:
            return

        Image.fromarray(preview).save(file_name)
        self.status_var.set(
            f"Vorschau gespeichert: {Path(file_name).name}"
        )

    def export_json(self):
        if self.labels is None:
            messagebox.showinfo("Hinweis", "Noch keine Analyse vorhanden.")
            return

        initial = (
            f"{self.image_path.stem}_regions.json"
            if self.image_path
            else "regions.json"
        )

        file_name = filedialog.asksaveasfilename(
            title="JSON speichern",
            defaultextension=".json",
            initialfile=initial,
            filetypes=[("JSON", "*.json")],
        )
        if not file_name:
            return

        height, width = self.labels.shape

        data = {
            "source": self.image_path.name if self.image_path else None,
            "width": width,
            "height": height,
            "parameters": {
                "threshold": int(self.threshold_var.get()),
                "close_size": int(self.close_size_var.get()),
                "min_area": int(self.min_area_var.get()),
                "simplify_epsilon": float(self.simplify_var.get()),
            },
            "regions": [
                {
                    "id": region["id"],
                    "active": region["active"],
                    "area": region["area"],
                    "bbox": region["bbox"],
                    "centroid": region["centroid"],
                    "points": region["points"],
                }
                for region in self.regions
            ],
        }

        Path(file_name).write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        self.status_var.set(
            f"JSON gespeichert: {Path(file_name).name}"
        )


if __name__ == "__main__":
    app = ColoringRegionExtractor()
    app.mainloop()
