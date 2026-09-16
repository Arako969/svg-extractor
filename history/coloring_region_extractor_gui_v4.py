#!/usr/bin/env python3
"""
Coloring Region Extractor v4

New in v4:
- One logical group = one game area
- One label position per group
- Set label position by clicking in the image
- Highlight ungrouped active regions
- Save/load project JSON
- Export game SVG, game JSON, and outline PNG
- Group color IDs and names
- Multi-selection with Shift + click

Requirements:
    pip install opencv-python pillow numpy

Run:
    python3 coloring_region_extractor_gui_v4.py
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

        self.title("Coloring Region Extractor v4")
        self.geometry("1540x930")
        self.minsize(1150, 760)

        self.image_path: Path | None = None
        self.original_bgr: np.ndarray | None = None
        self.gray: np.ndarray | None = None

        self.line_mask: np.ndarray | None = None
        self.labels: np.ndarray | None = None
        self.regions: list[dict] = []

        self.selected_region_ids: set[int] = set()
        self.groups: dict[int, dict] = {}
        self.next_group_id = 1

        self.preview_photo: ImageTk.PhotoImage | None = None
        self.preview_rgb: np.ndarray | None = None
        self.display_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0

        self.threshold_var = tk.IntVar(value=190)
        self.close_size_var = tk.IntVar(value=3)
        self.min_area_var = tk.IntVar(value=100)
        self.simplify_var = tk.DoubleVar(value=1.5)

        self.include_border_var = tk.BooleanVar(value=True)
        self.show_numbers_var = tk.BooleanVar(value=True)
        self.show_inactive_var = tk.BooleanVar(value=True)
        self.highlight_ungrouped_var = tk.BooleanVar(value=True)

        self.color_id_var = tk.IntVar(value=1)
        self.group_name_var = tk.StringVar(value="")

        self.mode_var = tk.StringVar(value="select")

        self.status_var = tk.StringVar(value="Bitte ein Bild öffnen.")
        self.region_count_var = tk.StringVar(value="Regionen: 0")
        self.active_count_var = tk.StringVar(value="Aktiv: 0")
        self.selected_count_var = tk.StringVar(value="Ausgewählt: 0")
        self.group_count_var = tk.StringVar(value="Gruppen: 0")
        self.ungrouped_count_var = tk.StringVar(value="Ungegruppiert: 0")

        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        left = ttk.Frame(root, width=350)
        left.pack(side="left", fill="y", padx=(0, 10))

        right = ttk.Frame(root)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(
            left,
            text="Coloring Region Extractor",
            font=("Helvetica", 17, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        top_buttons = ttk.Frame(left)
        top_buttons.pack(fill="x")
        ttk.Button(top_buttons, text="Bild öffnen", command=self.open_image).pack(side="left", fill="x", expand=True, padx=(0,3))
        ttk.Button(top_buttons, text="Projekt laden", command=self.load_project).pack(side="left", fill="x", expand=True, padx=(3,0))

        ttk.Button(left, text="Projekt speichern", command=self.save_project).pack(fill="x", pady=(6,2))
        ttk.Button(left, text="Neu analysieren", command=self.analyze).pack(fill="x", pady=2)

        ttk.Separator(left).pack(fill="x", pady=10)

        self._add_slider(left, "Schwarz/Weiß-Schwelle", self.threshold_var, 50, 245)
        self._add_slider(left, "Lücken schließen", self.close_size_var, 1, 15)
        self._add_slider(left, "Min. Flächengröße", self.min_area_var, 10, 5000)
        self._add_slider(left, "Pfad-Vereinfachung", self.simplify_var, 0.2, 8.0, is_float=True)

        ttk.Checkbutton(left, text="Bildrand als Grenze verwenden", variable=self.include_border_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(left, text="Regions-/Farbnummern anzeigen", variable=self.show_numbers_var, command=self.refresh_preview).pack(anchor="w", pady=2)
        ttk.Checkbutton(left, text="Deaktivierte Regionen anzeigen", variable=self.show_inactive_var, command=self.refresh_preview).pack(anchor="w", pady=2)
        ttk.Checkbutton(left, text="Ungegruppierte Regionen markieren", variable=self.highlight_ungrouped_var, command=self.refresh_preview).pack(anchor="w", pady=2)

        ttk.Separator(left).pack(fill="x", pady=10)

        stats = ttk.Frame(left)
        stats.pack(fill="x")
        ttk.Label(stats, textvariable=self.region_count_var).grid(row=0, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.active_count_var).grid(row=0, column=1, sticky="w", padx=(12,0))
        ttk.Label(stats, textvariable=self.selected_count_var).grid(row=1, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.group_count_var).grid(row=1, column=1, sticky="w", padx=(12,0))
        ttk.Label(stats, textvariable=self.ungrouped_count_var).grid(row=2, column=0, columnspan=2, sticky="w")

        ttk.Separator(left).pack(fill="x", pady=10)

        ttk.Label(left, text="Werkzeug", font=("Helvetica", 13, "bold")).pack(anchor="w")

        modes = ttk.Frame(left)
        modes.pack(fill="x", pady=(4,6))
        ttk.Radiobutton(modes, text="Auswahl", value="select", variable=self.mode_var, command=self.refresh_preview).pack(side="left")
        ttk.Radiobutton(modes, text="Label setzen", value="label", variable=self.mode_var, command=self.refresh_preview).pack(side="left", padx=(10,0))

        ttk.Label(
            left,
            text=(
                "Auswahl: Klick wählt eine Region.\n"
                "Shift + Klick erweitert oder entfernt die Auswahl.\n"
                "Label setzen: Gruppe wählen und ins Bild klicken."
            ),
            justify="left",
        ).pack(anchor="w", pady=(0,8))

        ttk.Button(left, text="Auswahl löschen", command=self.clear_selection).pack(fill="x", pady=2)

        ttk.Separator(left).pack(fill="x", pady=10)

        ttk.Label(left, text="Gruppe / Game Area", font=("Helvetica", 13, "bold")).pack(anchor="w")

        row = ttk.Frame(left)
        row.pack(fill="x", pady=(5,2))
        ttk.Label(row, text="Name").pack(side="left")
        ttk.Entry(row, textvariable=self.group_name_var).pack(side="right", fill="x", expand=True, padx=(8,0))

        row = ttk.Frame(left)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Farb-ID").pack(side="left")
        ttk.Spinbox(row, from_=1, to=999, textvariable=self.color_id_var, width=8).pack(side="right")

        ttk.Button(left, text="Gruppe aus Auswahl erstellen", command=self.create_group).pack(fill="x", pady=(5,2))
        ttk.Button(left, text="Auswahl zur gewählten Gruppe", command=self.add_selection_to_group).pack(fill="x", pady=2)
        ttk.Button(left, text="Auswahl aus Gruppen entfernen", command=self.remove_selection_from_groups).pack(fill="x", pady=2)

        ttk.Label(left, text="Gruppen").pack(anchor="w", pady=(8,3))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill="x")

        self.group_list = tk.Listbox(list_frame, height=8, exportselection=False)
        self.group_list.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.group_list.yview)
        scroll.pack(side="right", fill="y")
        self.group_list.configure(yscrollcommand=scroll.set)
        self.group_list.bind("<<ListboxSelect>>", self.on_group_selected)

        ttk.Button(left, text="Gewählte Gruppe aktualisieren", command=self.update_selected_group).pack(fill="x", pady=(4,2))
        ttk.Button(left, text="Label automatisch zentrieren", command=self.auto_center_group_label).pack(fill="x", pady=2)
        ttk.Button(left, text="Gewählte Gruppe löschen", command=self.delete_selected_group).pack(fill="x", pady=2)

        ttk.Separator(left).pack(fill="x", pady=10)

        ttk.Button(left, text="Auswahl aktivieren", command=lambda: self.set_selection_active(True)).pack(fill="x", pady=2)
        ttk.Button(left, text="Auswahl deaktivieren", command=lambda: self.set_selection_active(False)).pack(fill="x", pady=2)
        ttk.Button(left, text="Alle aktivieren", command=self.activate_all).pack(fill="x", pady=2)

        ttk.Separator(left).pack(fill="x", pady=10)

        ttk.Button(left, text="Game SVG exportieren", command=self.export_svg).pack(fill="x", pady=2)
        ttk.Button(left, text="Game JSON exportieren", command=self.export_game_json).pack(fill="x", pady=2)
        ttk.Button(left, text="Outline PNG exportieren", command=self.export_outline_png).pack(fill="x", pady=2)
        ttk.Button(left, text="Vorschau speichern", command=self.export_preview).pack(fill="x", pady=2)

        ttk.Label(left, textvariable=self.status_var, wraplength=330, justify="left").pack(anchor="w", pady=(10,0))

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

        ttk.Scale(frame, from_=minimum, to=maximum, variable=variable, orient="horizontal").pack(fill="x")

        def update(*_):
            if is_float:
                value_label.config(text=f"{float(variable.get()):.1f}")
            else:
                value = int(round(variable.get()))
                if variable is self.close_size_var:
                    if value < 1:
                        value = 1
                    if value % 2 == 0:
                        value += 1
                    variable.set(value)
                value_label.config(text=str(value))

        variable.trace_add("write", update)
        update()

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Coloring-Bild öffnen",
            filetypes=[
                ("Bilder", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if not path:
            return

        bgr = cv2.imread(path)
        if bgr is None:
            messagebox.showerror("Fehler", "Bild konnte nicht geladen werden.")
            return

        self.image_path = Path(path)
        self.original_bgr = bgr
        self.gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        self.groups.clear()
        self.selected_region_ids.clear()
        self.next_group_id = 1
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
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_size, close_size))
            line = cv2.morphologyEx(line, cv2.MORPH_CLOSE, kernel)

        self.line_mask = line

        white = cv2.bitwise_not(line)
        binary = (white > 0).astype(np.uint8)

        count, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
        self.labels = labels

        border_labels = set(
            np.unique(np.concatenate([
                labels[0, :],
                labels[-1, :],
                labels[:, 0],
                labels[:, -1],
            ])).tolist()
        )

        old_active = {r["source_label"]: r.get("active", True) for r in self.regions}
        regions = []

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
            pts = approx.reshape(-1, 2)
            if len(pts) < 3:
                continue

            x = int(stats[label_id, cv2.CC_STAT_LEFT])
            y = int(stats[label_id, cv2.CC_STAT_TOP])
            w = int(stats[label_id, cv2.CC_STAT_WIDTH])
            h = int(stats[label_id, cv2.CC_STAT_HEIGHT])

            regions.append({
                "source_label": label_id,
                "area": area,
                "bbox": [x, y, w, h],
                "centroid": [float(centroids[label_id][0]), float(centroids[label_id][1])],
                "points": pts.tolist(),
                "active": old_active.get(label_id, True),
            })

        regions.sort(key=lambda r: r["area"], reverse=True)
        for idx, region in enumerate(regions, start=1):
            region["id"] = idx

        self.regions = regions
        self.groups.clear()
        self.next_group_id = 1
        self.selected_region_ids.clear()

        self._refresh_group_list()
        self._update_counts()
        self.refresh_preview()
        self.status_var.set(f"Analyse abgeschlossen: {len(regions)} Regionen erkannt.")

    def _region_by_id(self, rid):
        for region in self.regions:
            if region["id"] == rid:
                return region
        return None

    def _group_for_region(self, rid):
        for group in self.groups.values():
            if rid in group["region_ids"]:
                return group
        return None

    def _selected_group_id(self):
        selection = self.group_list.curselection()
        if not selection:
            return None
        text = self.group_list.get(selection[0])
        try:
            return int(text.split("|")[0].strip())
        except Exception:
            return None

    def _update_counts(self):
        active = sum(1 for r in self.regions if r["active"])
        grouped = set()
        for g in self.groups.values():
            grouped |= set(g["region_ids"])
        ungrouped = sum(1 for r in self.regions if r["active"] and r["id"] not in grouped)

        self.region_count_var.set(f"Regionen: {len(self.regions)}")
        self.active_count_var.set(f"Aktiv: {active}")
        self.selected_count_var.set(f"Ausgewählt: {len(self.selected_region_ids)}")
        self.group_count_var.set(f"Gruppen: {len(self.groups)}")
        self.ungrouped_count_var.set(f"Ungegruppiert: {ungrouped}")

    @staticmethod
    def _palette_color(index):
        palette = [
            (246,189,96),(132,165,157),(242,132,130),(108,138,228),
            (184,199,122),(167,139,250),(100,181,166),(233,163,193),
            (230,194,41),(127,176,105),(244,162,97),(141,153,174),
            (92,201,160),(198,134,66),(115,133,213),
        ]
        return palette[index % len(palette)]

    def make_preview(self):
        if self.labels is None or self.line_mask is None:
            return None

        h, w = self.labels.shape
        preview = np.full((h, w, 3), 255, np.uint8)

        grouped_ids = set()
        for g in self.groups.values():
            grouped_ids |= set(g["region_ids"])

        for region in self.regions:
            mask = self.labels == region["source_label"]

            if not region["active"]:
                if self.show_inactive_var.get():
                    preview[mask] = (232,232,232)
                continue

            group = self._group_for_region(region["id"])
            if group:
                color = self._palette_color(group["color_id"] - 1)
            else:
                color = self._palette_color(region["id"] - 1)

            preview[mask] = np.array(color, dtype=np.uint8)

            if self.highlight_ungrouped_var.get() and region["id"] not in grouped_ids:
                contours, _ = cv2.findContours(
                    mask.astype(np.uint8) * 255,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE,
                )
                cv2.drawContours(preview, contours, -1, (255, 90, 0), 2)

        preview[self.line_mask > 0] = (25,25,25)

        # Selection highlight
        for rid in self.selected_region_ids:
            region = self._region_by_id(rid)
            if not region:
                continue
            mask = (self.labels == region["source_label"]).astype(np.uint8) * 255
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(preview, contours, -1, (255,0,255), 4)

        if self.show_numbers_var.get():
            # Ungrouped active regions show technical region IDs
            for region in self.regions:
                if not region["active"]:
                    continue
                if self._group_for_region(region["id"]):
                    continue
                if region["area"] < max(500, int(self.min_area_var.get()) * 2):
                    continue
                self._draw_number(preview, region["centroid"], str(region["id"]))

            # One number per group, at label_position
            for group in self.groups.values():
                if not group["region_ids"]:
                    continue
                pos = group.get("label_position")
                if pos is None:
                    pos = self._calculate_group_center(group)
                if pos is not None:
                    self._draw_number(preview, pos, str(group["color_id"]), radius=15)

        return preview

    def _draw_number(self, img, pos, text, radius=13):
        cx, cy = map(int, pos)
        cv2.circle(img, (cx,cy), radius, (255,255,255), -1)
        cv2.circle(img, (cx,cy), radius, (30,30,30), 1)
        ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)[0]
        cv2.putText(
            img,
            text,
            (cx-ts[0]//2, cy+ts[1]//2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (25,25,25),
            1,
            cv2.LINE_AA,
        )

    def _calculate_group_center(self, group):
        weighted = []
        total = 0
        for rid in group["region_ids"]:
            region = self._region_by_id(rid)
            if not region or not region["active"]:
                continue
            area = region["area"]
            cx, cy = region["centroid"]
            weighted.append((cx * area, cy * area))
            total += area
        if total <= 0:
            return None
        return [
            sum(v[0] for v in weighted) / total,
            sum(v[1] for v in weighted) / total,
        ]

    def refresh_preview(self):
        preview = self.make_preview()
        if preview is None:
            self.canvas.delete("all")
            return

        self.preview_rgb = preview
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        h, w = preview.shape[:2]
        scale = max(0.01, min(canvas_w/w, canvas_h/h))
        dw = max(1, int(w*scale))
        dh = max(1, int(h*scale))

        pil = Image.fromarray(preview).resize((dw,dh), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(pil)

        self.display_scale = scale
        self.display_offset_x = (canvas_w-dw)//2
        self.display_offset_y = (canvas_h-dh)//2

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

        x = int((event.x-self.display_offset_x)/self.display_scale)
        y = int((event.y-self.display_offset_y)/self.display_scale)

        h, w = self.labels.shape
        if not (0 <= x < w and 0 <= y < h):
            return

        if self.mode_var.get() == "label":
            gid = self._selected_group_id()
            if gid is None or gid not in self.groups:
                messagebox.showinfo("Hinweis", "Bitte zuerst eine Gruppe in der Liste auswählen.")
                return
            self.groups[gid]["label_position"] = [float(x), float(y)]
            self.status_var.set(f"Label-Position für Gruppe {gid} gesetzt.")
            self.refresh_preview()
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

        shift = bool(event.state & 0x0001)
        rid = clicked["id"]

        if shift:
            if rid in self.selected_region_ids:
                self.selected_region_ids.remove(rid)
            else:
                self.selected_region_ids.add(rid)
        else:
            self.selected_region_ids = {rid}

        group = self._group_for_region(rid)
        if group:
            self.status_var.set(
                f"Region {rid} ausgewählt. Gruppe {group['id']} / Farb-ID {group['color_id']}."
            )
        else:
            self.status_var.set(f"Region {rid} ausgewählt.")

        self._update_counts()
        self.refresh_preview()

    def clear_selection(self):
        self.selected_region_ids.clear()
        self._update_counts()
        self.refresh_preview()

    def create_group(self):
        if not self.selected_region_ids:
            messagebox.showinfo("Hinweis", "Bitte zuerst Regionen auswählen.")
            return

        self.remove_selection_from_groups(refresh=False)

        gid = self.next_group_id
        self.next_group_id += 1

        name = self.group_name_var.get().strip() or f"Gruppe {gid}"
        color_id = max(1, int(self.color_id_var.get()))

        group = {
            "id": gid,
            "name": name,
            "color_id": color_id,
            "region_ids": set(self.selected_region_ids),
            "label_position": None,
        }
        group["label_position"] = self._calculate_group_center(group)

        self.groups[gid] = group

        self.group_name_var.set("")
        self._refresh_group_list(gid)
        self._update_counts()
        self.refresh_preview()
        self.status_var.set(
            f"{name} erstellt: {len(group['region_ids'])} Regionen, Farb-ID {color_id}."
        )

    def add_selection_to_group(self):
        gid = self._selected_group_id()
        if gid is None or gid not in self.groups:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Zielgruppe auswählen.")
            return
        if not self.selected_region_ids:
            messagebox.showinfo("Hinweis", "Bitte Regionen auswählen.")
            return

        for other_gid, group in self.groups.items():
            if other_gid != gid:
                group["region_ids"] -= self.selected_region_ids

        self.groups[gid]["region_ids"] |= self.selected_region_ids
        self._remove_empty_groups()
        self.groups[gid]["label_position"] = self._calculate_group_center(self.groups[gid])

        self._refresh_group_list(gid)
        self._update_counts()
        self.refresh_preview()
        self.status_var.set("Regionen zur Gruppe hinzugefügt.")

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
            self.status_var.set("Regionen aus Gruppen entfernt.")

    def update_selected_group(self):
        gid = self._selected_group_id()
        if gid is None or gid not in self.groups:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Gruppe auswählen.")
            return

        group = self.groups[gid]
        group["name"] = self.group_name_var.get().strip() or group["name"]
        group["color_id"] = max(1, int(self.color_id_var.get()))

        self._refresh_group_list(gid)
        self.refresh_preview()
        self.status_var.set(f"Gruppe {gid} aktualisiert.")

    def auto_center_group_label(self):
        gid = self._selected_group_id()
        if gid is None or gid not in self.groups:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Gruppe auswählen.")
            return

        self.groups[gid]["label_position"] = self._calculate_group_center(self.groups[gid])
        self.refresh_preview()
        self.status_var.set(f"Label von Gruppe {gid} automatisch zentriert.")

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
        for gid in [gid for gid, g in self.groups.items() if not g["region_ids"]]:
            del self.groups[gid]

    def _refresh_group_list(self, select_group_id=None):
        self.group_list.delete(0, tk.END)
        select_index = None

        for idx, gid in enumerate(sorted(self.groups)):
            group = self.groups[gid]
            self.group_list.insert(
                tk.END,
                f"{gid} | Farbe {group['color_id']} | {group['name']} | {len(group['region_ids'])} Regionen"
            )
            if gid == select_group_id:
                select_index = idx

        if select_index is not None:
            self.group_list.selection_set(select_index)
            self.group_list.see(select_index)

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

    def set_selection_active(self, active):
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

    def save_project(self):
        if self.image_path is None or self.labels is None:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Bild analysieren.")
            return

        path = filedialog.asksaveasfilename(
            title="Projekt speichern",
            defaultextension=".json",
            initialfile=f"{self.image_path.stem}_project.json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return

        data = self._project_data()
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        self.status_var.set(f"Projekt gespeichert: {Path(path).name}")

    def load_project(self):
        path = filedialog.askopenfilename(
            title="Projekt laden",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return

        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as exc:
            messagebox.showerror("Fehler", f"Projekt konnte nicht geladen werden:\n{exc}")
            return

        image_path = Path(data.get("image_path", ""))
        if not image_path.exists():
            chosen = filedialog.askopenfilename(
                title="Originalbild auswählen",
                filetypes=[("Bilder", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")],
            )
            if not chosen:
                return
            image_path = Path(chosen)

        bgr = cv2.imread(str(image_path))
        if bgr is None:
            messagebox.showerror("Fehler", "Originalbild konnte nicht geladen werden.")
            return

        self.image_path = image_path
        self.original_bgr = bgr
        self.gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        params = data.get("parameters", {})
        self.threshold_var.set(params.get("threshold", 190))
        self.close_size_var.set(params.get("close_size", 3))
        self.min_area_var.set(params.get("min_area", 100))
        self.simplify_var.set(params.get("simplify_epsilon", 1.5))
        self.include_border_var.set(params.get("include_border_regions", True))

        # Rebuild labels from the source image first.
        self.analyze()

        # Restore regions by current region id. This assumes same image + same parameters.
        saved_regions = {r["id"]: r for r in data.get("regions", [])}
        for region in self.regions:
            saved = saved_regions.get(region["id"])
            if saved:
                region["active"] = saved.get("active", True)

        self.groups.clear()
        max_gid = 0

        for g in data.get("groups", []):
            gid = int(g["id"])
            max_gid = max(max_gid, gid)
            valid_ids = {
                int(rid)
                for rid in g.get("region_ids", [])
                if self._region_by_id(int(rid)) is not None
            }
            self.groups[gid] = {
                "id": gid,
                "name": g.get("name", f"Gruppe {gid}"),
                "color_id": int(g.get("color_id", 1)),
                "region_ids": valid_ids,
                "label_position": g.get("label_position"),
            }

        self.next_group_id = max_gid + 1
        self.selected_region_ids.clear()
        self._remove_empty_groups()
        self._refresh_group_list()
        self._update_counts()
        self.refresh_preview()
        self.status_var.set(f"Projekt geladen: {Path(path).name}")

    def _project_data(self):
        h, w = self.labels.shape
        return {
            "format": "coloring_region_project_v1",
            "image_path": str(self.image_path.resolve()) if self.image_path else None,
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
                    "id": g["id"],
                    "name": g["name"],
                    "color_id": g["color_id"],
                    "region_ids": sorted(g["region_ids"]),
                    "label_position": g.get("label_position"),
                }
                for _, g in sorted(self.groups.items())
            ],
        }

    def export_svg(self):
        if self.labels is None:
            return

        path = filedialog.asksaveasfilename(
            title="Game SVG exportieren",
            defaultextension=".svg",
            initialfile=f"{self.image_path.stem}_game.svg" if self.image_path else "game.svg",
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

        exported = set()

        for gid in sorted(self.groups):
            g = self.groups[gid]
            active_regions = [
                self._region_by_id(rid)
                for rid in sorted(g["region_ids"])
            ]
            active_regions = [r for r in active_regions if r and r["active"]]
            if not active_regions:
                continue

            safe_name = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in g["name"])
            label_pos = g.get("label_position") or self._calculate_group_center(g)
            lx, ly = label_pos if label_pos else (0,0)

            parts.append(
                f'<g id="group_{gid:03d}" data-group-id="{gid}" '
                f'data-name="{safe_name}" data-color-id="{g["color_id"]}" '
                f'data-label-x="{lx:.2f}" data-label-y="{ly:.2f}">'
            )

            for r in active_regions:
                exported.add(r["id"])
                d = "M " + " ".join(f"{float(x):.2f},{float(y):.2f}" for x,y in r["points"]) + " Z"
                parts.append(
                    f'<path id="group_{gid:03d}_region_{r["id"]:03d}" '
                    f'data-region-id="{r["id"]}" d="{d}" fill="#d9d9d9" stroke="none"/>'
                )

            parts.append("</g>")

        # Active ungrouped regions also remain available.
        for r in self.regions:
            if not r["active"] or r["id"] in exported:
                continue
            d = "M " + " ".join(f"{float(x):.2f},{float(y):.2f}" for x,y in r["points"]) + " Z"
            parts.append(
                f'<g id="region_group_{r["id"]:03d}" data-group-id="region_{r["id"]:03d}" data-color-id="0">'
            )
            parts.append(
                f'<path id="region_{r["id"]:03d}" data-region-id="{r["id"]}" d="{d}" fill="#d9d9d9" stroke="none"/>'
            )
            parts.append("</g>")

        parts.extend(["</g>", "</svg>"])
        Path(path).write_text("\n".join(parts), encoding="utf-8")
        self.status_var.set(f"Game SVG gespeichert: {Path(path).name}")

    def export_game_json(self):
        if self.labels is None:
            return

        path = filedialog.asksaveasfilename(
            title="Game JSON exportieren",
            defaultextension=".json",
            initialfile=f"{self.image_path.stem}_game.json" if self.image_path else "game.json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return

        h, w = self.labels.shape

        game_areas = []
        grouped_ids = set()

        for gid in sorted(self.groups):
            g = self.groups[gid]
            active_ids = [
                rid for rid in sorted(g["region_ids"])
                if (self._region_by_id(rid) and self._region_by_id(rid)["active"])
            ]
            if not active_ids:
                continue

            grouped_ids |= set(active_ids)
            label_pos = g.get("label_position") or self._calculate_group_center(g)

            game_areas.append({
                "id": gid,
                "name": g["name"],
                "color_id": g["color_id"],
                "region_ids": active_ids,
                "label_position": label_pos,
            })

        data = {
            "format": "coloring_game_export_v1",
            "source": self.image_path.name if self.image_path else None,
            "width": w,
            "height": h,
            "game_areas": game_areas,
            "ungrouped_active_regions": [
                r["id"]
                for r in self.regions
                if r["active"] and r["id"] not in grouped_ids
            ],
        }

        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        self.status_var.set(f"Game JSON gespeichert: {Path(path).name}")

    def export_outline_png(self):
        if self.line_mask is None:
            return

        path = filedialog.asksaveasfilename(
            title="Outline PNG exportieren",
            defaultextension=".png",
            initialfile=f"{self.image_path.stem}_outline.png" if self.image_path else "outline.png",
            filetypes=[("PNG", "*.png")],
        )
        if not path:
            return

        # RGBA: black linework, transparent background
        h, w = self.line_mask.shape
        rgba = np.zeros((h,w,4), dtype=np.uint8)
        rgba[..., :3] = 0
        rgba[..., 3] = self.line_mask
        Image.fromarray(rgba, mode="RGBA").save(path)
        self.status_var.set(f"Outline PNG gespeichert: {Path(path).name}")

    def export_preview(self):
        preview = self.make_preview()
        if preview is None:
            return

        path = filedialog.asksaveasfilename(
            title="Vorschau speichern",
            defaultextension=".png",
            initialfile=f"{self.image_path.stem}_preview.png" if self.image_path else "preview.png",
            filetypes=[("PNG", "*.png")],
        )
        if not path:
            return

        Image.fromarray(preview).save(path)
        self.status_var.set(f"Vorschau gespeichert: {Path(path).name}")


if __name__ == "__main__":
    app = ColoringRegionExtractor()
    app.mainloop()
