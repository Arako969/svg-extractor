#!/usr/bin/env python3
"""
Coloring Region Extractor v3

Features:
- Automatic closed-region detection
- Click to select regions
- Shift-click for multi-selection
- Create logical groups from multiple detected regions
- Assign color IDs
- Activate/deactivate regions
- Export SVG and JSON for later game import

Requirements:
    pip install opencv-python pillow numpy

Run:
    python3 coloring_region_extractor_gui_v3.py
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

        self.title("Coloring Region Extractor v3")
        self.geometry("1500x900")
        self.minsize(1100, 720)

        self.image_path: Path | None = None
        self.original_bgr: np.ndarray | None = None
        self.gray: np.ndarray | None = None

        self.line_mask: np.ndarray | None = None
        self.labels: np.ndarray | None = None

        self.regions: list[dict] = []
        self.selected_region_ids: set[int] = set()

        # group_id -> {"id": int, "name": str, "color_id": int, "region_ids": set[int]}
        self.groups: dict[int, dict] = {}
        self.next_group_id = 1

        self.preview_rgb: np.ndarray | None = None
        self.preview_photo: ImageTk.PhotoImage | None = None

        self.display_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0

        self.threshold_var = tk.IntVar(value=190)
        self.close_size_var = tk.IntVar(value=3)
        self.min_area_var = tk.IntVar(value=100)
        self.simplify_var = tk.DoubleVar(value=1.5)

        self.show_numbers_var = tk.BooleanVar(value=True)
        self.show_inactive_var = tk.BooleanVar(value=True)
        self.include_border_var = tk.BooleanVar(value=True)

        self.color_id_var = tk.IntVar(value=1)
        self.group_name_var = tk.StringVar(value="")

        self.status_var = tk.StringVar(value="Bitte ein Bild öffnen.")
        self.region_count_var = tk.StringVar(value="Regionen: 0")
        self.active_count_var = tk.StringVar(value="Aktiv: 0")
        self.selected_count_var = tk.StringVar(value="Ausgewählt: 0")
        self.group_count_var = tk.StringVar(value="Gruppen: 0")

        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        left = ttk.Frame(root, width=330)
        left.pack(side="left", fill="y", padx=(0, 10))

        right = ttk.Frame(root)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(
            left,
            text="Coloring Region Extractor",
            font=("Helvetica", 17, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        ttk.Button(left, text="Bild öffnen", command=self.open_image).pack(fill="x", pady=3)
        ttk.Button(left, text="Neu analysieren", command=self.analyze).pack(fill="x", pady=3)

        ttk.Separator(left).pack(fill="x", pady=10)

        self._add_slider(left, "Schwarz/Weiß-Schwelle", self.threshold_var, 50, 245)
        self._add_slider(left, "Lücken schließen", self.close_size_var, 1, 15)
        self._add_slider(left, "Min. Flächengröße", self.min_area_var, 10, 5000)
        self._add_slider(left, "Pfad-Vereinfachung", self.simplify_var, 0.2, 8.0, is_float=True)

        ttk.Checkbutton(
            left,
            text="Regionsnummern anzeigen",
            variable=self.show_numbers_var,
            command=self.refresh_preview,
        ).pack(anchor="w", pady=2)

        ttk.Checkbutton(
            left,
            text="Deaktivierte Regionen anzeigen",
            variable=self.show_inactive_var,
            command=self.refresh_preview,
        ).pack(anchor="w", pady=2)

        ttk.Checkbutton(
            left,
            text="Bildrand als Grenze verwenden",
            variable=self.include_border_var,
        ).pack(anchor="w", pady=2)

        ttk.Separator(left).pack(fill="x", pady=10)

        stats = ttk.Frame(left)
        stats.pack(fill="x")
        ttk.Label(stats, textvariable=self.region_count_var).grid(row=0, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.active_count_var).grid(row=0, column=1, sticky="w", padx=(15,0))
        ttk.Label(stats, textvariable=self.selected_count_var).grid(row=1, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.group_count_var).grid(row=1, column=1, sticky="w", padx=(15,0))

        ttk.Separator(left).pack(fill="x", pady=10)

        ttk.Label(left, text="Auswahl und Gruppen", font=("Helvetica", 13, "bold")).pack(anchor="w")

        ttk.Label(
            left,
            text="Klick: einzelne Region auswählen\nShift + Klick: Auswahl erweitern oder entfernen",
            justify="left",
        ).pack(anchor="w", pady=(4, 8))

        ttk.Button(left, text="Auswahl löschen", command=self.clear_selection).pack(fill="x", pady=2)

        group_row = ttk.Frame(left)
        group_row.pack(fill="x", pady=(8, 3))
        ttk.Label(group_row, text="Gruppenname").pack(side="left")
        ttk.Entry(group_row, textvariable=self.group_name_var).pack(side="right", fill="x", expand=True, padx=(8,0))

        color_row = ttk.Frame(left)
        color_row.pack(fill="x", pady=3)
        ttk.Label(color_row, text="Farb-ID").pack(side="left")
        ttk.Spinbox(
            color_row,
            from_=1,
            to=999,
            textvariable=self.color_id_var,
            width=8,
        ).pack(side="right")

        ttk.Button(left, text="Gruppe aus Auswahl erstellen", command=self.create_group).pack(fill="x", pady=(6, 2))
        ttk.Button(left, text="Auswahl bestehender Gruppe hinzufügen", command=self.add_selection_to_group).pack(fill="x", pady=2)
        ttk.Button(left, text="Auswahl aus Gruppen entfernen", command=self.remove_selection_from_groups).pack(fill="x", pady=2)

        ttk.Label(left, text="Gruppen").pack(anchor="w", pady=(10, 3))

        group_list_frame = ttk.Frame(left)
        group_list_frame.pack(fill="both", expand=False)

        self.group_list = tk.Listbox(group_list_frame, height=9, exportselection=False)
        self.group_list.pack(side="left", fill="both", expand=True)
        group_scroll = ttk.Scrollbar(group_list_frame, orient="vertical", command=self.group_list.yview)
        group_scroll.pack(side="right", fill="y")
        self.group_list.configure(yscrollcommand=group_scroll.set)
        self.group_list.bind("<<ListboxSelect>>", self.on_group_selected)

        ttk.Button(left, text="Gewählte Gruppe aktualisieren", command=self.update_selected_group).pack(fill="x", pady=(4,2))
        ttk.Button(left, text="Gewählte Gruppe löschen", command=self.delete_selected_group).pack(fill="x", pady=2)

        ttk.Separator(left).pack(fill="x", pady=10)

        ttk.Button(left, text="Auswahl aktivieren", command=lambda: self.set_selection_active(True)).pack(fill="x", pady=2)
        ttk.Button(left, text="Auswahl deaktivieren", command=lambda: self.set_selection_active(False)).pack(fill="x", pady=2)
        ttk.Button(left, text="Alle aktivieren", command=self.activate_all).pack(fill="x", pady=2)

        ttk.Separator(left).pack(fill="x", pady=10)

        ttk.Button(left, text="SVG exportieren", command=self.export_svg).pack(fill="x", pady=3)
        ttk.Button(left, text="JSON speichern", command=self.export_json).pack(fill="x", pady=3)
        ttk.Button(left, text="Vorschau speichern", command=self.export_preview).pack(fill="x", pady=3)

        ttk.Label(
            left,
            textvariable=self.status_var,
            wraplength=310,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))

        self.canvas = tk.Canvas(
            right,
            bg="#2b2b2b",
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", lambda _e: self.refresh_preview())

    def _add_slider(self, parent, label, variable, minimum, maximum, is_float=False):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=4)

        header = ttk.Frame(frame)
        header.pack(fill="x")
        ttk.Label(header, text=label).pack(side="left")
        value_label = ttk.Label(header, width=8, anchor="e")
        value_label.pack(side="right")

        scale = ttk.Scale(frame, from_=minimum, to=maximum, variable=variable, orient="horizontal")
        scale.pack(fill="x", pady=(2,0))

        def update(*_):
            if is_float:
                value_label.configure(text=f"{float(variable.get()):.1f}")
            else:
                val = int(round(variable.get()))
                if variable is self.close_size_var:
                    if val < 1:
                        val = 1
                    if val % 2 == 0:
                        val += 1
                    variable.set(val)
                value_label.configure(text=str(val))

        variable.trace_add("write", update)
        update()

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

        bgr = cv2.imread(file_name)
        if bgr is None:
            messagebox.showerror("Fehler", "Das Bild konnte nicht geöffnet werden.")
            return

        self.image_path = Path(file_name)
        self.original_bgr = bgr
        self.gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        self.groups.clear()
        self.next_group_id = 1
        self.selected_region_ids.clear()

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

        count, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
        self.labels = labels

        border_labels = set(
            np.unique(
                np.concatenate([
                    labels[0, :],
                    labels[-1, :],
                    labels[:, 0],
                    labels[:, -1],
                ])
            ).tolist()
        )

        old_active = {r["source_label"]: r.get("active", True) for r in self.regions}

        new_regions = []

        for label_id in range(1, count):
            area = int(stats[label_id, cv2.CC_STAT_AREA])

            if area < min_area:
                continue

            if (not self.include_border_var.get()) and label_id in border_labels:
                continue

            mask = np.zeros_like(binary, dtype=np.uint8)
            mask[labels == label_id] = 255

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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

            new_regions.append({
                "source_label": label_id,
                "area": area,
                "bbox": [x, y, w, h],
                "centroid": [float(centroids[label_id][0]), float(centroids[label_id][1])],
                "points": points.tolist(),
                "active": old_active.get(label_id, True),
            })

        new_regions.sort(key=lambda r: r["area"], reverse=True)

        for idx, region in enumerate(new_regions, start=1):
            region["id"] = idx

        self.regions = new_regions
        self.selected_region_ids.clear()

        # Existing groups become invalid after re-analysis, because region IDs may change.
        self.groups.clear()
        self.next_group_id = 1

        self._refresh_group_list()
        self._update_counts()
        self.refresh_preview()
        self.status_var.set(f"Analyse abgeschlossen: {len(self.regions)} Regionen erkannt.")

    def _update_counts(self):
        self.region_count_var.set(f"Regionen: {len(self.regions)}")
        self.active_count_var.set(f"Aktiv: {sum(1 for r in self.regions if r['active'])}")
        self.selected_count_var.set(f"Ausgewählt: {len(self.selected_region_ids)}")
        self.group_count_var.set(f"Gruppen: {len(self.groups)}")

    def _region_by_id(self, region_id):
        for region in self.regions:
            if region["id"] == region_id:
                return region
        return None

    def _group_for_region(self, region_id):
        for group in self.groups.values():
            if region_id in group["region_ids"]:
                return group
        return None

    @staticmethod
    def _palette_color(index):
        palette = [
            (246, 189, 96), (132, 165, 157), (242, 132, 130),
            (108, 138, 228), (184, 199, 122), (167, 139, 250),
            (100, 181, 166), (233, 163, 193), (230, 194, 41),
            (127, 176, 105), (244, 162, 97), (141, 153, 174),
            (92, 201, 160), (198, 134, 66), (115, 133, 213),
        ]
        return palette[index % len(palette)]

    def make_preview(self):
        if self.labels is None or self.line_mask is None:
            return None

        h, w = self.labels.shape
        preview = np.full((h, w, 3), 255, dtype=np.uint8)

        for region in self.regions:
            mask = self.labels == region["source_label"]
            group = self._group_for_region(region["id"])

            if not region["active"]:
                if self.show_inactive_var.get():
                    preview[mask] = (232, 232, 232)
                continue

            if group:
                color = self._palette_color(group["color_id"] - 1)
            else:
                color = self._palette_color(region["id"] - 1)

            preview[mask] = np.array(color, dtype=np.uint8)

        preview[self.line_mask > 0] = (25, 25, 25)

        # Selection overlay
        overlay = preview.copy()
        for region_id in self.selected_region_ids:
            region = self._region_by_id(region_id)
            if not region:
                continue
            mask = self.labels == region["source_label"]
            overlay[mask] = (255, 255, 255)
            contours, _ = cv2.findContours(
                mask.astype(np.uint8) * 255,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            cv2.drawContours(preview, contours, -1, (255, 0, 255), 4)

        if self.selected_region_ids:
            preview = cv2.addWeighted(preview, 0.72, overlay, 0.28, 0)

        if self.show_numbers_var.get():
            for region in self.regions:
                if not region["active"]:
                    continue
                if region["area"] < max(500, int(self.min_area_var.get()) * 2):
                    continue

                cx, cy = map(int, region["centroid"])
                group = self._group_for_region(region["id"])

                text = str(group["color_id"] if group else region["id"])

                cv2.circle(preview, (cx, cy), 13, (255,255,255), -1)
                cv2.circle(preview, (cx, cy), 13, (30,30,30), 1)

                ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)[0]
                cv2.putText(
                    preview,
                    text,
                    (cx - ts[0] // 2, cy + ts[1] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.42,
                    (25,25,25),
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
        h, w = preview.shape[:2]

        scale = max(0.01, min(canvas_w / w, canvas_h / h))
        disp_w = max(1, int(w * scale))
        disp_h = max(1, int(h * scale))

        pil = Image.fromarray(preview).resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(pil)

        self.display_scale = scale
        self.display_offset_x = (canvas_w - disp_w) // 2
        self.display_offset_y = (canvas_h - disp_h) // 2

        self.canvas.delete("all")
        self.canvas.create_image(
            self.display_offset_x,
            self.display_offset_y,
            image=self.preview_photo,
            anchor="nw",
        )

    def on_canvas_click(self, event):
        if self.labels is None:
            return

        x = int((event.x - self.display_offset_x) / self.display_scale)
        y = int((event.y - self.display_offset_y) / self.display_scale)

        h, w = self.labels.shape
        if not (0 <= x < w and 0 <= y < h):
            return

        source_label = int(self.labels[y, x])

        clicked = None
        for region in self.regions:
            if region["source_label"] == source_label:
                clicked = region
                break

        if not clicked:
            if not (event.state & 0x0001):
                self.selected_region_ids.clear()
                self._update_counts()
                self.refresh_preview()
            return

        shift_pressed = bool(event.state & 0x0001)

        if shift_pressed:
            if clicked["id"] in self.selected_region_ids:
                self.selected_region_ids.remove(clicked["id"])
            else:
                self.selected_region_ids.add(clicked["id"])
        else:
            self.selected_region_ids = {clicked["id"]}

        group = self._group_for_region(clicked["id"])
        if group:
            self.status_var.set(
                f"Region {clicked['id']} ausgewählt. Gruppe {group['id']}, Farb-ID {group['color_id']}."
            )
        else:
            self.status_var.set(f"Region {clicked['id']} ausgewählt.")

        self._update_counts()
        self.refresh_preview()

    def clear_selection(self):
        self.selected_region_ids.clear()
        self._update_counts()
        self.refresh_preview()

    def create_group(self):
        if not self.selected_region_ids:
            messagebox.showinfo("Hinweis", "Bitte zuerst mindestens eine Region auswählen.")
            return

        # Remove selected regions from any existing group first.
        self.remove_selection_from_groups(refresh=False)

        gid = self.next_group_id
        self.next_group_id += 1

        name = self.group_name_var.get().strip() or f"Gruppe {gid}"
        color_id = max(1, int(self.color_id_var.get()))

        self.groups[gid] = {
            "id": gid,
            "name": name,
            "color_id": color_id,
            "region_ids": set(self.selected_region_ids),
        }

        self.group_name_var.set("")
        self._refresh_group_list(select_group_id=gid)
        self._update_counts()
        self.refresh_preview()
        self.status_var.set(
            f"{name} erstellt mit {len(self.selected_region_ids)} Regionen und Farb-ID {color_id}."
        )

    def _selected_group_id(self):
        sel = self.group_list.curselection()
        if not sel:
            return None
        text = self.group_list.get(sel[0])
        try:
            return int(text.split("|")[0].strip())
        except Exception:
            return None

    def on_group_selected(self, _event=None):
        gid = self._selected_group_id()
        if gid is None or gid not in self.groups:
            return

        group = self.groups[gid]
        self.group_name_var.set(group["name"])
        self.color_id_var.set(group["color_id"])
        self.selected_region_ids = set(group["region_ids"])
        self._update_counts()
        self.refresh_preview()
        self.status_var.set(f"Gruppe {gid} ausgewählt.")

    def update_selected_group(self):
        gid = self._selected_group_id()
        if gid is None or gid not in self.groups:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Gruppe in der Liste auswählen.")
            return

        group = self.groups[gid]
        group["name"] = self.group_name_var.get().strip() or group["name"]
        group["color_id"] = max(1, int(self.color_id_var.get()))

        if self.selected_region_ids:
            # Replace group contents with current selection.
            for other_gid, other in self.groups.items():
                if other_gid != gid:
                    other["region_ids"] -= self.selected_region_ids
            group["region_ids"] = set(self.selected_region_ids)

        self._remove_empty_groups()
        self._refresh_group_list(select_group_id=gid)
        self._update_counts()
        self.refresh_preview()
        self.status_var.set(f"Gruppe {gid} aktualisiert.")

    def add_selection_to_group(self):
        gid = self._selected_group_id()
        if gid is None or gid not in self.groups:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Zielgruppe in der Liste auswählen.")
            return
        if not self.selected_region_ids:
            messagebox.showinfo("Hinweis", "Bitte Regionen auswählen.")
            return

        # A region belongs to only one logical group.
        for other_gid, other in self.groups.items():
            if other_gid != gid:
                other["region_ids"] -= self.selected_region_ids

        self.groups[gid]["region_ids"] |= self.selected_region_ids

        self._remove_empty_groups()
        self._refresh_group_list(select_group_id=gid)
        self._update_counts()
        self.refresh_preview()
        self.status_var.set("Ausgewählte Regionen wurden zur Gruppe hinzugefügt.")

    def remove_selection_from_groups(self, refresh=True):
        if not self.selected_region_ids:
            return

        for group in self.groups.values():
            group["region_ids"] -= self.selected_region_ids

        self._remove_empty_groups()

        if refresh:
            self._refresh_group_list()
            self._update_counts()
            self.refresh_preview()
            self.status_var.set("Ausgewählte Regionen wurden aus ihren Gruppen entfernt.")

    def delete_selected_group(self):
        gid = self._selected_group_id()
        if gid is None or gid not in self.groups:
            return

        name = self.groups[gid]["name"]
        del self.groups[gid]
        self.selected_region_ids.clear()
        self._refresh_group_list()
        self._update_counts()
        self.refresh_preview()
        self.status_var.set(f"{name} gelöscht.")

    def _remove_empty_groups(self):
        empty = [gid for gid, group in self.groups.items() if not group["region_ids"]]
        for gid in empty:
            del self.groups[gid]

    def _refresh_group_list(self, select_group_id=None):
        self.group_list.delete(0, tk.END)

        index_to_select = None

        for idx, gid in enumerate(sorted(self.groups)):
            group = self.groups[gid]
            self.group_list.insert(
                tk.END,
                f"{gid} | Farbe {group['color_id']} | {group['name']} | {len(group['region_ids'])} Regionen"
            )
            if gid == select_group_id:
                index_to_select = idx

        if index_to_select is not None:
            self.group_list.selection_set(index_to_select)
            self.group_list.see(index_to_select)

    def set_selection_active(self, active):
        if not self.selected_region_ids:
            return
        for rid in self.selected_region_ids:
            region = self._region_by_id(rid)
            if region:
                region["active"] = active
        self._update_counts()
        self.refresh_preview()

    def activate_all(self):
        for region in self.regions:
            region["active"] = True
        self._update_counts()
        self.refresh_preview()

    def export_svg(self):
        if self.labels is None:
            return

        path = filedialog.asksaveasfilename(
            title="SVG speichern",
            defaultextension=".svg",
            initialfile=(self.image_path.stem + "_game_areas.svg") if self.image_path else "game_areas.svg",
            filetypes=[("SVG", "*.svg")],
        )
        if not path:
            return

        h, w = self.labels.shape

        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
            '<g id="game_areas">',
        ]

        exported_regions = set()

        # Export groups first. Each group can contain multiple independent paths.
        for gid in sorted(self.groups):
            group = self.groups[gid]

            active_regions = [
                self._region_by_id(rid)
                for rid in sorted(group["region_ids"])
            ]
            active_regions = [r for r in active_regions if r and r["active"]]

            if not active_regions:
                continue

            safe_name = "".join(
                ch if ch.isalnum() or ch in "_-" else "_"
                for ch in group["name"]
            )

            parts.append(
                f'<g id="group_{gid:03d}" data-group-id="{gid}" '
                f'data-name="{safe_name}" data-color-id="{group["color_id"]}">'
            )

            for region in active_regions:
                exported_regions.add(region["id"])
                d = "M " + " ".join(
                    f"{float(x):.2f},{float(y):.2f}"
                    for x, y in region["points"]
                ) + " Z"

                parts.append(
                    f'<path id="group_{gid:03d}_region_{region["id"]:03d}" '
                    f'data-region-id="{region["id"]}" '
                    f'd="{d}" fill="#d9d9d9" stroke="none"/>'
                )

            parts.append("</g>")

        # Ungrouped active regions are exported as individual game areas.
        for region in self.regions:
            if not region["active"] or region["id"] in exported_regions:
                continue

            d = "M " + " ".join(
                f"{float(x):.2f},{float(y):.2f}"
                for x, y in region["points"]
            ) + " Z"

            parts.append(
                f'<g id="region_group_{region["id"]:03d}" '
                f'data-group-id="region_{region["id"]:03d}" '
                f'data-color-id="0">'
            )
            parts.append(
                f'<path id="region_{region["id"]:03d}" '
                f'data-region-id="{region["id"]}" '
                f'd="{d}" fill="#d9d9d9" stroke="none"/>'
            )
            parts.append("</g>")

        parts.extend(["</g>", "</svg>"])

        Path(path).write_text("\n".join(parts), encoding="utf-8")
        self.status_var.set(f"SVG gespeichert: {Path(path).name}")

    def export_json(self):
        if self.labels is None:
            return

        path = filedialog.asksaveasfilename(
            title="JSON speichern",
            defaultextension=".json",
            initialfile=(self.image_path.stem + "_areas.json") if self.image_path else "areas.json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return

        h, w = self.labels.shape

        data = {
            "source": self.image_path.name if self.image_path else None,
            "width": w,
            "height": h,
            "parameters": {
                "threshold": int(self.threshold_var.get()),
                "close_size": int(self.close_size_var.get()),
                "min_area": int(self.min_area_var.get()),
                "simplify_epsilon": float(self.simplify_var.get()),
                "include_border_regions": bool(self.include_border_var.get()),
            },
            "regions": [
                {
                    "id": r["id"],
                    "active": r["active"],
                    "area": r["area"],
                    "bbox": r["bbox"],
                    "centroid": r["centroid"],
                    "points": r["points"],
                }
                for r in self.regions
            ],
            "groups": [
                {
                    "id": group["id"],
                    "name": group["name"],
                    "color_id": group["color_id"],
                    "region_ids": sorted(group["region_ids"]),
                }
                for gid, group in sorted(self.groups.items())
            ],
        }

        Path(path).write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self.status_var.set(f"JSON gespeichert: {Path(path).name}")

    def export_preview(self):
        preview = self.make_preview()
        if preview is None:
            return

        path = filedialog.asksaveasfilename(
            title="Vorschau speichern",
            defaultextension=".png",
            initialfile=(self.image_path.stem + "_preview.png") if self.image_path else "preview.png",
            filetypes=[("PNG", "*.png")],
        )
        if not path:
            return

        Image.fromarray(preview).save(path)
        self.status_var.set(f"Vorschau gespeichert: {Path(path).name}")


if __name__ == "__main__":
    app = ColoringRegionExtractor()
    app.mainloop()
