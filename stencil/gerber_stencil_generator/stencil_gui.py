from __future__ import annotations

import json
import math
import queue
import threading
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from shapely import affinity
from shapely.geometry import Point

from stencil_core import (
    StencilError,
    StencilOptions,
    convert_gerber_to_stencil,
    create_library_aperture,
    list_openings,
    load_gerber_image,
    split_opening_grid,
)


class StencilApp(tk.Tk):
    BACKGROUND = "#15181c"

    def __init__(self) -> None:
        super().__init__()
        self.title("Gerber → герметичный STL-трафарет")
        self.minsize(1180, 720)
        self.geometry("1400x860")
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.thickness_var = tk.StringVar(value="0.12")
        self.margin_var = tk.StringVar(value="10.0")
        self.radius_var = tk.StringVar(value="2.0")
        self.offset_var = tk.StringVar(value="0.0")
        self.tolerance_var = tk.StringVar(value="0.01")
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.rotation_var = tk.StringVar(value="0")
        self.minimum_area_var = tk.StringVar(value="0")
        self.mirror_x_var = tk.BooleanVar(value=False)
        self.mirror_y_var = tk.BooleanVar(value=False)
        self.center_z_var = tk.BooleanVar(value=False)

        self.duplicate_dx_var = tk.StringVar(value="3.6")
        self.duplicate_dy_var = tk.StringVar(value="0.0")
        self.library_preset_var = tk.StringVar()
        self.library_rotation_var = tk.StringVar(value="0")
        self.grid_cell_width_var = tk.StringVar(value="3.0")
        self.grid_cell_height_var = tk.StringVar(value="3.0")
        self.grid_web_x_var = tk.StringVar(value="0.5")
        self.grid_web_y_var = tk.StringVar(value="0.5")
        self.grid_rotation_var = tk.StringVar(value="0")
        self.grid_min_area_var = tk.StringVar(value="0.02")

        self.preview_status_var = tk.StringVar(value="Выберите Gerber-файл.")
        self.zoom_status_var = tk.StringVar(value="Масштаб: —")

        # Preview records. Original IDs are stable geometry hashes; user-created
        # apertures use an "added:" prefix.
        self.original_records: dict[str, object] = {}
        self.added_records: dict[str, object] = {}
        self.excluded_ids: set[str] = set()
        self.selected_ids: set[str] = set()
        self.screen_bboxes: dict[str, tuple[float, float, float, float]] = {}

        # World-to-screen view state. Scale is pixels per millimetre.
        self.view_bounds: tuple[float, float, float, float] | None = None
        self.view_center: tuple[float, float] | None = None
        self.view_scale = 1.0
        self.fit_scale = 1.0
        self.view_is_fit = True
        self.cursor_world: tuple[float, float] | None = None

        # Mouse interaction state.
        self.drag_start: tuple[float, float] | None = None
        self.selection_rect: int | None = None
        self.pan_start_screen: tuple[float, float] | None = None
        self.pan_start_center: tuple[float, float] | None = None
        self.pending_aperture_preset: dict[str, object] | None = None

        self.library_presets: dict[str, dict[str, object]] = {}

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        controls = ttk.Frame(self, padding=10)
        controls.grid(row=0, column=0, sticky="nsew")
        controls.columnconfigure(0, weight=1)
        controls.rowconfigure(3, weight=1)

        preview_frame = ttk.Frame(self, padding=(0, 10, 10, 10))
        preview_frame.grid(row=0, column=1, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)

        preview_toolbar = ttk.Frame(preview_frame)
        preview_toolbar.grid(row=0, column=0, sticky="ew")
        preview_toolbar.columnconfigure(0, weight=1)
        ttk.Label(preview_toolbar, text="Предпросмотр апертур").grid(row=0, column=0, sticky="w")
        ttk.Label(preview_toolbar, textvariable=self.zoom_status_var).grid(
            row=0, column=1, sticky="e", padx=(8, 8)
        )
        ttk.Button(preview_toolbar, text="−", width=3, command=lambda: self._zoom_button(1 / 1.25)).grid(
            row=0, column=2, padx=1
        )
        ttk.Button(preview_toolbar, text="+", width=3, command=lambda: self._zoom_button(1.25)).grid(
            row=0, column=3, padx=1
        )
        ttk.Button(preview_toolbar, text="Вписать", command=self._fit_view).grid(
            row=0, column=4, padx=(4, 0)
        )

        self.canvas = tk.Canvas(
            preview_frame,
            background=self.BACKGROUND,
            highlightthickness=1,
            takefocus=True,
        )
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(5, 4))
        ttk.Label(preview_frame, textvariable=self.preview_status_var).grid(row=2, column=0, sticky="w")

        self.canvas.bind("<Configure>", self._canvas_configure)
        self.canvas.bind("<ButtonPress-1>", self._canvas_press)
        self.canvas.bind("<B1-Motion>", self._canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)
        self.canvas.bind("<ButtonPress-2>", self._pan_press)
        self.canvas.bind("<B2-Motion>", self._pan_drag)
        self.canvas.bind("<ButtonRelease-2>", self._pan_release)
        self.canvas.bind("<MouseWheel>", self._canvas_mousewheel)
        self.canvas.bind("<Button-4>", lambda event: self._zoom_at(event.x, event.y, 1.25))
        self.canvas.bind("<Button-5>", lambda event: self._zoom_at(event.x, event.y, 1 / 1.25))
        self.canvas.bind("<Motion>", self._canvas_motion)
        self.canvas.bind("<Leave>", self._canvas_leave)
        self.canvas.bind("<Control-a>", lambda _event: self._select_all())
        self.canvas.bind("<Home>", lambda _event: self._fit_view())
        self.canvas.bind("<KeyPress-f>", lambda _event: self._fit_view())
        self.canvas.bind("<KeyPress-plus>", lambda _event: self._zoom_button(1.25))
        self.canvas.bind("<KeyPress-equal>", lambda _event: self._zoom_button(1.25))
        self.canvas.bind("<KeyPress-minus>", lambda _event: self._zoom_button(1 / 1.25))
        self.canvas.bind("<Escape>", lambda _event: self._cancel_placement())
        self.canvas.bind("<Button-3>", lambda _event: self._cancel_placement())
        self.canvas.focus_set()

        paths = ttk.Frame(controls)
        paths.grid(row=0, column=0, sticky="ew")
        paths.columnconfigure(1, weight=1)
        row = 0
        row = self._path_row(paths, row, "Gerber пасты", self.input_var, self._choose_input)
        self._path_row(paths, row, "Выходной STL", self.output_var, self._choose_output)

        notebook = ttk.Notebook(controls)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(8, 6))
        parameters_tab = ttk.Frame(notebook, padding=8)
        editing_tab = ttk.Frame(notebook, padding=8)
        notebook.add(parameters_tab, text="Параметры")
        notebook.add(editing_tab, text="Правки апертур")
        parameters_tab.columnconfigure(1, weight=1)
        editing_tab.columnconfigure(0, weight=1)

        self._build_parameters_tab(parameters_tab)
        self._build_editing_tab(editing_tab)

        self.log = tk.Text(controls, width=50, height=7, wrap="word", state="disabled")
        self.log.grid(row=3, column=0, sticky="nsew", pady=4)

        self.convert_button = ttk.Button(controls, text="Создать STL", command=self._start_conversion)
        self.convert_button.grid(row=4, column=0, sticky="ew", pady=(5, 0))

        self._load_aperture_library()
        self.after(100, self._poll_events)

    def _build_parameters_tab(self, parent: ttk.Frame) -> None:
        row = 0
        row = self._entry_row(parent, row, "Толщина, мм", self.thickness_var)
        row = self._entry_row(parent, row, "Поле вокруг апертур, мм", self.margin_var)
        row = self._entry_row(parent, row, "Скругление углов, мм", self.radius_var)
        row = self._entry_row(parent, row, "Компенсация апертур, мм", self.offset_var)
        row = self._entry_row(parent, row, "Допуск дуг, мм", self.tolerance_var)
        row = self._entry_row(parent, row, "Фиксированная ширина, мм", self.width_var)
        row = self._entry_row(parent, row, "Фиксированная высота, мм", self.height_var)
        row = self._entry_row(parent, row, "Поворот, °", self.rotation_var)
        row = self._entry_row(parent, row, "Мин. площадь апертуры, мм²", self.minimum_area_var)

        flags = ttk.Frame(parent)
        flags.grid(row=row, column=0, columnspan=3, sticky="w", pady=8)
        ttk.Checkbutton(flags, text="Зеркально X", variable=self.mirror_x_var).pack(anchor="w")
        ttk.Checkbutton(flags, text="Зеркально Y", variable=self.mirror_y_var).pack(anchor="w")
        ttk.Checkbutton(flags, text="Толщина симметрично Z=0", variable=self.center_z_var).pack(anchor="w")

    def _build_editing_tab(self, parent: ttk.Frame) -> None:
        hint = (
            "Клик — выбрать; рамка — выбрать группу; Shift — добавить к выбору.\n"
            "Колесо — масштаб под курсором; средняя кнопка — перемещение; Home/F — вписать."
        )
        ttk.Label(parent, text=hint, wraplength=410, justify="left").grid(
            row=0, column=0, sticky="ew", pady=(0, 6)
        )
        ttk.Button(parent, text="Исключить / вернуть выбранные", command=self._toggle_excluded).grid(
            row=1, column=0, sticky="ew", pady=2
        )

        duplicate = ttk.LabelFrame(parent, text="Дублирование существующей апертуры", padding=6)
        duplicate.grid(row=2, column=0, sticky="ew", pady=(6, 2))
        duplicate.columnconfigure(1, weight=1)
        ttk.Label(duplicate, text="Смещение X, мм").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(duplicate, textvariable=self.duplicate_dx_var, width=12).grid(
            row=0, column=1, sticky="ew", padx=(6, 0), pady=2
        )
        ttk.Label(duplicate, text="Смещение Y, мм").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(duplicate, textvariable=self.duplicate_dy_var, width=12).grid(
            row=1, column=1, sticky="ew", padx=(6, 0), pady=2
        )
        ttk.Button(duplicate, text="Дублировать выбранные", command=self._duplicate_selected).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0)
        )

        library = ttk.LabelFrame(parent, text="Библиотека типовых апертур", padding=6)
        library.grid(row=3, column=0, sticky="ew", pady=(6, 2))
        library.columnconfigure(1, weight=1)
        ttk.Label(library, text="Пресет").grid(row=0, column=0, sticky="w", pady=2)
        self.library_combo = ttk.Combobox(
            library, textvariable=self.library_preset_var, state="readonly", width=28
        )
        self.library_combo.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=2)
        ttk.Label(library, text="Поворот, °").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(library, textvariable=self.library_rotation_var, width=12).grid(
            row=1, column=1, sticky="ew", padx=(6, 0), pady=2
        )
        ttk.Button(library, text="Поставить центром по клику", command=self._begin_library_placement).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0)
        )

        grid = ttk.LabelFrame(parent, text="Разбиение выбранных апертур сеткой", padding=6)
        grid.grid(row=4, column=0, sticky="ew", pady=(6, 2))
        grid.columnconfigure(1, weight=1)
        entries = [
            ("Макс. ячейка X, мм", self.grid_cell_width_var),
            ("Макс. ячейка Y, мм", self.grid_cell_height_var),
            ("Перемычка X, мм", self.grid_web_x_var),
            ("Перемычка Y, мм", self.grid_web_y_var),
            ("Поворот сетки, °", self.grid_rotation_var),
            ("Мин. площадь фрагмента, мм²", self.grid_min_area_var),
        ]
        for row, (label, variable) in enumerate(entries):
            ttk.Label(grid, text=label).grid(row=row, column=0, sticky="w", pady=1)
            ttk.Entry(grid, textvariable=variable, width=12).grid(
                row=row, column=1, sticky="ew", padx=(6, 0), pady=1
            )
        ttk.Button(grid, text="Разбить выбранные", command=self._split_selected_grid).grid(
            row=len(entries), column=0, columnspan=2, sticky="ew", pady=(4, 0)
        )

        edit_buttons = ttk.Frame(parent)
        edit_buttons.grid(row=5, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(edit_buttons, text="Удалить добавленные", command=self._remove_selected_added).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(edit_buttons, text="Сбросить правки", command=self._clear_edits).pack(
            side="left", fill="x", expand=True, padx=(4, 0)
        )

    def _path_row(self, parent, row: int, label: str, variable: tk.StringVar, command) -> int:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable, width=34).grid(
            row=row, column=1, sticky="ew", padx=5, pady=4
        )
        ttk.Button(parent, text="Обзор…", command=command).grid(row=row, column=2, pady=4)
        return row + 1

    def _entry_row(self, parent, row: int, label: str, variable: tk.StringVar) -> int:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable, width=14).grid(
            row=row, column=1, sticky="ew", padx=5, pady=3
        )
        return row + 1

    def _choose_input(self) -> None:
        filename = filedialog.askopenfilename(
            title="Выберите Gerber paste-mask",
            filetypes=[("Gerber", "*.gtp *.gbp *.gbr *.ger *.gerber"), ("Все файлы", "*.*")],
        )
        if filename:
            self.input_var.set(filename)
            input_path = Path(filename)
            self.output_var.set(str(input_path.with_suffix(".stencil.stl")))
            self._start_preview_load(input_path)

    def _choose_output(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Сохранить STL",
            defaultextension=".stl",
            filetypes=[("STL", "*.stl")],
        )
        if filename:
            self.output_var.set(filename)

    @staticmethod
    def _optional_float(value: str) -> float | None:
        value = value.strip().replace(",", ".")
        return None if not value else float(value)

    @staticmethod
    def _float(value: str) -> float:
        return float(value.strip().replace(",", "."))

    def _build_options(self) -> StencilOptions:
        return StencilOptions(
            thickness_mm=self._float(self.thickness_var.get()),
            margin_mm=self._float(self.margin_var.get()),
            corner_radius_mm=self._float(self.radius_var.get()),
            aperture_offset_mm=self._float(self.offset_var.get()),
            arc_tolerance_mm=self._float(self.tolerance_var.get()),
            sheet_width_mm=self._optional_float(self.width_var.get()),
            sheet_height_mm=self._optional_float(self.height_var.get()),
            mirror_x=self.mirror_x_var.get(),
            mirror_y=self.mirror_y_var.get(),
            rotate_deg=self._float(self.rotation_var.get()),
            center_z=self.center_z_var.get(),
            min_opening_area_mm2=self._float(self.minimum_area_var.get()),
        )

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    # ---------- Aperture library ----------

    def _load_aperture_library(self) -> None:
        library_path = Path(__file__).with_name("aperture_library.json")
        try:
            payload = json.loads(library_path.read_text(encoding="utf-8"))
            presets = payload.get("presets", [])
            if not isinstance(presets, list):
                raise ValueError("поле presets должно быть списком")
            for preset in presets:
                if isinstance(preset, dict) and str(preset.get("name", "")).strip():
                    self.library_presets[str(preset["name"])] = preset
        except Exception as exc:
            self._append_log(f"ПРЕДУПРЕЖДЕНИЕ: библиотека апертур не загружена: {exc}")

        names = list(self.library_presets)
        self.library_combo.configure(values=names)
        if names:
            self.library_preset_var.set(names[0])

    def _begin_library_placement(self) -> None:
        name = self.library_preset_var.get()
        preset = self.library_presets.get(name)
        if preset is None:
            messagebox.showerror("Ошибка", "Выберите библиотечную апертуру.")
            return
        try:
            rotation = self._float(self.library_rotation_var.get())
            # Validate the preset before entering placement mode.
            create_library_aperture(
                preset,
                rotation_deg=rotation,
                arc_tolerance_mm=max(self._float(self.tolerance_var.get()), 1e-6),
            )
        except (ValueError, StencilError) as exc:
            messagebox.showerror("Ошибка библиотечной апертуры", str(exc))
            return
        if self.view_center is None:
            messagebox.showinfo("Нет Gerber", "Сначала откройте Gerber-файл.")
            return
        self.pending_aperture_preset = preset
        self.canvas.configure(cursor="crosshair")
        self.preview_status_var.set("Режим установки: щёлкните центром апертуры; Esc/ПКМ — отмена.")
        self.canvas.focus_set()

    def _cancel_placement(self) -> None:
        if self.pending_aperture_preset is not None:
            self.pending_aperture_preset = None
            self.canvas.configure(cursor="")
            self._update_preview_status()

    def _place_pending_aperture(self, sx: float, sy: float) -> None:
        preset = self.pending_aperture_preset
        if preset is None or self.view_center is None:
            return
        try:
            rotation = self._float(self.library_rotation_var.get())
            x, y = self._screen_to_world(sx, sy)
            geometry = create_library_aperture(
                preset,
                center_x=x,
                center_y=y,
                rotation_deg=rotation,
                arc_tolerance_mm=max(self._float(self.tolerance_var.get()), 1e-6),
            )
        except (ValueError, StencilError) as exc:
            messagebox.showerror("Ошибка библиотечной апертуры", str(exc))
            return
        new_id = f"added:library:{uuid.uuid4().hex}"
        self.added_records[new_id] = geometry
        self.selected_ids = {new_id}
        self.pending_aperture_preset = None
        self.canvas.configure(cursor="")
        self._draw_preview()
        self._append_log(
            f"Добавлена библиотечная апертура «{preset.get('name', preset.get('shape', ''))}» "
            f"в X={x:.3f}, Y={y:.3f} мм"
        )

    # ---------- Preview loading, drawing and navigation ----------

    def _start_preview_load(self, input_path: Path) -> None:
        try:
            tolerance = self._float(self.tolerance_var.get())
        except ValueError:
            tolerance = 0.01
        self.preview_status_var.set("Чтение Gerber…")
        self.original_records.clear()
        self.added_records.clear()
        self.excluded_ids.clear()
        self.selected_ids.clear()
        self.view_bounds = None
        self.view_center = None
        self.view_is_fit = True
        self._draw_preview()

        def worker() -> None:
            try:
                geometry, primitive_count = load_gerber_image(
                    input_path,
                    arc_tolerance_mm=tolerance,
                )
                records = list_openings(geometry)
                self.events.put(("preview", (records, primitive_count)))
            except Exception as exc:
                self.events.put(("preview_error", exc))

        threading.Thread(target=worker, daemon=True).start()

    def _all_records(self) -> dict[str, object]:
        return {**self.original_records, **self.added_records}

    def _active_records(self) -> dict[str, object]:
        return {key: poly for key, poly in self._all_records().items() if key not in self.excluded_ids}

    def _calculate_record_bounds(self) -> tuple[float, float, float, float] | None:
        records = self._all_records()
        if not records:
            return None
        return (
            min(poly.bounds[0] for poly in records.values()),
            min(poly.bounds[1] for poly in records.values()),
            max(poly.bounds[2] for poly in records.values()),
            max(poly.bounds[3] for poly in records.values()),
        )

    def _calculate_fit_scale(self, bounds: tuple[float, float, float, float]) -> float:
        min_x, min_y, max_x, max_y = bounds
        width = max(max_x - min_x, 1e-9)
        height = max(max_y - min_y, 1e-9)
        canvas_w = max(self.canvas.winfo_width(), 100)
        canvas_h = max(self.canvas.winfo_height(), 100)
        padding = 28.0
        return max(1e-6, min((canvas_w - 2 * padding) / width, (canvas_h - 2 * padding) / height))

    def _fit_view(self) -> None:
        bounds = self._calculate_record_bounds()
        if bounds is None:
            return
        min_x, min_y, max_x, max_y = bounds
        self.view_bounds = bounds
        self.view_center = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
        self.fit_scale = self._calculate_fit_scale(bounds)
        self.view_scale = self.fit_scale
        self.view_is_fit = True
        self._draw_preview()

    def _canvas_configure(self, _event) -> None:
        if self.view_is_fit and self._all_records():
            self._fit_view()
        else:
            bounds = self._calculate_record_bounds()
            if bounds is not None:
                self.fit_scale = self._calculate_fit_scale(bounds)
            self._draw_preview()

    def _draw_preview(self) -> None:
        self.canvas.delete("all")
        self.screen_bboxes.clear()
        records = self._all_records()
        if not records:
            self.zoom_status_var.set("Масштаб: —")
            return

        bounds = self._calculate_record_bounds()
        assert bounds is not None
        self.view_bounds = bounds
        self.fit_scale = self._calculate_fit_scale(bounds)
        if self.view_center is None:
            min_x, min_y, max_x, max_y = bounds
            self.view_center = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
            self.view_scale = self.fit_scale
            self.view_is_fit = True

        canvas_w = max(self.canvas.winfo_width(), 100)
        canvas_h = max(self.canvas.winfo_height(), 100)
        visible_margin = 8.0

        for record_id, poly in records.items():
            min_x, min_y, max_x, max_y = poly.bounds
            sx0, sy1 = self._world_to_screen(min_x, min_y)
            sx1, sy0 = self._world_to_screen(max_x, max_y)
            bbox = (min(sx0, sx1), min(sy0, sy1), max(sx0, sx1), max(sy0, sy1))
            self.screen_bboxes[record_id] = bbox
            if (
                bbox[2] < -visible_margin
                or bbox[0] > canvas_w + visible_margin
                or bbox[3] < -visible_margin
                or bbox[1] > canvas_h + visible_margin
            ):
                continue

            exterior = list(poly.exterior.coords)
            points: list[float] = []
            for x, y in exterior:
                sx, sy = self._world_to_screen(x, y)
                points.extend((sx, sy))

            if record_id in self.excluded_ids:
                fill = "#555a61"
            elif record_id.startswith("added:"):
                fill = "#63c174"
            else:
                fill = "#62aee8"
            selected = record_id in self.selected_ids
            self.canvas.create_polygon(
                points,
                fill=fill,
                outline="#ffb347" if selected else "#d7e5ef",
                width=3 if selected else 1,
            )
            # Tk Canvas has no even-odd fill rule. Draw polygon holes back in the
            # canvas background so annular Gerber primitives remain legible.
            for interior in poly.interiors:
                hole_points: list[float] = []
                for x, y in interior.coords:
                    sx, sy = self._world_to_screen(x, y)
                    hole_points.extend((sx, sy))
                self.canvas.create_polygon(
                    hole_points,
                    fill=self.BACKGROUND,
                    outline="#ffb347" if selected else self.BACKGROUND,
                    width=1,
                )

        self._update_preview_status()

    def _world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        assert self.view_center is not None
        center_x, center_y = self.view_center
        canvas_w = max(self.canvas.winfo_width(), 100)
        canvas_h = max(self.canvas.winfo_height(), 100)
        return (
            canvas_w / 2.0 + (x - center_x) * self.view_scale,
            canvas_h / 2.0 - (y - center_y) * self.view_scale,
        )

    def _screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        assert self.view_center is not None
        center_x, center_y = self.view_center
        canvas_w = max(self.canvas.winfo_width(), 100)
        canvas_h = max(self.canvas.winfo_height(), 100)
        return (
            center_x + (sx - canvas_w / 2.0) / self.view_scale,
            center_y - (sy - canvas_h / 2.0) / self.view_scale,
        )

    def _zoom_button(self, factor: float) -> None:
        self._zoom_at(self.canvas.winfo_width() / 2.0, self.canvas.winfo_height() / 2.0, factor)

    def _zoom_at(self, sx: float, sy: float, factor: float) -> None:
        if self.view_center is None or not self._all_records():
            return
        world_x, world_y = self._screen_to_world(sx, sy)
        minimum = max(self.fit_scale * 0.05, 1e-6)
        maximum = max(self.fit_scale * 500.0, minimum * 2.0)
        new_scale = min(max(self.view_scale * factor, minimum), maximum)
        if math.isclose(new_scale, self.view_scale, rel_tol=1e-12):
            return
        canvas_w = max(self.canvas.winfo_width(), 100)
        canvas_h = max(self.canvas.winfo_height(), 100)
        center_x = world_x - (sx - canvas_w / 2.0) / new_scale
        center_y = world_y + (sy - canvas_h / 2.0) / new_scale
        self.view_center = (center_x, center_y)
        self.view_scale = new_scale
        self.view_is_fit = False
        self._draw_preview()

    def _canvas_mousewheel(self, event) -> str:
        factor = 1.25 if event.delta > 0 else 1 / 1.25
        self._zoom_at(event.x, event.y, factor)
        return "break"

    def _pan_press(self, event) -> None:
        if self.view_center is None:
            return
        self.pan_start_screen = (event.x, event.y)
        self.pan_start_center = self.view_center
        self.canvas.configure(cursor="fleur")

    def _pan_drag(self, event) -> None:
        if self.pan_start_screen is None or self.pan_start_center is None:
            return
        start_x, start_y = self.pan_start_screen
        center_x, center_y = self.pan_start_center
        self.view_center = (
            center_x - (event.x - start_x) / self.view_scale,
            center_y + (event.y - start_y) / self.view_scale,
        )
        self.view_is_fit = False
        self._draw_preview()

    def _pan_release(self, _event) -> None:
        self.pan_start_screen = None
        self.pan_start_center = None
        self.canvas.configure(cursor="crosshair" if self.pending_aperture_preset is not None else "")

    def _canvas_motion(self, event) -> None:
        if self.view_center is not None:
            self.cursor_world = self._screen_to_world(event.x, event.y)
            self._update_preview_status()

    def _canvas_leave(self, _event) -> None:
        self.cursor_world = None
        self._update_preview_status()

    def _update_preview_status(self) -> None:
        total = len(self.original_records)
        added = len(self.added_records)
        excluded = len(self.excluded_ids)
        selected = len(self.selected_ids)
        coordinates = ""
        if self.cursor_world is not None:
            coordinates = f"; X={self.cursor_world[0]:.3f}, Y={self.cursor_world[1]:.3f} мм"
        self.preview_status_var.set(
            f"Исходных: {total}; добавлено: {added}; исключено: {excluded}; "
            f"выбрано: {selected}{coordinates}"
        )
        if self.fit_scale > 0:
            percent = self.view_scale / self.fit_scale * 100.0
            self.zoom_status_var.set(f"{percent:.0f}% · {self.view_scale:.2f} px/мм")

    # ---------- Selection and aperture editing ----------

    def _canvas_press(self, event) -> None:
        self.canvas.focus_set()
        if self.pending_aperture_preset is not None:
            self._place_pending_aperture(event.x, event.y)
            return
        self.drag_start = (event.x, event.y)
        if self.selection_rect is not None:
            self.canvas.delete(self.selection_rect)
        self.selection_rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#ffb347", dash=(4, 3)
        )

    def _canvas_drag(self, event) -> None:
        if self.drag_start is None or self.selection_rect is None:
            return
        x0, y0 = self.drag_start
        self.canvas.coords(self.selection_rect, x0, y0, event.x, event.y)

    def _canvas_release(self, event) -> None:
        if self.drag_start is None:
            return
        x0, y0 = self.drag_start
        self.drag_start = None
        if self.selection_rect is not None:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

        additive = bool(event.state & 0x0001)  # Shift
        if not additive:
            self.selected_ids.clear()

        if abs(event.x - x0) < 5 and abs(event.y - y0) < 5:
            self._select_at_point(event.x, event.y, additive=True)
        else:
            left, right = sorted((x0, event.x))
            top, bottom = sorted((y0, event.y))
            for record_id, bbox in self.screen_bboxes.items():
                bx0, by0, bx1, by1 = bbox
                if bx1 >= left and bx0 <= right and by1 >= top and by0 <= bottom:
                    self.selected_ids.add(record_id)
        self._draw_preview()

    def _select_at_point(self, sx: float, sy: float, additive: bool) -> None:
        if self.view_center is None:
            return
        world_x, world_y = self._screen_to_world(sx, sy)
        point = Point(world_x, world_y)
        inside: list[tuple[float, str]] = []
        nearby: list[tuple[float, float, str]] = []
        tolerance_world = max(5.0 / self.view_scale, 1e-9)
        for record_id, poly in self._all_records().items():
            min_x, min_y, max_x, max_y = poly.bounds
            if (
                min_x - tolerance_world <= world_x <= max_x + tolerance_world
                and min_y - tolerance_world <= world_y <= max_y + tolerance_world
            ):
                if poly.contains(point) or poly.touches(point):
                    inside.append((poly.area, record_id))
                else:
                    distance = poly.distance(point)
                    if distance <= tolerance_world:
                        nearby.append((distance, poly.area, record_id))
        record_id: str | None = None
        if inside:
            _, record_id = min(inside)
        elif nearby:
            _, _, record_id = min(nearby)
        if record_id is not None:
            if record_id in self.selected_ids and additive:
                self.selected_ids.remove(record_id)
            else:
                self.selected_ids.add(record_id)

    def _select_all(self) -> None:
        self.selected_ids = set(self._all_records())
        self._draw_preview()

    def _toggle_excluded(self) -> None:
        if not self.selected_ids:
            messagebox.showinfo("Нет выбора", "Выберите одну или несколько апертур.")
            return
        for record_id in self.selected_ids:
            if record_id in self.excluded_ids:
                self.excluded_ids.remove(record_id)
            else:
                self.excluded_ids.add(record_id)
        self._draw_preview()

    def _duplicate_selected(self) -> None:
        if not self.selected_ids:
            messagebox.showinfo("Нет выбора", "Выберите апертуру-шаблон.")
            return
        try:
            dx = self._float(self.duplicate_dx_var.get())
            dy = self._float(self.duplicate_dy_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Смещения X и Y должны быть числами.")
            return
        if abs(dx) < 1e-12 and abs(dy) < 1e-12:
            messagebox.showerror("Ошибка", "Хотя бы одно смещение должно отличаться от нуля.")
            return

        records = self._all_records()
        new_ids: set[str] = set()
        for record_id in list(self.selected_ids):
            poly = records.get(record_id)
            if poly is None:
                continue
            new_id = f"added:duplicate:{uuid.uuid4().hex}"
            self.added_records[new_id] = affinity.translate(poly, xoff=dx, yoff=dy)
            new_ids.add(new_id)
        self.selected_ids = new_ids
        self._draw_preview()
        self._append_log(f"Добавлено копий: {len(new_ids)}; смещение X={dx:g} мм, Y={dy:g} мм")

    def _split_selected_grid(self) -> None:
        if not self.selected_ids:
            messagebox.showinfo("Нет выбора", "Выберите одну или несколько крупных апертур.")
            return
        try:
            cell_width = self._float(self.grid_cell_width_var.get())
            cell_height = self._float(self.grid_cell_height_var.get())
            web_x = self._float(self.grid_web_x_var.get())
            web_y = self._float(self.grid_web_y_var.get())
            rotation = self._float(self.grid_rotation_var.get())
            min_area = self._float(self.grid_min_area_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Параметры сетки должны быть числами.")
            return

        records = self._all_records()
        replacements: dict[str, list[object]] = {}
        try:
            for record_id in list(self.selected_ids):
                polygon = records.get(record_id)
                if polygon is None:
                    continue
                fragments = split_opening_grid(
                    polygon,
                    max_cell_width_mm=cell_width,
                    max_cell_height_mm=cell_height,
                    web_x_mm=web_x,
                    web_y_mm=web_y,
                    rotation_deg=rotation,
                    min_fragment_area_mm2=min_area,
                )
                if len(fragments) > 1:
                    replacements[record_id] = fragments
        except StencilError as exc:
            messagebox.showerror("Ошибка разбиения", str(exc))
            return

        if not replacements:
            messagebox.showinfo(
                "Разбиение не требуется",
                "При заданных размерах выбранные апертуры помещаются в одну ячейку.",
            )
            return

        new_ids: set[str] = set()
        fragment_count = 0
        for record_id, fragments in replacements.items():
            if record_id.startswith("added:"):
                self.added_records.pop(record_id, None)
                self.excluded_ids.discard(record_id)
            else:
                self.excluded_ids.add(record_id)
            for fragment in fragments:
                new_id = f"added:grid:{uuid.uuid4().hex}"
                self.added_records[new_id] = fragment
                new_ids.add(new_id)
                fragment_count += 1
        self.selected_ids = new_ids
        self._draw_preview()
        self._append_log(
            f"Сеткой заменено апертур: {len(replacements)}; создано окон: {fragment_count}; "
            f"ячейка ≤ {cell_width:g}×{cell_height:g} мм, перемычки {web_x:g}/{web_y:g} мм"
        )

    def _remove_selected_added(self) -> None:
        removable = [record_id for record_id in self.selected_ids if record_id.startswith("added:")]
        for record_id in removable:
            self.added_records.pop(record_id, None)
            self.excluded_ids.discard(record_id)
            self.selected_ids.discard(record_id)
        self._draw_preview()

    def _clear_edits(self) -> None:
        self.added_records.clear()
        self.excluded_ids.clear()
        self.selected_ids.clear()
        self._cancel_placement()
        self._fit_view()

    # ---------- STL conversion ----------

    def _start_conversion(self) -> None:
        try:
            input_path = Path(self.input_var.get())
            output_path = Path(self.output_var.get())
            options = self._build_options()
            options.validate()
            if not input_path.is_file():
                raise StencilError("Выберите существующий Gerber-файл.")
            if not output_path.name:
                raise StencilError("Укажите выходной STL-файл.")
        except (ValueError, StencilError) as exc:
            messagebox.showerror("Ошибка параметров", str(exc))
            return

        excluded_originals = {
            record_id for record_id in self.excluded_ids if not record_id.startswith("added:")
        }
        active_added = [
            poly for record_id, poly in self.added_records.items() if record_id not in self.excluded_ids
        ]

        self.convert_button.configure(state="disabled")
        self._append_log(f"Чтение: {input_path}")
        self._append_log(
            f"Правки: исключено исходных {len(excluded_originals)}, добавлено {len(active_added)}"
        )
        self._append_log("Сборка векторной геометрии и герметичного тела…")

        def worker() -> None:
            try:
                report = convert_gerber_to_stencil(
                    input_path,
                    output_path,
                    options,
                    preview_svg_path=output_path.with_suffix(".svg"),
                    report_path=output_path.with_suffix(".json"),
                    excluded_opening_keys=excluded_originals,
                    added_openings=active_added,
                )
                self.events.put(("success", report))
            except Exception as exc:
                self.events.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "preview_error":
                    self.preview_status_var.set(f"Ошибка предпросмотра: {payload}")
                    messagebox.showerror("Не удалось открыть Gerber", str(payload))
                elif event == "preview":
                    records, primitive_count = payload
                    self.original_records = {key: poly for key, poly in records}
                    self.added_records.clear()
                    self.excluded_ids.clear()
                    self.selected_ids.clear()
                    self.view_center = None
                    self.view_is_fit = True
                    self._fit_view()
                    self._append_log(
                        f"Gerber загружен: примитивов {primitive_count}, апертур/областей {len(records)}"
                    )
                elif event == "error":
                    self.convert_button.configure(state="normal")
                    self._append_log(f"ОШИБКА: {payload}")
                    messagebox.showerror("Преобразование не выполнено", str(payload))
                elif event == "success":
                    self.convert_button.configure(state="normal")
                    report = payload
                    self._append_log(
                        f"Готово: {report.sheet_width_mm:.3f} × "
                        f"{report.sheet_height_mm:.3f} × {report.thickness_mm:.3f} мм"
                    )
                    self._append_log(
                        f"Герметичность: {'ДА' if report.watertight else 'НЕТ'}, "
                        f"тел: {report.body_count}, отверстий: {report.opening_count}, "
                        f"добавлено: {report.added_opening_count}"
                    )
                    for warning in report.warnings:
                        self._append_log(f"ПРЕДУПРЕЖДЕНИЕ: {warning}")
                    messagebox.showinfo("Готово", f"STL сохранён:\n{report.output_file}")
        except queue.Empty:
            pass
        self.after(100, self._poll_events)


if __name__ == "__main__":
    StencilApp().mainloop()
