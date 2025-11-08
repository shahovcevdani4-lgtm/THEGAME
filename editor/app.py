"""Tkinter-based application for editing the game's data files."""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Callable

from editor.data_manager import GameDataManager


def _rgb_to_string(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return ", ".join(str(int(component)) for component in value)
    return str(value)


def _string_to_rgb(value: str) -> list[int] | None:
    stripped = value.strip()
    if not stripped:
        return None
    parts = [part.strip() for part in stripped.split(",")]
    if len(parts) != 3:
        raise ValueError("Ожидается три значения RGB, разделённых запятой")
    rgb = []
    for part in parts:
        component = int(part)
        if not 0 <= component <= 255:
            raise ValueError("Компоненты цвета должны быть в диапазоне 0..255")
        rgb.append(component)
    return rgb


def _string_to_list(value: str) -> list[str]:
    if not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _list_to_string(items: Any) -> str:
    if isinstance(items, (list, tuple)):
        return ", ".join(str(item) for item in items)
    return str(items)


def _ensure_relative(path: str) -> str:
    candidate = Path(path).expanduser()
    try:
        relative = candidate.relative_to(Path.cwd())
        return str(relative)
    except ValueError:
        return str(candidate)


class GameEditorApp(ttk.Frame):
    """Root widget combining all editing panels."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.manager = GameDataManager()
        self.pack(fill=tk.BOTH, expand=True)
        self._build_ui()

    def _build_ui(self) -> None:
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Button(control_frame, text="Перезагрузить", command=self.reload).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(control_frame, text="Сохранить", command=self.save).pack(
            side=tk.LEFT, padx=4
        )

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.creatures_editor = CreaturesEditor(notebook, self.manager)
        self.tiles_editor = TilesEditor(notebook, self.manager)
        self.items_editor = ItemsEditor(notebook, self.manager)

        notebook.add(self.creatures_editor, text="Существа")
        notebook.add(self.tiles_editor, text="Тайлы и структуры")
        notebook.add(self.items_editor, text="Предметы")

        self.refresh()

    def reload(self) -> None:
        if messagebox.askyesno("Подтвердите", "Отменить несохранённые изменения?"):
            self.manager.load()
            self.refresh()

    def save(self) -> None:
        try:
            self.creatures_editor.flush()
            self.tiles_editor.flush()
            self.items_editor.flush()
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self.manager.save()
        messagebox.showinfo("Готово", "Файлы данных успешно сохранены")

    def refresh(self) -> None:
        self.creatures_editor.refresh()
        self.tiles_editor.refresh()
        self.items_editor.refresh()


class CreaturesEditor(ttk.Frame):
    DATASETS = {
        "characters": {
            "label": "Мирные", "extra_fields": []
        },
        "enemies": {
            "label": "Враги",
            "extra_fields": [
                ("hp", "Здоровье"),
                ("attack_min", "Мин. атака"),
                ("attack_max", "Макс. атака"),
                ("reward_talents", "Награда"),
            ],
        },
    }

    def __init__(self, master: tk.Misc, manager: GameDataManager) -> None:
        super().__init__(master)
        self.manager = manager
        self.dataset_var = tk.StringVar(value="characters")
        self.current_key: str | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.BOTH, expand=True)

        dataset_frame = ttk.Frame(top)
        dataset_frame.pack(fill=tk.X, padx=4, pady=4)

        ttk.Label(dataset_frame, text="Тип существ:").pack(side=tk.LEFT)
        dataset_menu = ttk.OptionMenu(
            dataset_frame,
            self.dataset_var,
            self.dataset_var.get(),
            *[name for name in self.DATASETS],
            command=self._on_dataset_change,
        )
        dataset_menu.pack(side=tk.LEFT, padx=4)

        main = ttk.Frame(top)
        main.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(main)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)

        self.listbox = tk.Listbox(list_frame, width=28)
        self.listbox.pack(fill=tk.Y, expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_select())

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Добавить", command=self.add).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Клонировать", command=self.duplicate).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(btn_frame, text="Удалить", command=self.delete).pack(fill=tk.X)

        form = ttk.Frame(main)
        form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.char_var = tk.StringVar()
        self.tile_var = tk.StringVar()
        self.sprite_var = tk.StringVar()
        self.fg_var = tk.StringVar()
        self.bg_var = tk.StringVar()
        self.stat_vars = {
            "str": tk.StringVar(),
            "agi": tk.StringVar(),
            "int": tk.StringVar(),
        }
        self.extra_vars = {
            "hp": tk.StringVar(),
            "attack_min": tk.StringVar(),
            "attack_max": tk.StringVar(),
            "reward_talents": tk.StringVar(),
        }

        form_rows = (
            ("ID", self.id_var),
            ("Имя", self.name_var),
            ("Символ", self.char_var),
            ("Тайл", self.tile_var),
            ("Спрайт", self.sprite_var),
            ("Цвет FG", self.fg_var),
            ("Цвет BG", self.bg_var),
        )
        for idx, (label, var) in enumerate(form_rows):
            row = ttk.Frame(form)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label, width=15).pack(side=tk.LEFT)
            entry = ttk.Entry(row, textvariable=var)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            if label == "Спрайт":
                ttk.Button(row, text="Выбрать", command=self._choose_sprite).pack(
                    side=tk.LEFT, padx=4
                )

        stats_frame = ttk.LabelFrame(form, text="Характеристики")
        stats_frame.pack(fill=tk.X, pady=6)
        for key, label in (("str", "Сила"), ("agi", "Ловкость"), ("int", "Интеллект")):
            row = ttk.Frame(stats_frame)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label, width=15).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=self.stat_vars[key]).pack(
                side=tk.LEFT, fill=tk.X, expand=True
            )

        self.extra_frame = ttk.LabelFrame(form, text="Боевые параметры")
        self.extra_rows: dict[str, ttk.Entry] = {}
        for key, label in self.DATASETS["enemies"]["extra_fields"]:
            row = ttk.Frame(self.extra_frame)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label, width=15).pack(side=tk.LEFT)
            entry = ttk.Entry(row, textvariable=self.extra_vars[key])
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.extra_rows[key] = entry
        self.extra_frame.pack(fill=tk.X, pady=6)

        ttk.Button(form, text="Сохранить", command=self.save_current).pack(
            anchor=tk.E, pady=6
        )

    def _dataset_data(self) -> dict[str, Any]:
        dataset = self.dataset_var.get()
        section = self.manager.section(dataset)
        return section

    def _on_dataset_change(self, *_: object) -> None:
        dataset = self.dataset_var.get()
        self.extra_frame.pack_forget()
        if dataset == "enemies":
            self.extra_frame.pack(fill=tk.X, pady=6)
        self.refresh()

    def refresh(self) -> None:
        data = self._dataset_data()
        keys = sorted(data)
        self.listbox.delete(0, tk.END)
        for key in keys:
            creature = data[key]
            label = creature.get("name", key)
            self.listbox.insert(tk.END, f"{key} — {label}")
        self.current_key = None
        self._clear_form()

    def flush(self) -> None:
        if self.id_var.get().strip():
            key, data = self._collect_data()
            dataset = self._dataset_data()
            dataset[key] = data
            if self.current_key and self.current_key != key:
                dataset.pop(self.current_key, None)
            self.current_key = key

    def _clear_form(self) -> None:
        for var in (
            self.id_var,
            self.name_var,
            self.char_var,
            self.tile_var,
            self.sprite_var,
            self.fg_var,
            self.bg_var,
        ):
            var.set("")
        for var in self.stat_vars.values():
            var.set("")
        for var in self.extra_vars.values():
            var.set("")

    def _on_select(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        dataset = self._dataset_data()
        key = sorted(dataset)[selection[0]]
        self.current_key = key
        creature = dataset[key]
        self.id_var.set(key)
        self.name_var.set(creature.get("name", ""))
        self.char_var.set(creature.get("char", ""))
        self.tile_var.set(creature.get("tile", ""))
        self.sprite_var.set(creature.get("sprite", ""))
        self.fg_var.set(_rgb_to_string(creature.get("fg")))
        self.bg_var.set(_rgb_to_string(creature.get("bg")))
        stats = creature.get("stats", {})
        for key in self.stat_vars:
            self.stat_vars[key].set(str(stats.get(key, "")))
        for key in self.extra_vars:
            self.extra_vars[key].set(str(creature.get(key, "")))

    def _choose_sprite(self) -> None:
        filename = filedialog.askopenfilename(
            title="Выберите изображение", filetypes=[("Изображения", "*.png *.jpg *.jpeg *.gif"), ("Все файлы", "*.*")]
        )
        if filename:
            self.sprite_var.set(_ensure_relative(filename))

    def _collect_data(self) -> tuple[str, dict[str, Any]]:
        key = self.id_var.get().strip()
        if not key:
            raise ValueError("ID существа не может быть пустым")
        data: dict[str, Any] = {
            "name": self.name_var.get().strip() or key,
            "char": self.char_var.get()[:1] if self.char_var.get() else "",
            "tile": self.tile_var.get().strip(),
        }
        sprite = self.sprite_var.get().strip()
        if sprite:
            data["sprite"] = sprite
        fg = _string_to_rgb(self.fg_var.get())
        if fg is not None:
            data["fg"] = fg
        bg = _string_to_rgb(self.bg_var.get())
        if bg is not None:
            data["bg"] = bg
        stats: dict[str, int] = {}
        for field, var in self.stat_vars.items():
            text = var.get().strip()
            if text:
                stats[field] = int(text)
        if stats:
            data["stats"] = stats
        if self.dataset_var.get() == "enemies":
            for key, var in self.extra_vars.items():
                text = var.get().strip()
                if text:
                    data[key] = int(text)
        return key, data

    def save_current(self) -> None:
        try:
            key, data = self._collect_data()
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        dataset = self._dataset_data()
        dataset[key] = data
        if self.current_key and self.current_key != key:
            dataset.pop(self.current_key, None)
        self.current_key = key
        self.refresh()
        self._select_key(key)

    def _select_key(self, key: str) -> None:
        keys = sorted(self._dataset_data())
        try:
            index = keys.index(key)
        except ValueError:
            return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self._on_select()

    def add(self) -> None:
        dataset = self.dataset_var.get()
        key = simpledialog.askstring("Новый ID", "Введите уникальный идентификатор:")
        if not key:
            return
        data_section = self._dataset_data()
        if key in data_section:
            messagebox.showerror("Ошибка", "Такой ID уже существует")
            return
        data_section[key] = {
            "name": key.upper(),
            "char": "?",
            "fg": [255, 255, 255],
            "bg": [0, 0, 0],
            "stats": {"str": 1, "agi": 1, "int": 1},
        }
        self.refresh()
        self._select_key(key)

    def duplicate(self) -> None:
        if not self.current_key:
            return
        dataset = self._dataset_data()
        base = dataset[self.current_key]
        new_key = simpledialog.askstring("Клонировать", "Новый ID для копии:")
        if not new_key:
            return
        if new_key in dataset:
            messagebox.showerror("Ошибка", "Такой ID уже существует")
            return
        dataset[new_key] = json.loads(json.dumps(base))
        self.refresh()
        self._select_key(new_key)

    def delete(self) -> None:
        if not self.current_key:
            return
        dataset = self._dataset_data()
        if messagebox.askyesno("Удаление", "Удалить выбранного персонажа?"):
            dataset.pop(self.current_key, None)
            self.current_key = None
            self.refresh()


class TileForm(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, title: str, on_save: Callable[[dict[str, Any]], None]) -> None:
        super().__init__(master, text=title)
        self.on_save = on_save
        self.key_var = tk.StringVar()
        self.char_var = tk.StringVar()
        self.walkable_var = tk.BooleanVar()
        self.tile_id_var = tk.StringVar()
        self.sprite_var = tk.StringVar()
        self.fg_var = tk.StringVar()
        self.bg_var = tk.StringVar()
        self._build()

    def _build(self) -> None:
        fields = (
            ("ID", self.key_var),
            ("Символ", self.char_var),
            ("Tile ID", self.tile_id_var),
        )
        for label, var in fields:
            row = ttk.Frame(self)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label, width=15).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        walk_row = ttk.Frame(self)
        walk_row.pack(fill=tk.X, pady=1)
        ttk.Label(walk_row, text="Проходимый", width=15).pack(side=tk.LEFT)
        ttk.Checkbutton(walk_row, variable=self.walkable_var).pack(side=tk.LEFT)

        for label, var in (("FG", self.fg_var), ("BG", self.bg_var)):
            row = ttk.Frame(self)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=f"Цвет {label}", width=15).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        sprite_row = ttk.Frame(self)
        sprite_row.pack(fill=tk.X, pady=1)
        ttk.Label(sprite_row, text="Спрайт", width=15).pack(side=tk.LEFT)
        ttk.Entry(sprite_row, textvariable=self.sprite_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(sprite_row, text="Выбрать", command=self._choose_sprite).pack(
            side=tk.LEFT, padx=4
        )

        ttk.Button(self, text="Сохранить плитку", command=self._save).pack(
            anchor=tk.E, pady=4
        )

    def load(self, key: str, data: Mapping[str, Any]) -> None:
        self.key_var.set(key)
        self.char_var.set(data.get("char", ""))
        self.walkable_var.set(bool(data.get("walkable", False)))
        self.tile_id_var.set(data.get("tile_id", ""))
        self.sprite_var.set(data.get("sprite", ""))
        self.fg_var.set(_rgb_to_string(data.get("fg")))
        self.bg_var.set(_rgb_to_string(data.get("bg")))

    def clear(self) -> None:
        self.key_var.set("")
        self.char_var.set("")
        self.walkable_var.set(False)
        self.tile_id_var.set("")
        self.sprite_var.set("")
        self.fg_var.set("")
        self.bg_var.set("")

    def _choose_sprite(self) -> None:
        filename = filedialog.askopenfilename(
            title="Выберите изображение", filetypes=[("Изображения", "*.png *.jpg *.jpeg *.gif"), ("Все файлы", "*.*")]
        )
        if filename:
            self.sprite_var.set(_ensure_relative(filename))

    def _save(self) -> None:
        key = self.key_var.get().strip()
        if not key:
            messagebox.showerror("Ошибка", "ID плитки не может быть пустым")
            return
        try:
            fg = _string_to_rgb(self.fg_var.get())
            bg = _string_to_rgb(self.bg_var.get())
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        tile: dict[str, Any] = {
            "char": self.char_var.get()[:1] if self.char_var.get() else "",
            "walkable": bool(self.walkable_var.get()),
            "tile_id": self.tile_id_var.get().strip() or key,
        }
        if fg is not None:
            tile["fg"] = fg
        if bg is not None:
            tile["bg"] = bg
        sprite = self.sprite_var.get().strip()
        if sprite:
            tile["sprite"] = sprite
        self.on_save({"key": key, "tile": tile})


class TileCollectionEditor(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str, get_collection: Callable[[], dict[str, Any]]) -> None:
        super().__init__(master)
        self.get_collection = get_collection
        ttk.Label(self, text=title, font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(body, width=25)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 6))
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_select())

        button_frame = ttk.Frame(body)
        button_frame.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(button_frame, text="Добавить", command=self.add).pack(fill=tk.X)
        ttk.Button(button_frame, text="Клонировать", command=self.duplicate).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(button_frame, text="Удалить", command=self.delete).pack(fill=tk.X)

        self.form = TileForm(body, "Параметры плитки", self._save_tile)
        self.form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        self.current_key: str | None = None

    def refresh(self) -> None:
        collection = self.get_collection()
        keys = sorted(collection)
        self.listbox.delete(0, tk.END)
        for key in keys:
            tile = collection[key]
            label = tile.get("char", "?") or "?"
            self.listbox.insert(tk.END, f"{key} ({label})")
        self.current_key = None
        self.form.clear()

    def _collection(self) -> dict[str, Any]:
        return self.get_collection()

    def _on_select(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        keys = sorted(self._collection())
        key = keys[selection[0]]
        self.current_key = key
        self.form.load(key, self._collection()[key])

    def add(self) -> None:
        key = simpledialog.askstring("Новая плитка", "Введите ID плитки:")
        if not key:
            return
        collection = self._collection()
        if key in collection:
            messagebox.showerror("Ошибка", "Такая плитка уже существует")
            return
        collection[key] = {
            "char": "?",
            "walkable": True,
            "fg": [255, 255, 255],
            "bg": [0, 0, 0],
            "tile_id": key,
        }
        self.refresh()
        self._select_key(key)

    def duplicate(self) -> None:
        if not self.current_key:
            return
        collection = self._collection()
        base = collection[self.current_key]
        new_key = simpledialog.askstring("Клонировать", "ID новой плитки:")
        if not new_key:
            return
        if new_key in collection:
            messagebox.showerror("Ошибка", "Такая плитка уже существует")
            return
        collection[new_key] = json.loads(json.dumps(base))
        self.refresh()
        self._select_key(new_key)

    def delete(self) -> None:
        if not self.current_key:
            return
        collection = self._collection()
        if messagebox.askyesno("Удаление", "Удалить выбранную плитку?"):
            collection.pop(self.current_key, None)
            self.current_key = None
            self.refresh()

    def _select_key(self, key: str) -> None:
        keys = sorted(self._collection())
        try:
            index = keys.index(key)
        except ValueError:
            return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self._on_select()

    def _save_tile(self, payload: dict[str, Any]) -> None:
        key = payload["key"]
        tile = payload["tile"]
        collection = self._collection()
        if self.current_key and self.current_key != key:
            collection.pop(self.current_key, None)
        collection[key] = tile
        self.current_key = key
        self.refresh()
        self._select_key(key)


class ScatterRuleEditor(ttk.Frame):
    def __init__(self, master: tk.Misc, get_rules: Callable[[], list[dict[str, Any]]]) -> None:
        super().__init__(master)
        self.get_rules = get_rules
        self.listbox = tk.Listbox(self, width=30)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_select())

        control = ttk.Frame(self)
        control.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(control, text="Добавить", command=self.add).pack(fill=tk.X)
        ttk.Button(control, text="Удалить", command=self.delete).pack(fill=tk.X, pady=2)

        form = ttk.Frame(self)
        form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tile_var = tk.StringVar()
        self.min_var = tk.StringVar()
        self.max_var = tk.StringVar()
        self.border_var = tk.BooleanVar(value=True)

        for label, var in (("Тайл", self.tile_var), ("Мин", self.min_var), ("Макс", self.max_var)):
            row = ttk.Frame(form)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label, width=10).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        border_row = ttk.Frame(form)
        border_row.pack(fill=tk.X, pady=1)
        ttk.Label(border_row, text="Избегать края", width=10).pack(side=tk.LEFT)
        ttk.Checkbutton(border_row, variable=self.border_var).pack(side=tk.LEFT)

        ttk.Button(form, text="Сохранить правило", command=self.save_rule).pack(
            anchor=tk.E, pady=4
        )

        self.current_index: int | None = None

    def refresh(self) -> None:
        rules = self.get_rules()
        self.listbox.delete(0, tk.END)
        for idx, rule in enumerate(rules):
            tile = rule.get("tile", "?")
            count_range = rule.get("count_range", [0, 0])
            self.listbox.insert(tk.END, f"{idx + 1}. {tile} ({count_range})")
        self.current_index = None
        self.tile_var.set("")
        self.min_var.set("")
        self.max_var.set("")
        self.border_var.set(True)

    def _rules(self) -> list[dict[str, Any]]:
        return self.get_rules()

    def _on_select(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        self.current_index = index
        rule = self._rules()[index]
        self.tile_var.set(rule.get("tile", ""))
        count_range = rule.get("count_range", [0, 0])
        if isinstance(count_range, (list, tuple)):
            self.min_var.set(str(count_range[0]))
            if len(count_range) > 1:
                self.max_var.set(str(count_range[1]))
        self.border_var.set(bool(rule.get("avoid_border", True)))

    def add(self) -> None:
        self._rules().append({"tile": "", "count_range": [1, 1], "avoid_border": True})
        self.refresh()

    def delete(self) -> None:
        if self.current_index is None:
            return
        rules = self._rules()
        if 0 <= self.current_index < len(rules):
            rules.pop(self.current_index)
        self.current_index = None
        self.refresh()

    def save_rule(self) -> None:
        if self.current_index is None:
            messagebox.showerror("Ошибка", "Выберите правило для сохранения")
            return
        try:
            min_value = int(self.min_var.get())
            max_value = int(self.max_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Мин/макс должны быть числами")
            return
        if min_value > max_value:
            messagebox.showerror("Ошибка", "Мин не может быть больше макс")
            return
        rule = {
            "tile": self.tile_var.get().strip(),
            "count_range": [min_value, max_value],
            "avoid_border": bool(self.border_var.get()),
        }
        self._rules()[self.current_index] = rule
        self.refresh()
        self.listbox.selection_set(self.current_index)
        self._on_select()


class StructuresEditor(ttk.Frame):
    def __init__(self, master: tk.Misc, manager: GameDataManager) -> None:
        super().__init__(master)
        self.manager = manager
        self.current_key: str | None = None
        self._build()

    def _structures(self) -> dict[str, Any]:
        return self.manager.section("structures")

    def _build(self) -> None:
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(body, width=30)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_select())

        control = ttk.Frame(body)
        control.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(control, text="Добавить", command=self.add).pack(fill=tk.X)
        ttk.Button(control, text="Удалить", command=self.delete).pack(fill=tk.X, pady=2)

        form = ttk.Frame(body)
        form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.radius_min_var = tk.StringVar()
        self.radius_max_var = tk.StringVar()
        self.density_var = tk.StringVar()
        self.tiles_var = tk.StringVar()

        fields = (
            ("ID", self.id_var),
            ("Название", self.name_var),
            ("Описание", self.desc_var),
            ("Радиус мин", self.radius_min_var),
            ("Радиус макс", self.radius_max_var),
            ("Плотность", self.density_var),
            ("Тайлы", self.tiles_var),
        )
        for label, var in fields:
            row = ttk.Frame(form)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label, width=15).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(form, text="Сохранить", command=self.save).pack(anchor=tk.E, pady=4)

    def refresh(self) -> None:
        structures = self._structures()
        self.listbox.delete(0, tk.END)
        for key, struct in sorted(structures.items()):
            label = struct.get("description", "")
            self.listbox.insert(tk.END, f"{key} — {label}")
        self.current_key = None
        self._clear()

    def flush(self) -> None:
        if not self.id_var.get().strip() and not self.current_key:
            return
        key = self.id_var.get().strip() or (self.current_key or "")
        if not key:
            raise ValueError("ID структуры не может быть пустым")
        try:
            radius_min = int(self.radius_min_var.get())
            radius_max = int(self.radius_max_var.get())
            density = float(self.density_var.get())
        except ValueError as exc:
            raise ValueError("Проверьте числовые поля структуры") from exc
        struct = {
            "name": self.name_var.get().strip() or key,
            "description": self.desc_var.get().strip(),
            "radius_range": [radius_min, radius_max],
            "density": density,
            "tiles": _string_to_list(self.tiles_var.get()),
        }
        structures = self._structures()
        if self.current_key and self.current_key != key:
            structures.pop(self.current_key, None)
        structures[key] = struct
        self.current_key = key

    def _clear(self) -> None:
        for var in (
            self.id_var,
            self.name_var,
            self.desc_var,
            self.radius_min_var,
            self.radius_max_var,
            self.density_var,
            self.tiles_var,
        ):
            var.set("")

    def _on_select(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        key = sorted(self._structures())[selection[0]]
        self.current_key = key
        struct = self._structures()[key]
        self.id_var.set(key)
        self.name_var.set(struct.get("name", ""))
        self.desc_var.set(struct.get("description", ""))
        radius = struct.get("radius_range", [0, 0])
        if isinstance(radius, (list, tuple)):
            self.radius_min_var.set(str(radius[0]))
            if len(radius) > 1:
                self.radius_max_var.set(str(radius[1]))
        self.density_var.set(str(struct.get("density", "")))
        self.tiles_var.set(_list_to_string(struct.get("tiles", [])))

    def add(self) -> None:
        key = simpledialog.askstring("Новая структура", "ID структуры:")
        if not key:
            return
        structures = self._structures()
        if key in structures:
            messagebox.showerror("Ошибка", "Такая структура уже существует")
            return
        structures[key] = {
            "description": "Новая структура",
            "radius_range": [1, 2],
            "density": 0.5,
            "tiles": [],
        }
        self.refresh()
        self._select(key)

    def _select(self, key: str) -> None:
        keys = sorted(self._structures())
        try:
            index = keys.index(key)
        except ValueError:
            return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self._on_select()

    def delete(self) -> None:
        if not self.current_key:
            return
        if messagebox.askyesno("Удаление", "Удалить структуру?"):
            self._structures().pop(self.current_key, None)
            self.current_key = None
            self.refresh()

    def save(self) -> None:
        try:
            self.flush()
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        key = self.current_key
        self.refresh()
        if key:
            self._select(key)


class BiomesEditor(ttk.Frame):
    def __init__(self, master: tk.Misc, manager: GameDataManager) -> None:
        super().__init__(master)
        self.manager = manager
        self.current_key: str | None = None
        self._build()

    def _biomes(self) -> dict[str, Any]:
        tiles_section = self.manager.section("tiles")
        biomes = tiles_section.setdefault("biomes", {})
        if not isinstance(biomes, dict):
            raise TypeError("Раздел biomes должен быть словарём")
        return biomes

    def _build(self) -> None:
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(body, width=30)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_select())

        control = ttk.Frame(body)
        control.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(control, text="Добавить", command=self.add).pack(fill=tk.X)
        ttk.Button(control, text="Клонировать", command=self.duplicate).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(control, text="Удалить", command=self.delete).pack(fill=tk.X)

        right = ttk.Frame(body)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.name_var = tk.StringVar()
        self.ground_var = tk.StringVar()
        self.forest_tiles_var = tk.StringVar()
        self.forest_min_var = tk.StringVar()
        self.forest_max_var = tk.StringVar()
        self.radius_min_var = tk.StringVar()
        self.radius_max_var = tk.StringVar()
        self.density_var = tk.StringVar()

        basic = ttk.LabelFrame(right, text="Основные настройки")
        basic.pack(fill=tk.X, pady=4)
        for label, var in (
            ("Название", self.name_var),
            ("Базовый тайл", self.ground_var),
            ("Лесные тайлы", self.forest_tiles_var),
        ):
            row = ttk.Frame(basic)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label, width=18).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        pairs = ttk.Frame(basic)
        pairs.pack(fill=tk.X, pady=2)
        ttk.Label(pairs, text="Лесов (мин/макс)", width=18).grid(row=0, column=0)
        ttk.Entry(pairs, textvariable=self.forest_min_var, width=8).grid(
            row=0, column=1, padx=2
        )
        ttk.Entry(pairs, textvariable=self.forest_max_var, width=8).grid(
            row=0, column=2, padx=2
        )
        ttk.Label(pairs, text="Радиус (мин/макс)", width=18).grid(row=1, column=0)
        ttk.Entry(pairs, textvariable=self.radius_min_var, width=8).grid(
            row=1, column=1, padx=2
        )
        ttk.Entry(pairs, textvariable=self.radius_max_var, width=8).grid(
            row=1, column=2, padx=2
        )

        density_row = ttk.Frame(basic)
        density_row.pack(fill=tk.X, pady=1)
        ttk.Label(density_row, text="Плотность леса", width=18).pack(side=tk.LEFT)
        ttk.Entry(density_row, textvariable=self.density_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        notebooks = ttk.Notebook(right)
        notebooks.pack(fill=tk.BOTH, expand=True, pady=4)

        self.unique_editor = TileCollectionEditor(
            notebooks, "Уникальные плитки", lambda: self._current_collection("unique_tiles")
        )
        notebooks.add(self.unique_editor, text="Уникальные плитки")

        self.extras_editor = TileCollectionEditor(
            notebooks, "Дополнительные плитки", lambda: self._current_collection("extras")
        )
        notebooks.add(self.extras_editor, text="Дополнения")

        self.scatter_editor = ScatterRuleEditor(
            notebooks, lambda: self._current_rules()
        )
        notebooks.add(self.scatter_editor, text="Рассеивание")

        ttk.Button(right, text="Сохранить биом", command=self.save).pack(anchor=tk.E, pady=4)

    def _current_biome(self) -> dict[str, Any]:
        if not self.current_key:
            raise ValueError("Сначала выберите биом")
        return self._biomes()[self.current_key]

    def _current_collection(self, key: str) -> dict[str, Any]:
        if not self.current_key:
            return {}
        biome = self._biomes().setdefault(self.current_key, {})
        collection = biome.setdefault(key, {})
        if not isinstance(collection, dict):
            biome[key] = {}
            collection = biome[key]
        return collection  # type: ignore[return-value]

    def _current_rules(self) -> list[dict[str, Any]]:
        if not self.current_key:
            return []
        biome = self._biomes().setdefault(self.current_key, {})
        rules = biome.setdefault("scatter_rules", [])
        if not isinstance(rules, list):
            biome["scatter_rules"] = []
            rules = biome["scatter_rules"]
        return rules  # type: ignore[return-value]

    def refresh(self) -> None:
        biomes = self._biomes()
        self.listbox.delete(0, tk.END)
        for key in sorted(biomes):
            entry = biomes[key]
            label = entry.get("ground_tile", "")
            self.listbox.insert(tk.END, f"{key} — {label}")
        self.current_key = None
        self._clear()
        self.unique_editor.refresh()
        self.extras_editor.refresh()
        self.scatter_editor.refresh()

    def _clear(self) -> None:
        for var in (
            self.name_var,
            self.ground_var,
            self.forest_tiles_var,
            self.forest_min_var,
            self.forest_max_var,
            self.radius_min_var,
            self.radius_max_var,
            self.density_var,
        ):
            var.set("")

    def _on_select(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        key = sorted(self._biomes())[selection[0]]
        self.current_key = key
        biome = self._biomes()[key]
        self.name_var.set(key)
        self.ground_var.set(biome.get("ground_tile", ""))
        self.forest_tiles_var.set(_list_to_string(biome.get("forest_tiles", [])))
        forest_count = biome.get("forest_count", [0, 0])
        if isinstance(forest_count, (list, tuple)):
            self.forest_min_var.set(str(forest_count[0]))
            if len(forest_count) > 1:
                self.forest_max_var.set(str(forest_count[1]))
        forest_radius = biome.get("forest_radius", [0, 0])
        if isinstance(forest_radius, (list, tuple)):
            self.radius_min_var.set(str(forest_radius[0]))
            if len(forest_radius) > 1:
                self.radius_max_var.set(str(forest_radius[1]))
        self.density_var.set(str(biome.get("forest_density", "")))
        self.unique_editor.refresh()
        self.extras_editor.refresh()
        self.scatter_editor.refresh()

    def add(self) -> None:
        key = simpledialog.askstring("Новый биом", "Введите ID биома:")
        if not key:
            return
        biomes = self._biomes()
        if key in biomes:
            messagebox.showerror("Ошибка", "Такой биом уже существует")
            return
        biomes[key] = {
            "ground_tile": "ground",
            "unique_tiles": {},
            "forest_tiles": [],
            "forest_count": [1, 3],
            "forest_radius": [1, 2],
            "forest_density": 0.5,
            "scatter_rules": [],
        }
        self.refresh()
        self._select(key)

    def flush(self) -> None:
        if not self.current_key and not self.name_var.get().strip():
            return
        if not self.current_key:
            raise ValueError("Выберите биом для сохранения")
        key = self.name_var.get().strip() or self.current_key
        try:
            forest_min = int(self.forest_min_var.get())
            forest_max = int(self.forest_max_var.get())
            radius_min = int(self.radius_min_var.get())
            radius_max = int(self.radius_max_var.get())
            density = float(self.density_var.get())
        except ValueError as exc:
            raise ValueError("Проверьте числовые поля") from exc
        biome = self._biomes()[self.current_key]
        biome.update(
            {
                "ground_tile": self.ground_var.get().strip(),
                "forest_tiles": _string_to_list(self.forest_tiles_var.get()),
                "forest_count": [forest_min, forest_max],
                "forest_radius": [radius_min, radius_max],
                "forest_density": density,
            }
        )
        if self.current_key != key:
            self._biomes()[key] = biome
            self._biomes().pop(self.current_key, None)
            self.current_key = key
        else:
            self.current_key = key

    def _select(self, key: str) -> None:
        keys = sorted(self._biomes())
        try:
            index = keys.index(key)
        except ValueError:
            return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self._on_select()

    def duplicate(self) -> None:
        if not self.current_key:
            return
        new_key = simpledialog.askstring("Клонировать биом", "ID нового биома:")
        if not new_key:
            return
        biomes = self._biomes()
        if new_key in biomes:
            messagebox.showerror("Ошибка", "Такой биом уже существует")
            return
        biomes[new_key] = json.loads(json.dumps(biomes[self.current_key]))
        self.refresh()
        self._select(new_key)

    def delete(self) -> None:
        if not self.current_key:
            return
        if messagebox.askyesno("Удаление", "Удалить биом?"):
            self._biomes().pop(self.current_key, None)
            self.current_key = None
            self.refresh()

    def save(self) -> None:
        try:
            self.flush()
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        key = self.current_key
        self.refresh()
        if key:
            self._select(key)


class CommonTilesEditor(ttk.Frame):
    def __init__(self, master: tk.Misc, manager: GameDataManager) -> None:
        super().__init__(master)
        self.manager = manager
        self.collection = TileCollectionEditor(
            self, "Общие плитки", lambda: self._tiles_section().setdefault("common_tiles", {})
        )
        self.collection.pack(fill=tk.BOTH, expand=True)

    def _tiles_section(self) -> dict[str, Any]:
        return self.manager.section("tiles")

    def refresh(self) -> None:
        self.collection.refresh()

    def flush(self) -> None:
        pass


class TilesEditor(ttk.Frame):
    def __init__(self, master: tk.Misc, manager: GameDataManager) -> None:
        super().__init__(master)
        self.manager = manager
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.common_editor = CommonTilesEditor(self.notebook, manager)
        self.biomes_editor = BiomesEditor(self.notebook, manager)
        self.structures_editor = StructuresEditor(self.notebook, manager)

        self.notebook.add(self.common_editor, text="Общие плитки")
        self.notebook.add(self.biomes_editor, text="Биомы")
        self.notebook.add(self.structures_editor, text="Структуры")

    def refresh(self) -> None:
        self.common_editor.refresh()
        self.biomes_editor.refresh()
        self.structures_editor.refresh()

    def flush(self) -> None:
        self.common_editor.flush()
        self.biomes_editor.flush()
        self.structures_editor.flush()


class ItemsEditor(ttk.Frame):
    def __init__(self, master: tk.Misc, manager: GameDataManager) -> None:
        super().__init__(master)
        self.manager = manager
        self.current_key: str | None = None
        self._build()

    def _items(self) -> dict[str, Any]:
        return self.manager.section("items")

    def _build(self) -> None:
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(body, width=28)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_select())

        control = ttk.Frame(body)
        control.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(control, text="Добавить", command=self.add).pack(fill=tk.X)
        ttk.Button(control, text="Клонировать", command=self.duplicate).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(control, text="Удалить", command=self.delete).pack(fill=tk.X)

        form = ttk.Frame(body)
        form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.icon_var = tk.StringVar()
        self.slot_var = tk.StringVar()
        self.two_handed_var = tk.BooleanVar()
        self.sprite_var = tk.StringVar()

        for label, var in (
            ("ID", self.id_var),
            ("Название", self.name_var),
            ("Иконка", self.icon_var),
            ("Слот", self.slot_var),
            ("Спрайт", self.sprite_var),
        ):
            row = ttk.Frame(form)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label, width=15).pack(side=tk.LEFT)
            entry = ttk.Entry(row, textvariable=var)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            if label == "Спрайт":
                ttk.Button(row, text="Выбрать", command=self._choose_sprite).pack(
                    side=tk.LEFT, padx=4
                )

        two_row = ttk.Frame(form)
        two_row.pack(fill=tk.X, pady=1)
        ttk.Label(two_row, text="Двуручный", width=15).pack(side=tk.LEFT)
        ttk.Checkbutton(two_row, variable=self.two_handed_var).pack(side=tk.LEFT)

        ttk.Button(form, text="Сохранить", command=self.save).pack(anchor=tk.E, pady=4)

    def refresh(self) -> None:
        items = self._items()
        self.listbox.delete(0, tk.END)
        for key, item in sorted(items.items()):
            label = item.get("name", "")
            self.listbox.insert(tk.END, f"{key} — {label}")
        self.current_key = None
        self._clear()

    def flush(self) -> None:
        if self.id_var.get().strip():
            key = self.id_var.get().strip()
            item = {
                "name": self.name_var.get().strip() or key,
                "icon": self.icon_var.get()[:1] if self.icon_var.get() else "",
                "slot_type": self.slot_var.get().strip(),
                "two_handed": bool(self.two_handed_var.get()),
            }
            sprite = self.sprite_var.get().strip()
            if sprite:
                item["sprite"] = sprite
            items = self._items()
            if self.current_key and self.current_key != key:
                items.pop(self.current_key, None)
            items[key] = item
            self.current_key = key

    def _clear(self) -> None:
        for var in (
            self.id_var,
            self.name_var,
            self.icon_var,
            self.slot_var,
            self.sprite_var,
        ):
            var.set("")
        self.two_handed_var.set(False)

    def _on_select(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        key = sorted(self._items())[selection[0]]
        self.current_key = key
        item = self._items()[key]
        self.id_var.set(key)
        self.name_var.set(item.get("name", ""))
        self.icon_var.set(item.get("icon", ""))
        self.slot_var.set(item.get("slot_type", ""))
        self.two_handed_var.set(bool(item.get("two_handed", False)))
        self.sprite_var.set(item.get("sprite", ""))

    def _choose_sprite(self) -> None:
        filename = filedialog.askopenfilename(
            title="Выберите изображение", filetypes=[("Изображения", "*.png *.jpg *.jpeg *.gif"), ("Все файлы", "*.*")]
        )
        if filename:
            self.sprite_var.set(_ensure_relative(filename))

    def add(self) -> None:
        key = simpledialog.askstring("Новый предмет", "ID предмета:")
        if not key:
            return
        items = self._items()
        if key in items:
            messagebox.showerror("Ошибка", "Такой ID уже существует")
            return
        items[key] = {
            "name": key.title(),
            "icon": "?",
            "slot_type": "upper",
            "two_handed": False,
        }
        self.refresh()
        self._select(key)

    def _select(self, key: str) -> None:
        keys = sorted(self._items())
        try:
            index = keys.index(key)
        except ValueError:
            return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self._on_select()

    def duplicate(self) -> None:
        if not self.current_key:
            return
        new_key = simpledialog.askstring("Клонировать", "Новый ID предмета:")
        if not new_key:
            return
        items = self._items()
        if new_key in items:
            messagebox.showerror("Ошибка", "Такой ID уже существует")
            return
        items[new_key] = json.loads(json.dumps(items[self.current_key]))
        self.refresh()
        self._select(new_key)

    def delete(self) -> None:
        if not self.current_key:
            return
        if messagebox.askyesno("Удаление", "Удалить предмет?"):
            self._items().pop(self.current_key, None)
            self.current_key = None
            self.refresh()

    def save(self) -> None:
        key = self.id_var.get().strip()
        if not key:
            messagebox.showerror("Ошибка", "ID не может быть пустым")
            return
        item = {
            "name": self.name_var.get().strip() or key,
            "icon": self.icon_var.get()[:1] if self.icon_var.get() else "",
            "slot_type": self.slot_var.get().strip(),
            "two_handed": bool(self.two_handed_var.get()),
        }
        sprite = self.sprite_var.get().strip()
        if sprite:
            item["sprite"] = sprite
        items = self._items()
        if self.current_key and self.current_key != key:
            items.pop(self.current_key, None)
        items[key] = item
        self.current_key = key
        self.refresh()
        self._select(key)


def run() -> None:
    root = tk.Tk()
    root.title("Редактор данных THEGAME")
    root.geometry("1100x700")
    app = GameEditorApp(root)
    app.mainloop()


if __name__ == "__main__":
    run()
