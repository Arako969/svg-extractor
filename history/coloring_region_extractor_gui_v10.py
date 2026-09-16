#!/usr/bin/env python3
"""
Coloring Region Extractor v10

Features:
- Automatic closed-region detection
- Resizable split interface with scrollable controls
- Adjustable left panel width by dragging the divider
- Multi-selection with Shift + click
- Logical groups / game areas
- One label position per group
- Project save/load
- Game SVG / JSON / transparent outline export
- Optional colored reference image
- Automatic representative color extraction
- Automatic palette clustering
- Automatic color-ID assignment to groups and regions
- Preview with detected target colors

Requirements:
    pip install opencv-python pillow numpy

Run:
    python3 coloring_region_extractor_gui_v10.py
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

        self.title("Coloring Region Extractor v10")
        self.geometry("1720x980")
        self.minsize(1050, 700)
        self.resizable(True, True)

        # Files / images
        self.image_path: Path | None = None
        self.color_image_path: Path | None = None
        self.original_bgr: np.ndarray | None = None
        self.color_bgr: np.ndarray | None = None
        self.gray: np.ndarray | None = None

        # Analysis
        self.line_mask: np.ndarray | None = None
        self.labels: np.ndarray | None = None
        self.regions: list[dict] = []

        # Editing
        self.selected_region_ids: set[int] = set()
        self.groups: dict[int, dict] = {}
        self.next_group_id = 1

        # Palette
        self.palette: list[dict] = []
        self.palette_size_var = tk.IntVar(value=12)
        self.ignore_dark_var = tk.BooleanVar(value=True)
        self.ignore_light_var = tk.BooleanVar(value=True)
        self.dark_threshold_var = tk.IntVar(value=45)
        self.light_threshold_var = tk.IntVar(value=245)
        self.use_real_colors_var = tk.BooleanVar(value=True)
        self.split_min_area_var = tk.IntVar(value=180)
        self.split_smooth_var = tk.IntVar(value=3)
        self.adaptive_micro_var = tk.BooleanVar(value=True)
        self.micro_min_area_var = tk.IntVar(value=8)
        self.relative_split_var = tk.BooleanVar(value=False)
        self.split_min_percent_var = tk.DoubleVar(value=0.08)
        self.recovery_min_area_var = tk.IntVar(value=20)
        self.recovery_erode_var = tk.IntVar(value=1)
        self.recovery_enabled_var = tk.BooleanVar(value=True)

        # Preview
        self.preview_photo: ImageTk.PhotoImage | None = None
        self.preview_rgb: np.ndarray | None = None
        self.display_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._pan_start = None
        self._pan_origin = None

        # Region parameters
        self.threshold_var = tk.IntVar(value=190)
        self.close_size_var = tk.IntVar(value=3)
        self.min_area_var = tk.IntVar(value=100)
        self.simplify_var = tk.DoubleVar(value=1.5)

        self.include_border_var = tk.BooleanVar(value=True)
        self.show_numbers_var = tk.BooleanVar(value=True)
        self.show_inactive_var = tk.BooleanVar(value=True)
        self.highlight_ungrouped_var = tk.BooleanVar(value=True)

        # Group editor
        self.color_id_var = tk.IntVar(value=1)
        self.group_name_var = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value="select")

        # Text
        self.status_var = tk.StringVar(value="Bitte ein Outline-Bild öffnen.")
        self.color_file_var = tk.StringVar(value="Keine Farbvorlage geladen")
        self.region_count_var = tk.StringVar(value="Regionen: 0")
        self.active_count_var = tk.StringVar(value="Aktiv: 0")
        self.selected_count_var = tk.StringVar(value="Ausgewählt: 0")
        self.group_count_var = tk.StringVar(value="Gruppen: 0")
        self.ungrouped_count_var = tk.StringVar(value="Ungegruppiert: 0")

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # PanedWindow makes the left side width adjustable by drag.
        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left_holder = ttk.Frame(paned)
        preview_holder = ttk.Frame(paned)
        right_holder = ttk.Frame(paned)

        paned.add(left_holder, weight=0)
        paned.add(preview_holder, weight=1)
        paned.add(right_holder, weight=0)

        # Scrollable left control panel.
        self.left_canvas = tk.Canvas(
            left_holder,
            width=420,
            highlightthickness=0,
            borderwidth=0,
        )
        left_scroll = ttk.Scrollbar(
            left_holder,
            orient="vertical",
            command=self.left_canvas.yview,
        )
        self.left_canvas.configure(yscrollcommand=left_scroll.set)

        left_scroll.pack(side="right", fill="y")
        self.left_canvas.pack(side="left", fill="both", expand=True)

        left = ttk.Frame(self.left_canvas, padding=12)
        self.left_window = self.left_canvas.create_window(
            (0, 0), window=left, anchor="nw"
        )

        left.bind(
            "<Configure>",
            lambda _e: self.left_canvas.configure(
                scrollregion=self.left_canvas.bbox("all")
            ),
        )
        self.left_canvas.bind(
            "<Configure>",
            lambda e: self.left_canvas.itemconfigure(
                self.left_window, width=e.width
            ),
        )

        # macOS mouse wheel / trackpad support
        self.left_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.left_canvas.bind_all("<Button-4>", lambda _e: self.left_canvas.yview_scroll(-1, "units"))
        self.left_canvas.bind_all("<Button-5>", lambda _e: self.left_canvas.yview_scroll(1, "units"))

        ttk.Label(
            left,
            text="Coloring Region Extractor",
            font=("Helvetica", 18, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        file_buttons = ttk.Frame(left)
        file_buttons.pack(fill="x")

        ttk.Button(
            file_buttons,
            text="Outline öffnen",
            command=self.open_image,
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ttk.Button(
            file_buttons,
            text="Farbvorlage laden",
            command=self.open_color_image,
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        ttk.Label(
            left,
            textvariable=self.color_file_var,
            wraplength=390,
        ).pack(anchor="w", pady=(5, 4))

        project_buttons = ttk.Frame(left)
        project_buttons.pack(fill="x")
        ttk.Button(
            project_buttons,
            text="Projekt laden",
            command=self.load_project,
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(
            project_buttons,
            text="Projekt speichern",
            command=self.save_project,
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        ttk.Button(
            left,
            text="Neu analysieren",
            command=self.analyze,
        ).pack(fill="x", pady=(6, 2))

        ttk.Separator(left).pack(fill="x", pady=10)

        # Region analysis
        ttk.Label(
            left,
            text="Regionserkennung",
            font=("Helvetica", 13, "bold"),
        ).pack(anchor="w")

        self._add_slider(left, "Schwarz/Weiß-Schwelle", self.threshold_var, 50, 245)
        self._add_slider(left, "Lücken schließen", self.close_size_var, 1, 15)
        self._add_slider(left, "Min. Flächengröße", self.min_area_var, 10, 5000)
        self._add_slider(left, "Pfad-Vereinfachung", self.simplify_var, 0.2, 8.0, is_float=True)

        ttk.Checkbutton(
            left,
            text="Bildrand als Grenze verwenden",
            variable=self.include_border_var,
        ).pack(anchor="w", pady=2)

        ttk.Checkbutton(
            left,
            text="Regions-/Farbnummern anzeigen",
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
            text="Ungegruppierte Regionen markieren",
            variable=self.highlight_ungrouped_var,
            command=self.refresh_preview,
        ).pack(anchor="w", pady=2)

        ttk.Separator(left).pack(fill="x", pady=7)

        ttk.Label(
            left,
            text="Adaptive Mikroregionen",
            font=("Helvetica", 12, "bold"),
        ).pack(anchor="w")

        ttk.Checkbutton(
            left,
            text="Kleine geschlossene Flächen zusätzlich suchen",
            variable=self.adaptive_micro_var,
        ).pack(anchor="w", pady=2)

        self._add_slider(
            left,
            "Min. Mikroregion",
            self.micro_min_area_var,
            1,
            200,
        )

        ttk.Label(
            left,
            text=(
                "Der zweite Erkennungsdurchlauf arbeitet ohne Lückenschließung. "
                "Das hilft bei sehr kleinen Beeren-, Blüten- und Detailflächen."
            ),
            wraplength=390,
            justify="left",
        ).pack(anchor="w", pady=(2, 4))

        ttk.Separator(left).pack(fill="x", pady=10)

        stats = ttk.Frame(left)
        stats.pack(fill="x")
        ttk.Label(stats, textvariable=self.region_count_var).grid(row=0, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.active_count_var).grid(row=0, column=1, sticky="w", padx=(18, 0))
        ttk.Label(stats, textvariable=self.selected_count_var).grid(row=1, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.group_count_var).grid(row=1, column=1, sticky="w", padx=(18, 0))
        ttk.Label(stats, textvariable=self.ungrouped_count_var).grid(row=2, column=0, columnspan=2, sticky="w")

        ttk.Separator(left).pack(fill="x", pady=10)

        # Color analysis
        ttk.Label(
            left,
            text="Farbanalyse",
            font=("Helvetica", 13, "bold"),
        ).pack(anchor="w")

        row = ttk.Frame(left)
        row.pack(fill="x", pady=(6, 2))
        ttk.Label(row, text="Palette").pack(side="left")
        ttk.Spinbox(
            row,
            from_=2,
            to=50,
            textvariable=self.palette_size_var,
            width=8,
        ).pack(side="right")

        ttk.Checkbutton(
            left,
            text="Sehr dunkle Pixel ignorieren",
            variable=self.ignore_dark_var,
        ).pack(anchor="w", pady=2)

        self._add_slider(
            left,
            "Dunkel-Grenzwert",
            self.dark_threshold_var,
            0,
            120,
        )

        ttk.Checkbutton(
            left,
            text="Sehr helle Pixel ignorieren",
            variable=self.ignore_light_var,
        ).pack(anchor="w", pady=2)

        self._add_slider(
            left,
            "Hell-Grenzwert",
            self.light_threshold_var,
            150,
            255,
        )

        ttk.Checkbutton(
            left,
            text="Erkannte Zielfarben in Vorschau",
            variable=self.use_real_colors_var,
            command=self.refresh_preview,
        ).pack(anchor="w", pady=2)

        ttk.Button(
            left,
            text="Farben automatisch analysieren",
            command=self.analyze_colors,
        ).pack(fill="x", pady=(6, 4))

        ttk.Separator(left).pack(fill="x", pady=8)

        ttk.Label(
            left,
            text="Farbbasierte Unterregionen",
            font=("Helvetica", 12, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            left,
            text=(
                "Für Bereiche ohne schwarze Trennlinie. "
                "Die Hauptregion bleibt als Grundfläche erhalten; "
                "abweichende Farbflächen werden als darüberliegende "
                "Unterregionen erzeugt."
            ),
            wraplength=390,
            justify="left",
        ).pack(anchor="w", pady=(3, 5))

        self._add_slider(
            left,
            "Min. Unterregion",
            self.split_min_area_var,
            20,
            3000,
        )

        ttk.Checkbutton(
            left,
            text="Mindestgröße relativ zur Bildfläche",
            variable=self.relative_split_var,
        ).pack(anchor="w", pady=(3, 1))

        self._add_slider(
            left,
            "Relative Mindestgröße (%)",
            self.split_min_percent_var,
            0.005,
            1.0,
            is_float=True,
        )

        self._add_slider(
            left,
            "Farbmasken glätten",
            self.split_smooth_var,
            1,
            15,
        )

        ttk.Button(
            left,
            text="Auswahl nach Farben aufteilen",
            command=self.split_selected_regions_by_color,
        ).pack(fill="x", pady=(5, 2))

        ttk.Button(
            left,
            text="Unterregionen der Auswahl löschen",
            command=self.remove_color_subregions_for_selection,
        ).pack(fill="x", pady=2)

        ttk.Label(left, text="Erkannte Palette").pack(anchor="w", pady=(4, 2))

        self.palette_canvas = tk.Canvas(
            left,
            height=76,
            bg="#eeeeee",
            highlightthickness=1,
            highlightbackground="#888888",
        )
        self.palette_canvas.pack(fill="x", pady=(0, 4))

        ttk.Separator(left).pack(fill="x", pady=8)

        ttk.Label(
            left,
            text="Farbbasierte Wiederherstellung",
            font=("Helvetica", 12, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            left,
            text=(
                "Ergänzt Farbflächen aus der kolorierten Vorlage, wenn "
                "die Outline dort offen oder unvollständig ist."
            ),
            wraplength=390,
            justify="left",
        ).pack(anchor="w", pady=(3, 5))

        ttk.Checkbutton(
            left,
            text="Wiederherstellung aktiv",
            variable=self.recovery_enabled_var,
        ).pack(anchor="w", pady=2)

        self._add_slider(
            left,
            "Min. Recovery-Fläche",
            self.recovery_min_area_var,
            2,
            1000,
        )

        self._add_slider(
            left,
            "Randabstand",
            self.recovery_erode_var,
            0,
            6,
        )

        ttk.Button(
            left,
            text="Fehlende Regionen aus Farbvorlage suchen",
            command=self.recover_missing_regions_from_color,
        ).pack(fill="x", pady=(5, 2))

        ttk.Button(
            left,
            text="Recovery-Regionen löschen",
            command=self.remove_recovered_regions,
        ).pack(fill="x", pady=2)

        ttk.Separator(left).pack(fill="x", pady=10)

        # Scrollable right control panel.
        self.right_canvas = tk.Canvas(
            right_holder, width=400, highlightthickness=0, borderwidth=0
        )
        right_scroll = ttk.Scrollbar(
            right_holder, orient="vertical", command=self.right_canvas.yview
        )
        self.right_canvas.configure(yscrollcommand=right_scroll.set)
        right_scroll.pack(side="right", fill="y")
        self.right_canvas.pack(side="left", fill="both", expand=True)
        controls_right = ttk.Frame(self.right_canvas, padding=12)
        self.right_window = self.right_canvas.create_window(
            (0, 0), window=controls_right, anchor="nw"
        )
        controls_right.bind(
            "<Configure>",
            lambda _e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all")),
        )
        self.right_canvas.bind(
            "<Configure>",
            lambda e: self.right_canvas.itemconfigure(self.right_window, width=e.width),
        )

        # Selection
        ttk.Label(
            controls_right,
            text="Auswahl und Game Areas",
            font=("Helvetica", 13, "bold"),
        ).pack(anchor="w")

        modes = ttk.Frame(controls_right)
        modes.pack(fill="x", pady=(4, 6))

        ttk.Radiobutton(
            modes,
            text="Auswahl",
            value="select",
            variable=self.mode_var,
        ).pack(side="left")

        ttk.Radiobutton(
            modes,
            text="Label setzen",
            value="label",
            variable=self.mode_var,
        ).pack(side="left", padx=(12, 0))

        ttk.Radiobutton(
            modes,
            text="Fehlende Fläche hinzufügen",
            value="manual_add",
            variable=self.mode_var,
        ).pack(side="left", padx=(12, 0))

        ttk.Label(
            controls_right,
            text=(
                "Klick: eine Region auswählen\n"
                "Shift + Klick: Auswahl erweitern/entfernen\n"
                "Label setzen: Gruppe wählen und ins Bild klicken\n"
                "Fehlende Fläche hinzufügen: direkt in die kleine Fläche klicken"
            ),
            justify="left",
        ).pack(anchor="w", pady=(0, 7))

        ttk.Button(
            controls_right,
            text="Auswahl löschen",
            command=self.clear_selection,
        ).pack(fill="x", pady=2)

        row = ttk.Frame(controls_right)
        row.pack(fill="x", pady=(7, 2))

        ttk.Label(row, text="Gruppenname").pack(side="left")
        ttk.Entry(
            row,
            textvariable=self.group_name_var,
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

        row = ttk.Frame(controls_right)
        row.pack(fill="x", pady=2)

        ttk.Label(row, text="Farb-ID").pack(side="left")
        ttk.Spinbox(
            row,
            from_=1,
            to=999,
            textvariable=self.color_id_var,
            width=8,
        ).pack(side="right")

        ttk.Button(
            controls_right,
            text="Gruppe aus Auswahl erstellen",
            command=self.create_group,
        ).pack(fill="x", pady=(6, 2))

        ttk.Button(
            controls_right,
            text="Auswahl zur gewählten Gruppe",
            command=self.add_selection_to_group,
        ).pack(fill="x", pady=2)

        ttk.Button(
            controls_right,
            text="Auswahl aus Gruppen entfernen",
            command=self.remove_selection_from_groups,
        ).pack(fill="x", pady=2)

        ttk.Label(left, text="Gruppen").pack(anchor="w", pady=(8, 3))

        list_frame = ttk.Frame(controls_right)
        list_frame.pack(fill="both")

        self.group_list = tk.Listbox(
            list_frame,
            height=11,
            exportselection=False,
        )
        self.group_list.pack(side="left", fill="both", expand=True)

        group_scroll = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.group_list.yview,
        )
        group_scroll.pack(side="right", fill="y")
        self.group_list.configure(yscrollcommand=group_scroll.set)
        self.group_list.bind("<<ListboxSelect>>", self.on_group_selected)

        ttk.Button(
            controls_right,
            text="Gewählte Gruppe aktualisieren",
            command=self.update_selected_group,
        ).pack(fill="x", pady=(5, 2))

        ttk.Button(
            controls_right,
            text="Farbe der Gruppe aus Vorlage neu bestimmen",
            command=self.analyze_selected_group_color,
        ).pack(fill="x", pady=2)

        ttk.Button(
            controls_right,
            text="Label automatisch zentrieren",
            command=self.auto_center_group_label,
        ).pack(fill="x", pady=2)

        ttk.Button(
            controls_right,
            text="Gewählte Gruppe löschen",
            command=self.delete_selected_group,
        ).pack(fill="x", pady=2)

        ttk.Separator(controls_right).pack(fill="x", pady=10)

        ttk.Button(
            controls_right,
            text="Auswahl aktivieren",
            command=lambda: self.set_selection_active(True),
        ).pack(fill="x", pady=2)

        ttk.Button(
            controls_right,
            text="Auswahl deaktivieren",
            command=lambda: self.set_selection_active(False),
        ).pack(fill="x", pady=2)

        ttk.Button(
            controls_right,
            text="Alle aktivieren",
            command=self.activate_all,
        ).pack(fill="x", pady=2)

        ttk.Separator(controls_right).pack(fill="x", pady=10)

        ttk.Label(
            controls_right,
            text="Export",
            font=("Helvetica", 13, "bold"),
        ).pack(anchor="w")

        ttk.Button(
            controls_right,
            text="Game SVG exportieren",
            command=self.export_svg,
        ).pack(fill="x", pady=(5, 2))

        ttk.Button(
            controls_right,
            text="Game JSON exportieren",
            command=self.export_game_json,
        ).pack(fill="x", pady=2)

        ttk.Button(
            controls_right,
            text="Outline PNG exportieren",
            command=self.export_outline_png,
        ).pack(fill="x", pady=2)

        ttk.Button(
            controls_right,
            text="Vorschau speichern",
            command=self.export_preview,
        ).pack(fill="x", pady=2)

        ttk.Label(
            controls_right,
            textvariable=self.status_var,
            wraplength=390,
            justify="left",
        ).pack(anchor="w", pady=(12, 20))

        # Center image preview with zoom controls
        preview_toolbar = ttk.Frame(preview_holder)
        preview_toolbar.pack(fill="x", padx=6, pady=6)
        ttk.Button(preview_toolbar, text="−", width=3, command=lambda: self._zoom_by(1/1.2)).pack(side="left")
        ttk.Button(preview_toolbar, text="+", width=3, command=lambda: self._zoom_by(1.2)).pack(side="left", padx=(4, 0))
        ttk.Button(preview_toolbar, text="Ganzes Bild", command=self.reset_zoom).pack(side="left", padx=(8, 0))
        self.zoom_text_var = tk.StringVar(value="Fit")
        ttk.Label(preview_toolbar, textvariable=self.zoom_text_var).pack(side="left", padx=10)
        ttk.Label(preview_toolbar, text="Magic Mouse: scrollen = Zoom · Rechtsklick ziehen = Verschieben").pack(side="right")

        self.canvas = tk.Canvas(
            preview_holder,
            bg="#292929",
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self._on_preview_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._zoom_at(e.x, e.y, 1.12))
        self.canvas.bind("<Button-5>", lambda e: self._zoom_at(e.x, e.y, 1/1.12))
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._do_pan)
        self.canvas.bind("<ButtonPress-3>", self._start_pan)
        self.canvas.bind("<B3-Motion>", self._do_pan)
        self.canvas.bind("<Configure>", lambda _e: self.refresh_preview())

        self.after(200, lambda: self._set_initial_sash(paned))

    def _set_initial_sash(self, paned):
        try:
            paned.sashpos(0, 420)
            paned.sashpos(1, max(850, self.winfo_width() - 410))
        except Exception:
            pass

    def _on_mousewheel(self, event):
        # Scroll whichever sidebar is under the pointer. macOS trackpads and
        # Magic Mouse often report small delta values, so use direction only.
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
            target = None
            while widget:
                if widget == self.left_canvas:
                    target = self.left_canvas
                    break
                if hasattr(self, "right_canvas") and widget == self.right_canvas:
                    target = self.right_canvas
                    break
                widget = widget.master
            if target is not None and event.delta:
                target.yview_scroll(-1 if event.delta > 0 else 1, "units")
        except Exception:
            pass

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.refresh_preview()

    def _zoom_by(self, factor):
        self._zoom_at(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2, factor)

    def _on_preview_wheel(self, event):
        if not event.delta:
            return
        # Smooth enough for Magic Mouse/trackpad, while avoiding huge jumps.
        magnitude = min(3.0, max(0.35, abs(event.delta) / 120.0))
        factor = 1.10 ** magnitude
        if event.delta < 0:
            factor = 1.0 / factor
        self._zoom_at(event.x, event.y, factor)
        return "break"

    def _zoom_at(self, canvas_x, canvas_y, factor):
        old_scale = max(1e-9, self.display_scale)
        image_x = (canvas_x - self.display_offset_x) / old_scale
        image_y = (canvas_y - self.display_offset_y) / old_scale
        self.zoom_factor = min(12.0, max(1.0, self.zoom_factor * factor))
        self.refresh_preview()
        new_scale = max(1e-9, self.display_scale)
        self.pan_x += canvas_x - (self.display_offset_x + image_x * new_scale)
        self.pan_y += canvas_y - (self.display_offset_y + image_y * new_scale)
        self.refresh_preview()

    def _start_pan(self, event):
        self._pan_start = (event.x, event.y)
        self._pan_origin = (self.pan_x, self.pan_y)

    def _do_pan(self, event):
        if not self._pan_start or not self._pan_origin:
            return
        self.pan_x = self._pan_origin[0] + event.x - self._pan_start[0]
        self.pan_y = self._pan_origin[1] + event.y - self._pan_start[1]
        self.refresh_preview()

    def _add_slider(self, parent, label, variable, minimum, maximum, is_float=False):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=4)

        header = ttk.Frame(frame)
        header.pack(fill="x")
        ttk.Label(header, text=label).pack(side="left")

        value_label = ttk.Label(header, width=8, anchor="e")
        value_label.pack(side="right")

        ttk.Scale(
            frame,
            from_=minimum,
            to=maximum,
            variable=variable,
            orient="horizontal",
        ).pack(fill="x")

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

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Outline-Bild öffnen",
            filetypes=[
                ("Bilder", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if not path:
            return

        bgr = cv2.imread(path)
        if bgr is None:
            messagebox.showerror("Fehler", "Das Outline-Bild konnte nicht geladen werden.")
            return

        self.image_path = Path(path)
        self.original_bgr = bgr
        self.gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        self.groups.clear()
        self.regions.clear()
        self.selected_region_ids.clear()
        self.next_group_id = 1
        self.palette.clear()

        self.analyze()

    def open_color_image(self):
        if self.original_bgr is None:
            messagebox.showinfo("Hinweis", "Bitte zuerst das Outline-Bild öffnen.")
            return

        path = filedialog.askopenfilename(
            title="Kolorierte Farbvorlage öffnen",
            filetypes=[
                ("Bilder", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if not path:
            return

        bgr = cv2.imread(path)
        if bgr is None:
            messagebox.showerror("Fehler", "Die Farbvorlage konnte nicht geladen werden.")
            return

        target_h, target_w = self.original_bgr.shape[:2]

        if bgr.shape[:2] != (target_h, target_w):
            bgr = cv2.resize(
                bgr,
                (target_w, target_h),
                interpolation=cv2.INTER_AREA,
            )
            self.status_var.set(
                "Farbvorlage hatte eine andere Auflösung und wurde auf die Outline-Größe skaliert. "
                "Für genaue Ergebnisse sollten beide Bilder deckungsgleich sein."
            )

        self.color_image_path = Path(path)
        self.color_bgr = bgr
        self.color_file_var.set(f"Farbvorlage: {self.color_image_path.name}")

        if self.regions:
            self.analyze_colors()

    # ------------------------------------------------------------------
    # Region detection
    # ------------------------------------------------------------------

    def analyze(self):
        if self.gray is None:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Outline-Bild öffnen.")
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

        old_active = {
            r["source_label"]: r.get("active", True)
            for r in self.regions
        }

        regions = []

        for label_id in range(1, count):
            area = int(stats[label_id, cv2.CC_STAT_AREA])

            if area < min_area:
                continue

            if (not self.include_border_var.get()) and label_id in border_labels:
                continue

            mask = np.zeros_like(binary, dtype=np.uint8)
            mask[labels == label_id] = 255

            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            if not contours:
                continue

            contour = max(contours, key=cv2.contourArea)
            approx = cv2.approxPolyDP(
                contour,
                simplify,
                True,
            )
            pts = approx.reshape(-1, 2)

            if len(pts) < 3:
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
                    "points": pts.tolist(),
                    "active": old_active.get(label_id, True),
                    "target_color": None,
                    "suggested_color_id": None,
                    "parent_id": None,
                    "is_overlay": False,
                    "is_micro": False,
                    "is_recovered": False,
                    "priority": 0,
                    "mask": None,
                }
            )

        # Optional second pass for tiny closed regions. It deliberately uses
        # the raw threshold mask without morphological closing, because closing
        # can swallow very small interiors such as raspberry cells.
        if self.adaptive_micro_var.get():
            raw_line = (self.gray < threshold).astype(np.uint8) * 255
            raw_white = cv2.bitwise_not(raw_line)
            raw_binary = (raw_white > 0).astype(np.uint8)

            raw_count, raw_labels, raw_stats, raw_centroids = cv2.connectedComponentsWithStats(
                raw_binary,
                connectivity=8,
            )

            micro_min = max(1, int(self.micro_min_area_var.get()))
            existing_masks = [self.labels == r["source_label"] for r in regions]

            for raw_id in range(1, raw_count):
                area = int(raw_stats[raw_id, cv2.CC_STAT_AREA])
                if area < micro_min or area >= min_area:
                    continue

                x = int(raw_stats[raw_id, cv2.CC_STAT_LEFT])
                y = int(raw_stats[raw_id, cv2.CC_STAT_TOP])
                ww = int(raw_stats[raw_id, cv2.CC_STAT_WIDTH])
                hh = int(raw_stats[raw_id, cv2.CC_STAT_HEIGHT])

                # Reject huge/thin border fragments and obvious line noise.
                if ww <= 1 or hh <= 1:
                    continue

                raw_mask = raw_labels == raw_id

                # Skip if this tiny region is already substantially represented
                # by a main-pass region.
                duplicate = False
                for em in existing_masks:
                    overlap = int(np.logical_and(raw_mask, em).sum())
                    if overlap / max(1, area) > 0.80:
                        duplicate = True
                        break
                if duplicate:
                    continue

                contour_img = raw_mask.astype(np.uint8) * 255
                contours, _ = cv2.findContours(
                    contour_img,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE,
                )
                if not contours:
                    continue

                contour = max(contours, key=cv2.contourArea)
                approx = cv2.approxPolyDP(contour, simplify, True)
                pts = approx.reshape(-1, 2)
                if len(pts) < 3:
                    continue

                regions.append(
                    {
                        "source_label": None,
                        "area": area,
                        "bbox": [x, y, ww, hh],
                        "centroid": [
                            float(raw_centroids[raw_id][0]),
                            float(raw_centroids[raw_id][1]),
                        ],
                        "points": pts.tolist(),
                        "active": True,
                        "target_color": None,
                        "suggested_color_id": None,
                        "parent_id": None,
                        "is_overlay": False,
                        "is_micro": True,
                        "is_recovered": False,
                        "priority": 0,
                        "mask": raw_mask.copy(),
                    }
                )

        regions.sort(key=lambda r: r["area"], reverse=True)

        for idx, region in enumerate(regions, start=1):
            region["id"] = idx

        self.regions = regions

        # Re-analysis invalidates groups because region IDs may change.
        self.groups.clear()
        self.next_group_id = 1
        self.selected_region_ids.clear()
        self.palette.clear()

        self._refresh_group_list()
        self._draw_palette()
        self._update_counts()
        self.refresh_preview()

        self.status_var.set(
            f"Analyse abgeschlossen: {len(regions)} Regionen erkannt."
        )

        if self.color_bgr is not None:
            self.analyze_colors()

    # ------------------------------------------------------------------
    # Color extraction / clustering
    # ------------------------------------------------------------------

    def analyze_colors(self):
        if self.color_bgr is None:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst eine kolorierte Farbvorlage laden.",
            )
            return

        if self.labels is None or not self.regions:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst Regionen analysieren.",
            )
            return

        usable_colors = []

        for region in self.regions:
            color = self._extract_color_for_region(region)
            region["target_color"] = color
            if color is not None and region["active"]:
                usable_colors.append(color)

        # Groups use all pixels from all member regions.
        for group in self.groups.values():
            group_color = self._extract_color_for_group(group)
            group["target_color"] = group_color
            if group_color is not None:
                usable_colors.append(group_color)

        if not usable_colors:
            messagebox.showwarning(
                "Farbanalyse",
                "Es konnten keine brauchbaren Farben aus der Vorlage gelesen werden.",
            )
            return

        self.palette = self._cluster_palette(
            usable_colors,
            max(2, int(self.palette_size_var.get())),
        )

        # Assign nearest palette entry to every region.
        for region in self.regions:
            if region.get("target_color") is not None:
                region["suggested_color_id"] = self._nearest_palette_id(
                    region["target_color"]
                )

        # Assign nearest palette entry to every group and set actual color ID.
        for group in self.groups.values():
            group_color = group.get("target_color")
            if group_color is None:
                group_color = self._extract_color_for_group(group)
                group["target_color"] = group_color

            if group_color is not None:
                group["color_id"] = self._nearest_palette_id(group_color)

        self._refresh_group_list()
        self._draw_palette()
        self.refresh_preview()

        self.status_var.set(
            f"Farbanalyse abgeschlossen. {len(self.palette)} Palettenfarben erzeugt."
        )

    def _filtered_color_pixels(self, pixels_bgr):
        if pixels_bgr is None or len(pixels_bgr) == 0:
            return pixels_bgr

        pixels = pixels_bgr.astype(np.uint8)

        # Convert to HSV for brightness filtering.
        hsv = cv2.cvtColor(
            pixels.reshape(-1, 1, 3),
            cv2.COLOR_BGR2HSV,
        ).reshape(-1, 3)

        value = hsv[:, 2]
        keep = np.ones(len(pixels), dtype=bool)

        if self.ignore_dark_var.get():
            keep &= value > int(self.dark_threshold_var.get())

        if self.ignore_light_var.get():
            keep &= value < int(self.light_threshold_var.get())

        filtered = pixels[keep]

        # If filtering was too aggressive, fall back to all non-dark pixels.
        if len(filtered) < 10:
            fallback = pixels[value > 20]
            if len(fallback) >= 5:
                filtered = fallback

        return filtered

    def _representative_color(self, pixels_bgr):
        pixels = self._filtered_color_pixels(pixels_bgr)

        if pixels is None or len(pixels) == 0:
            return None

        # Median is robust against outlines, gradients, highlights and noise.
        median_bgr = np.median(
            pixels.astype(np.float32),
            axis=0,
        )

        b, g, r = [int(round(x)) for x in median_bgr]
        return [r, g, b]

    def _extract_color_for_region(self, region):
        if self.color_bgr is None or self.labels is None:
            return None

        mask = self._region_mask(region)
        if mask is None:
            return None
        pixels = self.color_bgr[mask]

        return self._representative_color(pixels)

    def _extract_color_for_group(self, group):
        if self.color_bgr is None or self.labels is None:
            return None

        masks = []

        for rid in group["region_ids"]:
            region = self._region_by_id(rid)
            if region and region["active"]:
                mask = self._region_mask(region)
                if mask is not None:
                    masks.append(mask)

        if not masks:
            return None

        combined = np.logical_or.reduce(masks)
        pixels = self.color_bgr[combined]

        return self._representative_color(pixels)

    def _cluster_palette(self, rgb_colors, requested_k):
        arr_rgb = np.array(rgb_colors, dtype=np.uint8)

        # Lab gives more visually meaningful clustering than raw RGB.
        arr_bgr = arr_rgb[:, ::-1]
        lab = cv2.cvtColor(
            arr_bgr.reshape(-1, 1, 3),
            cv2.COLOR_BGR2LAB,
        ).reshape(-1, 3).astype(np.float32)

        k = min(requested_k, len(lab))
        k = max(1, k)

        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            100,
            0.2,
        )

        _compactness, labels, centers_lab = cv2.kmeans(
            lab,
            k,
            None,
            criteria,
            10,
            cv2.KMEANS_PP_CENTERS,
        )

        # Convert Lab centers back to RGB.
        centers_lab_u8 = np.clip(
            centers_lab,
            0,
            255,
        ).astype(np.uint8).reshape(-1, 1, 3)

        centers_bgr = cv2.cvtColor(
            centers_lab_u8,
            cv2.COLOR_LAB2BGR,
        ).reshape(-1, 3)

        centers_rgb = centers_bgr[:, ::-1]

        # Sort by hue-ish order for stable / pleasant palette numbering.
        hsv = cv2.cvtColor(
            centers_bgr.reshape(-1, 1, 3),
            cv2.COLOR_BGR2HSV,
        ).reshape(-1, 3)

        order = sorted(
            range(k),
            key=lambda i: (
                int(hsv[i][0]),
                -int(hsv[i][1]),
                -int(hsv[i][2]),
            ),
        )

        palette = []

        for new_id, old_idx in enumerate(order, start=1):
            rgb = [int(v) for v in centers_rgb[old_idx]]
            palette.append(
                {
                    "id": new_id,
                    "rgb": rgb,
                    "hex": self._rgb_to_hex(rgb),
                }
            )

        return palette

    def _nearest_palette_id(self, rgb):
        if not self.palette:
            return None

        color = np.array(rgb, dtype=np.uint8).reshape(1, 1, 3)
        bgr = color[:, :, ::-1]
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).reshape(3).astype(np.float32)

        best_id = None
        best_distance = None

        for entry in self.palette:
            p = np.array(entry["rgb"], dtype=np.uint8).reshape(1, 1, 3)
            p_lab = cv2.cvtColor(
                p[:, :, ::-1],
                cv2.COLOR_BGR2LAB,
            ).reshape(3).astype(np.float32)

            dist = float(np.linalg.norm(lab - p_lab))

            if best_distance is None or dist < best_distance:
                best_distance = dist
                best_id = entry["id"]

        return best_id

    def _draw_palette(self):
        c = self.palette_canvas
        c.delete("all")

        width = max(c.winfo_width(), 360)
        height = max(c.winfo_height(), 70)

        if not self.palette:
            c.create_text(
                width / 2,
                height / 2,
                text="Noch keine Palette analysiert",
                fill="#555555",
            )
            return

        swatch_w = max(26, int(width / max(1, len(self.palette))))
        x = 4

        for entry in self.palette:
            rgb = entry["rgb"]
            fill = self._rgb_to_hex(rgb)

            c.create_rectangle(
                x,
                8,
                min(width - 2, x + swatch_w - 4),
                46,
                fill=fill,
                outline="#444444",
            )

            c.create_text(
                x + (swatch_w - 4) / 2,
                58,
                text=str(entry["id"]),
                fill="#222222",
            )

            x += swatch_w

            if x >= width:
                break


    # ------------------------------------------------------------------
    # Color-based subregions
    # ------------------------------------------------------------------

    def _region_mask(self, region):
        """Return a boolean pixel mask for an original or generated region."""
        stored = region.get("mask")
        if stored is not None:
            return stored.astype(bool)

        source_label = region.get("source_label")
        if source_label is not None and self.labels is not None:
            return self.labels == source_label

        # Reconstruct generated masks from polygon points when loading a project.
        if self.labels is None:
            return None

        points = region.get("points") or []
        if len(points) < 3:
            return None

        mask = np.zeros(self.labels.shape, dtype=np.uint8)
        pts = np.array(points, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        region["mask"] = mask.astype(bool)
        return region["mask"]

    def _palette_label_map_for_mask(self, region_mask):
        """Map pixels in a mask to nearest current palette color in Lab space."""
        if self.color_bgr is None or not self.palette:
            return None

        h, w = region_mask.shape
        result = np.zeros((h, w), dtype=np.int16)

        # Smooth the reference image slightly to suppress antialiasing/noise.
        smooth_size = max(1, int(self.split_smooth_var.get()))
        if smooth_size % 2 == 0:
            smooth_size += 1

        color_img = self.color_bgr
        if smooth_size > 1:
            color_img = cv2.medianBlur(color_img, smooth_size)

        pixels_bgr = color_img[region_mask]
        if len(pixels_bgr) == 0:
            return result

        pixels_lab = cv2.cvtColor(
            pixels_bgr.reshape(-1, 1, 3),
            cv2.COLOR_BGR2LAB,
        ).reshape(-1, 3).astype(np.float32)

        centers = []
        ids = []

        for entry in self.palette:
            rgb = np.array(entry["rgb"], dtype=np.uint8).reshape(1, 1, 3)
            bgr = rgb[:, :, ::-1]
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).reshape(3).astype(np.float32)
            centers.append(lab)
            ids.append(int(entry["id"]))

        centers = np.array(centers, dtype=np.float32)

        # Squared Euclidean distance in Lab.
        dists = ((pixels_lab[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        nearest = np.argmin(dists, axis=1)

        mapped = np.array([ids[i] for i in nearest], dtype=np.int16)
        result[region_mask] = mapped

        return result

    def split_selected_regions_by_color(self):
        """
        Keep each selected original region as the base area and create
        additional overlay regions for sufficiently large secondary colors.
        This handles e.g. beige muzzle/paws inside one orange dog region.
        """
        if self.color_bgr is None:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst eine kolorierte Farbvorlage laden.",
            )
            return

        if not self.palette:
            self.analyze_colors()
            if not self.palette:
                return

        if not self.selected_region_ids:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst mindestens eine große Region auswählen.",
            )
            return

        selected_base_ids = []
        for rid in sorted(self.selected_region_ids):
            region = self._region_by_id(rid)
            if region and not region.get("is_overlay", False):
                selected_base_ids.append(rid)

        if not selected_base_ids:
            messagebox.showinfo(
                "Hinweis",
                "Bitte eine normale Grundregion auswählen, nicht nur eine Unterregion.",
            )
            return

        # Delete old generated overlays for these parents before recalculating.
        self._remove_overlays_by_parent_ids(set(selected_base_ids))

        if self.relative_split_var.get() and self.labels is not None:
            image_area = int(self.labels.shape[0] * self.labels.shape[1])
            min_area = max(
                1,
                int(image_area * float(self.split_min_percent_var.get()) / 100.0),
            )
        else:
            min_area = max(1, int(self.split_min_area_var.get()))
        created = 0

        next_id = max([r["id"] for r in self.regions], default=0) + 1

        for parent_id in selected_base_ids:
            parent = self._region_by_id(parent_id)
            if not parent:
                continue

            parent_mask = self._region_mask(parent)
            if parent_mask is None or not parent_mask.any():
                continue

            color_map = self._palette_label_map_for_mask(parent_mask)
            if color_map is None:
                continue

            ids, counts = np.unique(color_map[parent_mask], return_counts=True)
            valid_pairs = [(int(i), int(c)) for i, c in zip(ids, counts) if int(i) > 0]

            if len(valid_pairs) <= 1:
                continue

            # Dominant color remains represented by the parent/base region.
            dominant_color_id = max(valid_pairs, key=lambda item: item[1])[0]
            parent["suggested_color_id"] = dominant_color_id
            parent["target_color"] = list(self._palette_rgb(dominant_color_id) or parent.get("target_color") or [217,217,217])

            for color_id, _count in valid_pairs:
                if color_id == dominant_color_id:
                    continue

                color_mask = ((color_map == color_id) & parent_mask).astype(np.uint8) * 255

                # Clean small speckles but keep real islands.
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)
                color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)

                n, comps, stats, cents = cv2.connectedComponentsWithStats(
                    (color_mask > 0).astype(np.uint8),
                    connectivity=8,
                )

                for comp_id in range(1, n):
                    area = int(stats[comp_id, cv2.CC_STAT_AREA])
                    if area < min_area:
                        continue

                    comp_mask = comps == comp_id

                    contour_img = comp_mask.astype(np.uint8) * 255
                    contours, _ = cv2.findContours(
                        contour_img,
                        cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE,
                    )
                    if not contours:
                        continue

                    contour = max(contours, key=cv2.contourArea)
                    approx = cv2.approxPolyDP(
                        contour,
                        float(self.simplify_var.get()),
                        True,
                    )
                    points = approx.reshape(-1, 2)
                    if len(points) < 3:
                        continue

                    x = int(stats[comp_id, cv2.CC_STAT_LEFT])
                    y = int(stats[comp_id, cv2.CC_STAT_TOP])
                    ww = int(stats[comp_id, cv2.CC_STAT_WIDTH])
                    hh = int(stats[comp_id, cv2.CC_STAT_HEIGHT])
                    cx, cy = cents[comp_id]

                    rgb = self._palette_rgb(color_id)

                    self.regions.append(
                        {
                            "id": next_id,
                            "source_label": None,
                            "area": area,
                            "bbox": [x, y, ww, hh],
                            "centroid": [float(cx), float(cy)],
                            "points": points.tolist(),
                            "active": True,
                            "target_color": list(rgb) if rgb is not None else None,
                            "suggested_color_id": color_id,
                            "parent_id": parent_id,
                            "is_overlay": True,
                            "is_micro": False,
                            "is_recovered": False,
                            "priority": 1,
                            "mask": comp_mask.copy(),
                        }
                    )

                    next_id += 1
                    created += 1

        self.regions.sort(key=lambda r: (int(r.get("priority", 0)), int(r["id"])))

        self.selected_region_ids.clear()
        self._update_counts()
        self.refresh_preview()

        self.status_var.set(
            f"{created} farbbasierte Unterregionen erzeugt. "
            "Die Grundflächen bleiben darunter erhalten."
        )

    def _remove_overlays_by_parent_ids(self, parent_ids):
        remove_ids = {
            r["id"]
            for r in self.regions
            if r.get("is_overlay", False) and r.get("parent_id") in parent_ids
        }

        if not remove_ids:
            return

        self.regions = [
            r for r in self.regions
            if r["id"] not in remove_ids
        ]

        self.selected_region_ids -= remove_ids

        for group in self.groups.values():
            group["region_ids"] -= remove_ids

        self._remove_empty_groups()

    def remove_color_subregions_for_selection(self):
        if not self.selected_region_ids:
            return

        parent_ids = set()

        for rid in self.selected_region_ids:
            region = self._region_by_id(rid)
            if not region:
                continue

            if region.get("is_overlay", False):
                parent_ids.add(region.get("parent_id"))
            else:
                parent_ids.add(region["id"])

        parent_ids.discard(None)

        self._remove_overlays_by_parent_ids(parent_ids)
        self.selected_region_ids.clear()

        self._refresh_group_list()
        self._update_counts()
        self.refresh_preview()

        self.status_var.set(
            "Farbbasierte Unterregionen der Auswahl wurden entfernt."
        )


    # ------------------------------------------------------------------
    # Color recovery for incomplete/open outline regions
    # ------------------------------------------------------------------

    def _palette_label_map_full_image(self):
        """
        Convert the complete colored reference into palette IDs using Lab
        distance. This lets us recover color islands even when the outline
        is not closed.
        """
        if self.color_bgr is None or not self.palette:
            return None

        h, w = self.color_bgr.shape[:2]

        color_img = self.color_bgr.copy()

        # A light median blur removes antialias speckles without changing
        # larger colored cells much.
        smooth_size = max(1, int(self.split_smooth_var.get()))
        if smooth_size % 2 == 0:
            smooth_size += 1
        if smooth_size > 1:
            color_img = cv2.medianBlur(color_img, smooth_size)

        flat_bgr = color_img.reshape(-1, 1, 3)
        flat_lab = cv2.cvtColor(flat_bgr, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)

        centers = []
        ids = []

        for entry in self.palette:
            rgb = np.array(entry["rgb"], dtype=np.uint8).reshape(1, 1, 3)
            bgr = rgb[:, :, ::-1]
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).reshape(3).astype(np.float32)
            centers.append(lab)
            ids.append(int(entry["id"]))

        centers = np.array(centers, dtype=np.float32)
        dists = ((flat_lab[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        nearest = np.argmin(dists, axis=1)

        mapped = np.array([ids[i] for i in nearest], dtype=np.int16)
        return mapped.reshape(h, w)

    def _existing_region_same_color_overlap(self, candidate_mask, color_id):
        """
        Return the best overlap ratio with an already existing region that
        is assigned to the same palette color. If overlap is high, the
        candidate is already represented and does not need recovery.
        """
        area = int(candidate_mask.sum())
        if area <= 0:
            return 0.0

        best = 0.0

        for region in self.regions:
            if region.get("is_recovered", False):
                continue

            rid = region.get("suggested_color_id")
            group = self._group_for_region(region["id"])
            if group is not None:
                rid = group.get("color_id")

            if rid != color_id:
                continue

            rmask = self._region_mask(region)
            if rmask is None:
                continue

            overlap = int(np.logical_and(candidate_mask, rmask).sum())
            ratio = overlap / max(1, area)
            best = max(best, ratio)

            if best >= 0.82:
                break

        return best

    def recover_missing_regions_from_color(self):
        """
        Detect connected palette-color islands in the colored reference.
        If an island is not already represented by a region of the same
        target color, create a high-priority recovered overlay region.
        """
        if not self.recovery_enabled_var.get():
            messagebox.showinfo(
                "Hinweis",
                "Die farbbasierte Wiederherstellung ist deaktiviert.",
            )
            return

        if self.color_bgr is None:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst eine kolorierte Farbvorlage laden.",
            )
            return

        if not self.palette:
            self.analyze_colors()
            if not self.palette:
                return

        if self.labels is None:
            return

        # Recalculate from scratch to avoid duplicates.
        self.remove_recovered_regions(refresh=False)

        color_map = self._palette_label_map_full_image()
        if color_map is None:
            return

        min_area = max(1, int(self.recovery_min_area_var.get()))
        erode_px = max(0, int(self.recovery_erode_var.get()))

        next_id = max([r["id"] for r in self.regions], default=0) + 1
        created = 0
        skipped_existing = 0
        skipped_small = 0

        h, w = color_map.shape

        for entry in self.palette:
            color_id = int(entry["id"])

            mask = (color_map == color_id).astype(np.uint8) * 255

            # Ignore very dark outline-like source pixels even if palette
            # clustering assigned them to a nearby color.
            hsv = cv2.cvtColor(self.color_bgr, cv2.COLOR_BGR2HSV)
            if self.ignore_dark_var.get():
                mask[hsv[:, :, 2] <= int(self.dark_threshold_var.get())] = 0

            if erode_px > 0:
                kernel_size = erode_px * 2 + 1
                kernel = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE,
                    (kernel_size, kernel_size),
                )
                mask = cv2.erode(mask, kernel, iterations=1)

            # Remove one-pixel islands while preserving real small cells.
            tiny_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, tiny_kernel)

            n, comps, stats, cents = cv2.connectedComponentsWithStats(
                (mask > 0).astype(np.uint8),
                connectivity=8,
            )

            for comp_id in range(1, n):
                area = int(stats[comp_id, cv2.CC_STAT_AREA])

                if area < min_area:
                    skipped_small += 1
                    continue

                comp_mask = comps == comp_id

                # Skip a color island if it is already substantially covered
                # by an existing region with the same color assignment.
                overlap = self._existing_region_same_color_overlap(
                    comp_mask,
                    color_id,
                )
                if overlap >= 0.72:
                    skipped_existing += 1
                    continue

                contour_img = comp_mask.astype(np.uint8) * 255
                contours, _ = cv2.findContours(
                    contour_img,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE,
                )
                if not contours:
                    continue

                contour = max(contours, key=cv2.contourArea)
                approx = cv2.approxPolyDP(
                    contour,
                    float(self.simplify_var.get()),
                    True,
                )
                points = approx.reshape(-1, 2)

                if len(points) < 3:
                    continue

                x = int(stats[comp_id, cv2.CC_STAT_LEFT])
                y = int(stats[comp_id, cv2.CC_STAT_TOP])
                ww = int(stats[comp_id, cv2.CC_STAT_WIDTH])
                hh = int(stats[comp_id, cv2.CC_STAT_HEIGHT])
                cx, cy = cents[comp_id]

                rgb = self._palette_rgb(color_id)

                self.regions.append(
                    {
                        "id": next_id,
                        "source_label": None,
                        "area": area,
                        "bbox": [x, y, ww, hh],
                        "centroid": [float(cx), float(cy)],
                        "points": points.tolist(),
                        "active": True,
                        "target_color": list(rgb) if rgb is not None else None,
                        "suggested_color_id": color_id,
                        "parent_id": None,
                        "is_overlay": True,
                        "is_micro": False,
                        "is_recovered": True,
                        "priority": 2,
                        "mask": comp_mask.copy(),
                    }
                )

                next_id += 1
                created += 1

        self.regions.sort(
            key=lambda r: (
                int(r.get("priority", 0)),
                int(r["id"]),
            )
        )

        self.selected_region_ids.clear()
        self._update_counts()
        self.refresh_preview()

        self.status_var.set(
            f"Recovery abgeschlossen: {created} Regionen ergänzt, "
            f"{skipped_existing} bereits vorhanden, "
            f"{skipped_small} zu klein."
        )

    def remove_recovered_regions(self, refresh=True):
        remove_ids = {
            region["id"]
            for region in self.regions
            if region.get("is_recovered", False)
        }

        if not remove_ids:
            return

        self.regions = [
            region
            for region in self.regions
            if region["id"] not in remove_ids
        ]

        self.selected_region_ids -= remove_ids

        for group in self.groups.values():
            group["region_ids"] -= remove_ids

        self._remove_empty_groups()

        if refresh:
            self._refresh_group_list()
            self._update_counts()
            self.refresh_preview()
            self.status_var.set(
                "Recovery-Regionen wurden entfernt."
            )

    # ------------------------------------------------------------------
    # Helpers / groups
    # ------------------------------------------------------------------

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

        for group in self.groups.values():
            grouped |= set(group["region_ids"])

        ungrouped = sum(
            1
            for r in self.regions
            if r["active"] and r["id"] not in grouped
        )

        self.region_count_var.set(f"Regionen: {len(self.regions)}")
        self.active_count_var.set(f"Aktiv: {active}")
        self.selected_count_var.set(f"Ausgewählt: {len(self.selected_region_ids)}")
        self.group_count_var.set(f"Gruppen: {len(self.groups)}")
        self.ungrouped_count_var.set(f"Ungegruppiert: {ungrouped}")

    @staticmethod
    def _fallback_color(index):
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

    def _palette_rgb(self, color_id):
        for entry in self.palette:
            if entry["id"] == color_id:
                return tuple(entry["rgb"])

        return None

    @staticmethod
    def _rgb_to_hex(rgb):
        return "#{:02X}{:02X}{:02X}".format(
            int(rgb[0]),
            int(rgb[1]),
            int(rgb[2]),
        )

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def make_preview(self):
        if self.labels is None or self.line_mask is None:
            return None

        h, w = self.labels.shape
        preview = np.full((h, w, 3), 255, dtype=np.uint8)

        grouped_ids = set()

        for group in self.groups.values():
            grouped_ids |= set(group["region_ids"])

        for region in self.regions:
            mask = self._region_mask(region)
            if mask is None:
                continue

            if not region["active"]:
                if self.show_inactive_var.get():
                    preview[mask] = (232, 232, 232)
                continue

            group = self._group_for_region(region["id"])

            rgb = None

            if self.use_real_colors_var.get():
                if group:
                    if group.get("color_id"):
                        rgb = self._palette_rgb(group["color_id"])
                    if rgb is None:
                        rgb = group.get("target_color")
                else:
                    sid = region.get("suggested_color_id")
                    if sid:
                        rgb = self._palette_rgb(sid)
                    if rgb is None:
                        rgb = region.get("target_color")

            if rgb is None:
                if group:
                    rgb = self._fallback_color(group["color_id"] - 1)
                else:
                    rgb = self._fallback_color(region["id"] - 1)

            preview[mask] = np.array(rgb, dtype=np.uint8)

            if (
                self.highlight_ungrouped_var.get()
                and region["id"] not in grouped_ids
            ):
                contours, _ = cv2.findContours(
                    mask.astype(np.uint8) * 255,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE,
                )
                cv2.drawContours(
                    preview,
                    contours,
                    -1,
                    (255, 90, 0),
                    2,
                )

        preview[self.line_mask > 0] = (25, 25, 25)

        # Mark manually added regions in green.
        for region in self.regions:
            if not region.get("is_manual", False) or not region.get("active", True):
                continue
            rmask = self._region_mask(region)
            if rmask is None:
                continue
            contours, _ = cv2.findContours(
                rmask.astype(np.uint8) * 255,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            cv2.drawContours(preview, contours, -1, (60, 255, 60), 2)

        # Mark automatically recovered regions so they are easy to review.
        for region in self.regions:
            if not region.get("is_recovered", False) or not region.get("active", True):
                continue
            rmask = self._region_mask(region)
            if rmask is None:
                continue
            contours, _ = cv2.findContours(
                rmask.astype(np.uint8) * 255,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            cv2.drawContours(
                preview,
                contours,
                -1,
                (0, 220, 255),
                2,
            )

        # Selected regions
        for rid in self.selected_region_ids:
            region = self._region_by_id(rid)

            if not region:
                continue

            rmask = self._region_mask(region)
            if rmask is None:
                continue
            mask = rmask.astype(np.uint8) * 255

            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            cv2.drawContours(
                preview,
                contours,
                -1,
                (255, 0, 255),
                4,
            )

        if self.show_numbers_var.get():
            # Technical IDs / suggested IDs for ungrouped regions
            for region in self.regions:
                if not region["active"]:
                    continue
                if self._group_for_region(region["id"]):
                    continue
                if (
                    not region.get("force_label", False)
                    and region["area"] < max(
                        500,
                        int(self.min_area_var.get()) * 2,
                    )
                ):
                    continue

                text = str(
                    region.get("suggested_color_id")
                    or region["id"]
                )

                self._draw_number(
                    preview,
                    region["centroid"],
                    text,
                )

            # One number per logical group
            for group in self.groups.values():
                if not group["region_ids"]:
                    continue

                pos = group.get("label_position")

                if pos is None:
                    pos = self._calculate_group_center(group)

                if pos is not None:
                    self._draw_number(
                        preview,
                        pos,
                        str(group["color_id"]),
                        radius=15,
                    )

        return preview

    def _draw_number(self, img, pos, text, radius=13):
        cx, cy = map(int, pos)

        cv2.circle(
            img,
            (cx, cy),
            radius,
            (255, 255, 255),
            -1,
        )

        cv2.circle(
            img,
            (cx, cy),
            radius,
            (30, 30, 30),
            1,
        )

        ts = cv2.getTextSize(
            text,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            1,
        )[0]

        cv2.putText(
            img,
            text,
            (
                cx - ts[0] // 2,
                cy + ts[1] // 2,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (25, 25, 25),
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

        # Base scale always fits the complete artwork into the available
        # preview height/width. zoom_factor is relative to that fitted view.
        fit_scale = max(0.01, min(canvas_w / w, canvas_h / h))
        scale = fit_scale * self.zoom_factor

        display_w = max(1, int(w * scale))
        display_h = max(1, int(h * scale))

        pil = Image.fromarray(preview).resize(
            (display_w, display_h),
            Image.Resampling.LANCZOS,
        )

        self.preview_photo = ImageTk.PhotoImage(pil)

        self.display_scale = scale
        self.display_offset_x = (canvas_w - display_w) // 2 + int(self.pan_x)
        self.display_offset_y = (canvas_h - display_h) // 2 + int(self.pan_y)
        if hasattr(self, "zoom_text_var"):
            self.zoom_text_var.set("Fit" if abs(self.zoom_factor - 1.0) < 0.001 else f"{self.zoom_factor * 100:.0f}%")

        self.canvas.delete("all")
        self.canvas.create_image(
            self.display_offset_x,
            self.display_offset_y,
            image=self.preview_photo,
            anchor="nw",
        )


    # ------------------------------------------------------------------
    # Manual missing-region recovery
    # ------------------------------------------------------------------

    def _raw_component_at(self, x, y):
        """Find the raw white component at a click without morphology closing."""
        if self.gray is None:
            return None

        threshold = int(self.threshold_var.get())
        raw_line = (self.gray < threshold).astype(np.uint8) * 255
        raw_white = cv2.bitwise_not(raw_line)
        raw_binary = (raw_white > 0).astype(np.uint8)

        h, w = raw_binary.shape
        if not (0 <= x < w and 0 <= y < h) or raw_binary[y, x] == 0:
            return None

        _count, labels, stats, centroids = cv2.connectedComponentsWithStats(
            raw_binary, connectivity=8
        )

        label_id = int(labels[y, x])
        if label_id <= 0:
            return None

        area = int(stats[label_id, cv2.CC_STAT_AREA])
        mask = labels == label_id

        contour_img = mask.astype(np.uint8) * 255
        contours, _ = cv2.findContours(
            contour_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None

        contour = max(contours, key=cv2.contourArea)
        approx = cv2.approxPolyDP(
            contour, float(self.simplify_var.get()), True
        )
        points = approx.reshape(-1, 2)
        if len(points) < 3:
            return None

        xx = int(stats[label_id, cv2.CC_STAT_LEFT])
        yy = int(stats[label_id, cv2.CC_STAT_TOP])
        ww = int(stats[label_id, cv2.CC_STAT_WIDTH])
        hh = int(stats[label_id, cv2.CC_STAT_HEIGHT])
        cx, cy = centroids[label_id]

        return {
            "mask": mask,
            "area": area,
            "bbox": [xx, yy, ww, hh],
            "centroid": [float(cx), float(cy)],
            "points": points.tolist(),
        }

    def _color_component_at(self, x, y):
        """Fallback: recover the clicked connected palette-color island."""
        if self.color_bgr is None or not self.palette:
            return None

        color_map = self._palette_label_map_full_image()
        if color_map is None:
            return None

        h, w = color_map.shape
        if not (0 <= x < w and 0 <= y < h):
            return None

        color_id = int(color_map[y, x])
        if color_id <= 0:
            return None

        mask = (color_map == color_id).astype(np.uint8)

        hsv = cv2.cvtColor(self.color_bgr, cv2.COLOR_BGR2HSV)
        if self.ignore_dark_var.get():
            mask[hsv[:, :, 2] <= int(self.dark_threshold_var.get())] = 0

        _count, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask, connectivity=8
        )

        label_id = int(labels[y, x])
        if label_id <= 0:
            return None

        comp_mask = labels == label_id
        area = int(stats[label_id, cv2.CC_STAT_AREA])

        contour_img = comp_mask.astype(np.uint8) * 255
        contours, _ = cv2.findContours(
            contour_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None

        contour = max(contours, key=cv2.contourArea)
        approx = cv2.approxPolyDP(
            contour, float(self.simplify_var.get()), True
        )
        points = approx.reshape(-1, 2)
        if len(points) < 3:
            return None

        xx = int(stats[label_id, cv2.CC_STAT_LEFT])
        yy = int(stats[label_id, cv2.CC_STAT_TOP])
        ww = int(stats[label_id, cv2.CC_STAT_WIDTH])
        hh = int(stats[label_id, cv2.CC_STAT_HEIGHT])
        cx, cy = centroids[label_id]

        return {
            "mask": comp_mask,
            "area": area,
            "bbox": [xx, yy, ww, hh],
            "centroid": [float(cx), float(cy)],
            "points": points.tolist(),
            "suggested_color_id": color_id,
        }

    def _find_existing_region_covering_point(self, x, y):
        candidates = []

        for region in self.regions:
            if not region.get("active", True):
                continue
            mask = self._region_mask(region)
            if mask is not None and bool(mask[y, x]):
                candidates.append(region)

        if not candidates:
            return None

        return sorted(
            candidates,
            key=lambda r: (
                -int(r.get("priority", 0)),
                int(r.get("area", 0)),
            ),
        )[0]

    def add_missing_region_at(self, x, y):
        """
        Click once:
        - existing tiny region -> force a visible color number
        - otherwise add raw outline component
        - fallback to colored-reference island
        - derive target color automatically
        """
        if self.labels is None:
            return

        existing = self._find_existing_region_covering_point(x, y)

        if existing is not None:
            existing["force_label"] = True

            if self.color_bgr is not None:
                color = self._extract_color_for_region(existing)
                if color is not None:
                    existing["target_color"] = color
                    if self.palette:
                        existing["suggested_color_id"] = self._nearest_palette_id(color)

            self.selected_region_ids = {existing["id"]}
            self._update_counts()
            self.refresh_preview()

            self.status_var.set(
                f"Region {existing['id']} übernommen. "
                f"Farb-ID {existing.get('suggested_color_id') or 'noch nicht bestimmt'}."
            )
            return

        component = self._raw_component_at(x, y)
        source = "Outline"

        if component is None:
            component = self._color_component_at(x, y)
            source = "Farbvorlage"

        if component is None:
            self.status_var.set(
                "An dieser Stelle konnte keine geeignete Fläche ermittelt werden."
            )
            return

        next_id = max([r["id"] for r in self.regions], default=0) + 1

        new_region = {
            "id": next_id,
            "source_label": None,
            "area": int(component["area"]),
            "bbox": component["bbox"],
            "centroid": component["centroid"],
            "points": component["points"],
            "active": True,
            "target_color": None,
            "suggested_color_id": component.get("suggested_color_id"),
            "parent_id": None,
            "is_overlay": False,
            "is_micro": True,
            "is_recovered": source == "Farbvorlage",
            "is_manual": True,
            "force_label": True,
            "priority": 3,
            "mask": component["mask"].copy(),
        }

        if self.color_bgr is not None:
            color = self._representative_color(
                self.color_bgr[new_region["mask"]]
            )
            if color is not None:
                new_region["target_color"] = color
                if self.palette:
                    new_region["suggested_color_id"] = self._nearest_palette_id(color)

        self.regions.append(new_region)
        self.selected_region_ids = {next_id}

        self._update_counts()
        self.refresh_preview()

        self.status_var.set(
            f"Manuelle Region {next_id} aus {source} hinzugefügt, "
            f"{new_region['area']} px, "
            f"Farb-ID {new_region.get('suggested_color_id') or 'noch nicht bestimmt'}."
        )

    # ------------------------------------------------------------------
    # Mouse editing
    # ------------------------------------------------------------------

    def on_canvas_click(self, event):
        if self.labels is None:
            return

        x = int(
            (event.x - self.display_offset_x)
            / self.display_scale
        )
        y = int(
            (event.y - self.display_offset_y)
            / self.display_scale
        )

        h, w = self.labels.shape

        if not (0 <= x < w and 0 <= y < h):
            return

        if self.mode_var.get() == "manual_add":
            self.add_missing_region_at(x, y)
            return

        if self.mode_var.get() == "label":
            gid = self._selected_group_id()

            if gid is None or gid not in self.groups:
                messagebox.showinfo(
                    "Hinweis",
                    "Bitte zuerst eine Gruppe in der Liste auswählen.",
                )
                return

            self.groups[gid]["label_position"] = [
                float(x),
                float(y),
            ]

            self.status_var.set(
                f"Label-Position für Gruppe {gid} gesetzt."
            )

            self.refresh_preview()
            return

        clicked = None

        # Generated color subregions should win over their larger base region.
        candidates = []
        for region in self.regions:
            if not region.get("active", True):
                continue
            mask = self._region_mask(region)
            if mask is not None and bool(mask[y, x]):
                candidates.append(region)

        if candidates:
            clicked = sorted(
                candidates,
                key=lambda r: (
                    -int(r.get("priority", 0)),
                    int(r.get("area", 0)),
                ),
            )[0]

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
                f"Region {rid}: Gruppe {group['id']}, Farb-ID {group['color_id']}."
            )
        else:
            suggested = clicked.get("suggested_color_id")
            extra = (
                f", vorgeschlagene Farb-ID {suggested}"
                if suggested else ""
            )
            self.status_var.set(
                f"Region {rid} ausgewählt{extra}."
            )

        self._update_counts()
        self.refresh_preview()

    # ------------------------------------------------------------------
    # Group editing
    # ------------------------------------------------------------------

    def clear_selection(self):
        self.selected_region_ids.clear()
        self._update_counts()
        self.refresh_preview()

    def create_group(self):
        if not self.selected_region_ids:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst Regionen auswählen.",
            )
            return

        self.remove_selection_from_groups(refresh=False)

        gid = self.next_group_id
        self.next_group_id += 1

        name = (
            self.group_name_var.get().strip()
            or f"Gruppe {gid}"
        )

        selected_regions = [
            self._region_by_id(rid)
            for rid in self.selected_region_ids
        ]

        # Prefer automatic color if available.
        automatic_ids = [
            r.get("suggested_color_id")
            for r in selected_regions
            if r and r.get("suggested_color_id")
        ]

        if automatic_ids:
            color_id = max(
                set(automatic_ids),
                key=automatic_ids.count,
            )
        else:
            color_id = max(
                1,
                int(self.color_id_var.get()),
            )

        group = {
            "id": gid,
            "name": name,
            "color_id": color_id,
            "region_ids": set(self.selected_region_ids),
            "label_position": None,
            "target_color": None,
        }

        group["label_position"] = self._calculate_group_center(group)

        if self.color_bgr is not None:
            group["target_color"] = self._extract_color_for_group(group)

            if self.palette and group["target_color"] is not None:
                group["color_id"] = self._nearest_palette_id(
                    group["target_color"]
                )

        self.groups[gid] = group
        self.color_id_var.set(group["color_id"])
        self.group_name_var.set("")

        self._refresh_group_list(gid)
        self._update_counts()
        self.refresh_preview()

        self.status_var.set(
            f"{name} erstellt: {len(group['region_ids'])} Regionen, Farb-ID {group['color_id']}."
        )

    def add_selection_to_group(self):
        gid = self._selected_group_id()

        if gid is None or gid not in self.groups:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst eine Zielgruppe auswählen.",
            )
            return

        if not self.selected_region_ids:
            messagebox.showinfo(
                "Hinweis",
                "Bitte Regionen auswählen.",
            )
            return

        for other_gid, group in self.groups.items():
            if other_gid != gid:
                group["region_ids"] -= self.selected_region_ids

        self.groups[gid]["region_ids"] |= self.selected_region_ids
        self._remove_empty_groups()

        group = self.groups[gid]
        group["label_position"] = self._calculate_group_center(group)

        if self.color_bgr is not None:
            group["target_color"] = self._extract_color_for_group(group)

            if self.palette and group["target_color"] is not None:
                group["color_id"] = self._nearest_palette_id(
                    group["target_color"]
                )

        self._refresh_group_list(gid)
        self._update_counts()
        self.refresh_preview()

        self.status_var.set(
            "Regionen zur Gruppe hinzugefügt."
        )

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

            self.status_var.set(
                "Regionen aus Gruppen entfernt."
            )

    def update_selected_group(self):
        gid = self._selected_group_id()

        if gid is None or gid not in self.groups:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst eine Gruppe auswählen.",
            )
            return

        group = self.groups[gid]

        group["name"] = (
            self.group_name_var.get().strip()
            or group["name"]
        )

        group["color_id"] = max(
            1,
            int(self.color_id_var.get()),
        )

        # Update target color to chosen palette color where possible.
        palette_rgb = self._palette_rgb(group["color_id"])

        if palette_rgb is not None:
            group["target_color"] = list(palette_rgb)

        self._refresh_group_list(gid)
        self.refresh_preview()

        self.status_var.set(
            f"Gruppe {gid} aktualisiert."
        )

    def analyze_selected_group_color(self):
        gid = self._selected_group_id()

        if gid is None or gid not in self.groups:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst eine Gruppe auswählen.",
            )
            return

        if self.color_bgr is None:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst eine Farbvorlage laden.",
            )
            return

        group = self.groups[gid]
        color = self._extract_color_for_group(group)

        if color is None:
            messagebox.showwarning(
                "Farbanalyse",
                "Für diese Gruppe konnte keine brauchbare Farbe bestimmt werden.",
            )
            return

        group["target_color"] = color

        if self.palette:
            group["color_id"] = self._nearest_palette_id(color)

        self.color_id_var.set(group["color_id"])
        self._refresh_group_list(gid)
        self.refresh_preview()

        self.status_var.set(
            f"Farbe für Gruppe {gid} neu analysiert."
        )

    def auto_center_group_label(self):
        gid = self._selected_group_id()

        if gid is None or gid not in self.groups:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst eine Gruppe auswählen.",
            )
            return

        self.groups[gid]["label_position"] = (
            self._calculate_group_center(
                self.groups[gid]
            )
        )

        self.refresh_preview()

        self.status_var.set(
            f"Label von Gruppe {gid} automatisch zentriert."
        )

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

        self.status_var.set(
            f"{name} gelöscht."
        )

    def _remove_empty_groups(self):
        for gid in [
            gid
            for gid, group in self.groups.items()
            if not group["region_ids"]
        ]:
            del self.groups[gid]

    def _refresh_group_list(self, select_group_id=None):
        self.group_list.delete(0, tk.END)

        select_index = None

        for idx, gid in enumerate(sorted(self.groups)):
            group = self.groups[gid]

            color_hex = ""

            if group.get("target_color"):
                color_hex = " " + self._rgb_to_hex(
                    group["target_color"]
                )

            self.group_list.insert(
                tk.END,
                (
                    f"{gid} | Farbe {group['color_id']}{color_hex} | "
                    f"{group['name']} | {len(group['region_ids'])} Regionen"
                ),
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

        self.status_var.set(
            f"Gruppe {gid} ausgewählt."
        )

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

    # ------------------------------------------------------------------
    # Project save/load
    # ------------------------------------------------------------------

    def save_project(self):
        if self.image_path is None or self.labels is None:
            messagebox.showinfo(
                "Hinweis",
                "Bitte zuerst ein Bild analysieren.",
            )
            return

        path = filedialog.asksaveasfilename(
            title="Projekt speichern",
            defaultextension=".json",
            initialfile=f"{self.image_path.stem}_project.json",
            filetypes=[("JSON", "*.json")],
        )

        if not path:
            return

        Path(path).write_text(
            json.dumps(
                self._project_data(),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.status_var.set(
            f"Projekt gespeichert: {Path(path).name}"
        )

    def load_project(self):
        path = filedialog.askopenfilename(
            title="Projekt laden",
            filetypes=[("JSON", "*.json")],
        )

        if not path:
            return

        try:
            data = json.loads(
                Path(path).read_text(encoding="utf-8")
            )
        except Exception as exc:
            messagebox.showerror(
                "Fehler",
                f"Projekt konnte nicht geladen werden:\n{exc}",
            )
            return

        image_path = Path(
            data.get("image_path", "")
        )

        if not image_path.exists():
            chosen = filedialog.askopenfilename(
                title="Originalbild auswählen",
                filetypes=[
                    ("Bilder", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ],
            )

            if not chosen:
                return

            image_path = Path(chosen)

        bgr = cv2.imread(str(image_path))

        if bgr is None:
            messagebox.showerror(
                "Fehler",
                "Originalbild konnte nicht geladen werden.",
            )
            return

        self.image_path = image_path
        self.original_bgr = bgr
        self.gray = cv2.cvtColor(
            bgr,
            cv2.COLOR_BGR2GRAY,
        )

        params = data.get("parameters", {})

        self.threshold_var.set(
            params.get("threshold", 190)
        )
        self.close_size_var.set(
            params.get("close_size", 3)
        )
        self.min_area_var.set(
            params.get("min_area", 100)
        )
        self.simplify_var.set(
            params.get("simplify_epsilon", 1.5)
        )
        self.include_border_var.set(
            params.get("include_border_regions", True)
        )
        self.adaptive_micro_var.set(
            params.get("adaptive_micro", True)
        )
        self.micro_min_area_var.set(
            params.get("micro_min_area", 8)
        )

        color_params = data.get("color_parameters", {})
        self.palette_size_var.set(
            color_params.get("palette_size", 12)
        )
        self.dark_threshold_var.set(
            color_params.get("dark_threshold", 45)
        )
        self.light_threshold_var.set(
            color_params.get("light_threshold", 245)
        )
        self.ignore_dark_var.set(
            color_params.get("ignore_dark", True)
        )
        self.ignore_light_var.set(
            color_params.get("ignore_light", True)
        )
        self.split_min_area_var.set(
            color_params.get("split_min_area", 180)
        )
        self.split_smooth_var.set(
            color_params.get("split_smooth", 3)
        )
        self.relative_split_var.set(
            color_params.get("relative_split", False)
        )
        self.split_min_percent_var.set(
            color_params.get("split_min_percent", 0.08)
        )
        self.recovery_enabled_var.set(
            color_params.get("recovery_enabled", True)
        )
        self.recovery_min_area_var.set(
            color_params.get("recovery_min_area", 20)
        )
        self.recovery_erode_var.set(
            color_params.get("recovery_erode", 1)
        )

        # Build current region geometry.
        self.analyze()

        # Restore color reference.
        saved_color_path = data.get("color_image_path")

        if saved_color_path:
            cp = Path(saved_color_path)

            if cp.exists():
                cbgr = cv2.imread(str(cp))

                if cbgr is not None:
                    h, w = self.original_bgr.shape[:2]

                    if cbgr.shape[:2] != (h, w):
                        cbgr = cv2.resize(
                            cbgr,
                            (w, h),
                            interpolation=cv2.INTER_AREA,
                        )

                    self.color_image_path = cp
                    self.color_bgr = cbgr
                    self.color_file_var.set(
                        f"Farbvorlage: {cp.name}"
                    )

        saved_regions = {
            int(r["id"]): r
            for r in data.get("regions", [])
        }

        for region in self.regions:
            saved = saved_regions.get(region["id"])

            if saved:
                region["active"] = saved.get(
                    "active",
                    True,
                )
                region["target_color"] = saved.get(
                    "target_color"
                )
                region["suggested_color_id"] = saved.get(
                    "suggested_color_id"
                )

        self.palette = data.get(
            "palette",
            [],
        )

        # Restore generated color subregions and recovered regions.
        current_ids = {r["id"] for r in self.regions}
        for saved in data.get("regions", []):
            if not (
                saved.get("is_overlay", False)
                or saved.get("is_recovered", False)
                or saved.get("is_manual", False)
            ):
                continue

            rid = int(saved["id"])
            if rid in current_ids:
                continue

            points = saved.get("points", [])
            if len(points) < 3:
                continue

            mask = np.zeros(self.labels.shape, dtype=np.uint8)
            pts = np.array(points, dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)

            self.regions.append({
                "id": rid,
                "source_label": None,
                "area": int(saved.get("area", int((mask > 0).sum()))),
                "bbox": saved.get("bbox", [0,0,0,0]),
                "centroid": saved.get("centroid", [0.0,0.0]),
                "points": points,
                "active": saved.get("active", True),
                "target_color": saved.get("target_color"),
                "suggested_color_id": saved.get("suggested_color_id"),
                "parent_id": saved.get("parent_id"),
                "is_overlay": bool(saved.get("is_overlay", True)),
                "is_micro": bool(saved.get("is_micro", False)),
                "is_recovered": bool(saved.get("is_recovered", False)),
                "is_manual": bool(saved.get("is_manual", False)),
                "force_label": bool(saved.get("force_label", False)),
                "priority": int(saved.get("priority", 1)),
                "mask": mask.astype(bool),
            })

        self.groups.clear()
        max_gid = 0

        for saved in data.get("groups", []):
            gid = int(saved["id"])
            max_gid = max(max_gid, gid)

            valid_ids = {
                int(rid)
                for rid in saved.get("region_ids", [])
                if self._region_by_id(int(rid)) is not None
            }

            self.groups[gid] = {
                "id": gid,
                "name": saved.get(
                    "name",
                    f"Gruppe {gid}",
                ),
                "color_id": int(
                    saved.get("color_id", 1)
                ),
                "region_ids": valid_ids,
                "label_position": saved.get(
                    "label_position"
                ),
                "target_color": saved.get(
                    "target_color"
                ),
            }

        self.next_group_id = max_gid + 1
        self.selected_region_ids.clear()

        self._remove_empty_groups()
        self._refresh_group_list()
        self._draw_palette()
        self._update_counts()
        self.refresh_preview()

        self.status_var.set(
            f"Projekt geladen: {Path(path).name}"
        )

    def _project_data(self):
        h, w = self.labels.shape

        return {
            "format": "coloring_region_project_v2",
            "image_path": (
                str(self.image_path.resolve())
                if self.image_path else None
            ),
            "color_image_path": (
                str(self.color_image_path.resolve())
                if self.color_image_path else None
            ),
            "width": w,
            "height": h,
            "parameters": {
                "threshold": int(self.threshold_var.get()),
                "close_size": int(self.close_size_var.get()),
                "min_area": int(self.min_area_var.get()),
                "simplify_epsilon": float(self.simplify_var.get()),
                "include_border_regions": bool(self.include_border_var.get()),
                "adaptive_micro": bool(self.adaptive_micro_var.get()),
                "micro_min_area": int(self.micro_min_area_var.get()),
            },
            "color_parameters": {
                "palette_size": int(self.palette_size_var.get()),
                "ignore_dark": bool(self.ignore_dark_var.get()),
                "ignore_light": bool(self.ignore_light_var.get()),
                "dark_threshold": int(self.dark_threshold_var.get()),
                "light_threshold": int(self.light_threshold_var.get()),
                "split_min_area": int(self.split_min_area_var.get()),
                "split_smooth": int(self.split_smooth_var.get()),
                "relative_split": bool(self.relative_split_var.get()),
                "split_min_percent": float(self.split_min_percent_var.get()),
                "recovery_enabled": bool(self.recovery_enabled_var.get()),
                "recovery_min_area": int(self.recovery_min_area_var.get()),
                "recovery_erode": int(self.recovery_erode_var.get()),
            },
            "palette": self.palette,
            "regions": [
                {
                    "id": region["id"],
                    "active": region["active"],
                    "area": region["area"],
                    "bbox": region["bbox"],
                    "centroid": region["centroid"],
                    "points": region["points"],
                    "target_color": region.get("target_color"),
                    "suggested_color_id": region.get("suggested_color_id"),
                    "parent_id": region.get("parent_id"),
                    "is_overlay": bool(region.get("is_overlay", False)),
                    "is_micro": bool(region.get("is_micro", False)),
                    "is_recovered": bool(region.get("is_recovered", False)),
                    "is_manual": bool(region.get("is_manual", False)),
                    "force_label": bool(region.get("force_label", False)),
                    "priority": int(region.get("priority", 0)),
                }
                for region in self.regions
            ],
            "groups": [
                {
                    "id": group["id"],
                    "name": group["name"],
                    "color_id": group["color_id"],
                    "region_ids": sorted(group["region_ids"]),
                    "label_position": group.get("label_position"),
                    "target_color": group.get("target_color"),
                }
                for _, group in sorted(self.groups.items())
            ],
        }

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_svg(self):
        if self.labels is None:
            return

        path = filedialog.asksaveasfilename(
            title="Game SVG exportieren",
            defaultextension=".svg",
            initialfile=(
                f"{self.image_path.stem}_game.svg"
                if self.image_path else "game.svg"
            ),
            filetypes=[("SVG", "*.svg")],
        )

        if not path:
            return

        h, w = self.labels.shape

        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            ),
            '<g id="game_areas">',
        ]

        exported = set()

        for gid in sorted(self.groups):
            group = self.groups[gid]

            active_regions = [
                self._region_by_id(rid)
                for rid in sorted(group["region_ids"])
            ]

            active_regions = [
                region
                for region in active_regions
                if region and region["active"]
            ]

            if not active_regions:
                continue

            safe_name = "".join(
                ch if ch.isalnum() or ch in "_-" else "_"
                for ch in group["name"]
            )

            label_pos = (
                group.get("label_position")
                or self._calculate_group_center(group)
            )

            lx, ly = (
                label_pos
                if label_pos else (0, 0)
            )

            rgb = (
                self._palette_rgb(group["color_id"])
                or group.get("target_color")
                or (217, 217, 217)
            )

            color_hex = self._rgb_to_hex(rgb)

            parts.append(
                (
                    f'<g id="group_{gid:03d}" '
                    f'data-group-id="{gid}" '
                    f'data-name="{safe_name}" '
                    f'data-color-id="{group["color_id"]}" '
                    f'data-color="{color_hex}" '
                    f'data-label-x="{lx:.2f}" '
                    f'data-label-y="{ly:.2f}">'
                )
            )

            for region in active_regions:
                exported.add(region["id"])

                d = (
                    "M "
                    + " ".join(
                        f"{float(x):.2f},{float(y):.2f}"
                        for x, y in region["points"]
                    )
                    + " Z"
                )

                parts.append(
                    (
                        f'<path id="group_{gid:03d}_region_{region["id"]:03d}" '
                        f'data-region-id="{region["id"]}" '
                        f'data-priority="{int(region.get("priority", 0))}" '
                        f'data-recovered="{1 if region.get("is_recovered", False) else 0}" '
                    f'data-manual="{1 if region.get("is_manual", False) else 0}" '
                        f'data-manual="{1 if region.get("is_manual", False) else 0}" '
                        f'data-parent-id="{region.get("parent_id") if region.get("parent_id") is not None else ""}" '
                        f'd="{d}" fill="{color_hex}" stroke="none"/>'
                    )
                )

            parts.append("</g>")

        # Ungrouped active regions remain exportable.
        for region in self.regions:
            if not region["active"] or region["id"] in exported:
                continue

            d = (
                "M "
                + " ".join(
                    f"{float(x):.2f},{float(y):.2f}"
                    for x, y in region["points"]
                )
                + " Z"
            )

            color_id = (
                region.get("suggested_color_id")
                or 0
            )

            rgb = (
                self._palette_rgb(color_id)
                or region.get("target_color")
                or (217, 217, 217)
            )

            color_hex = self._rgb_to_hex(rgb)

            parts.append(
                (
                    f'<g id="region_group_{region["id"]:03d}" '
                    f'data-group-id="region_{region["id"]:03d}" '
                    f'data-color-id="{color_id}" '
                    f'data-color="{color_hex}">'
                )
            )

            parts.append(
                (
                    f'<path id="region_{region["id"]:03d}" '
                    f'data-region-id="{region["id"]}" '
                    f'data-priority="{int(region.get("priority", 0))}" '
                    f'data-recovered="{1 if region.get("is_recovered", False) else 0}" '
                    f'data-manual="{1 if region.get("is_manual", False) else 0}" '
                    f'data-parent-id="{region.get("parent_id") if region.get("parent_id") is not None else ""}" '
                    f'd="{d}" fill="{color_hex}" stroke="none"/>'
                )
            )

            parts.append("</g>")

        parts.extend(
            [
                "</g>",
                "</svg>",
            ]
        )

        Path(path).write_text(
            "\n".join(parts),
            encoding="utf-8",
        )

        self.status_var.set(
            f"Game SVG gespeichert: {Path(path).name}"
        )

    def export_game_json(self):
        if self.labels is None:
            return

        path = filedialog.asksaveasfilename(
            title="Game JSON exportieren",
            defaultextension=".json",
            initialfile=(
                f"{self.image_path.stem}_game.json"
                if self.image_path else "game.json"
            ),
            filetypes=[("JSON", "*.json")],
        )

        if not path:
            return

        h, w = self.labels.shape

        game_areas = []
        grouped_ids = set()

        for gid in sorted(self.groups):
            group = self.groups[gid]

            active_ids = [
                rid
                for rid in sorted(group["region_ids"])
                if (
                    self._region_by_id(rid)
                    and self._region_by_id(rid)["active"]
                )
            ]

            if not active_ids:
                continue

            grouped_ids |= set(active_ids)

            label_pos = (
                group.get("label_position")
                or self._calculate_group_center(group)
            )

            rgb = (
                self._palette_rgb(group["color_id"])
                or group.get("target_color")
            )

            game_areas.append(
                {
                    "id": gid,
                    "name": group["name"],
                    "color_id": group["color_id"],
                    "target_color": rgb,
                    "target_color_hex": (
                        self._rgb_to_hex(rgb)
                        if rgb is not None else None
                    ),
                    "region_ids": active_ids,
                    "label_position": label_pos,
                }
            )

        data = {
            "format": "coloring_game_export_v2",
            "source": (
                self.image_path.name
                if self.image_path else None
            ),
            "color_reference": (
                self.color_image_path.name
                if self.color_image_path else None
            ),
            "width": w,
            "height": h,
            "palette": self.palette,
            "game_areas": game_areas,
            "ungrouped_active_regions": [
                {
                    "region_id": region["id"],
                    "color_id": region.get("suggested_color_id"),
                    "target_color": region.get("target_color"),
                    "parent_id": region.get("parent_id"),
                    "is_overlay": bool(region.get("is_overlay", False)),
                    "is_micro": bool(region.get("is_micro", False)),
                    "is_recovered": bool(region.get("is_recovered", False)),
                    "is_manual": bool(region.get("is_manual", False)),
                    "force_label": bool(region.get("force_label", False)),
                    "priority": int(region.get("priority", 0)),
                }
                for region in self.regions
                if (
                    region["active"]
                    and region["id"] not in grouped_ids
                )
            ],
        }

        Path(path).write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.status_var.set(
            f"Game JSON gespeichert: {Path(path).name}"
        )

    def export_outline_png(self):
        if self.line_mask is None:
            return

        path = filedialog.asksaveasfilename(
            title="Outline PNG exportieren",
            defaultextension=".png",
            initialfile=(
                f"{self.image_path.stem}_outline.png"
                if self.image_path else "outline.png"
            ),
            filetypes=[("PNG", "*.png")],
        )

        if not path:
            return

        h, w = self.line_mask.shape

        rgba = np.zeros(
            (h, w, 4),
            dtype=np.uint8,
        )

        rgba[..., :3] = 0
        rgba[..., 3] = self.line_mask

        Image.fromarray(
            rgba,
            mode="RGBA",
        ).save(path)

        self.status_var.set(
            f"Outline PNG gespeichert: {Path(path).name}"
        )

    def export_preview(self):
        preview = self.make_preview()

        if preview is None:
            return

        path = filedialog.asksaveasfilename(
            title="Vorschau speichern",
            defaultextension=".png",
            initialfile=(
                f"{self.image_path.stem}_preview.png"
                if self.image_path else "preview.png"
            ),
            filetypes=[("PNG", "*.png")],
        )

        if not path:
            return

        Image.fromarray(
            preview,
        ).save(path)

        self.status_var.set(
            f"Vorschau gespeichert: {Path(path).name}"
        )


if __name__ == "__main__":
    app = ColoringRegionExtractor()
    app.mainloop()
