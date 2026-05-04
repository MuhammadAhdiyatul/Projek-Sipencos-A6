import json
import os
from datetime import datetime

import customtkinter as ctk

from ui_components import KosCard

PRIMARY_COLOR = "#002B49"
ACCENT_COLOR = "#C96A28"
APP_BG = "#F0F2F5"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E7EAF0"
TEXT_SUBTLE = "#6F7C85"


class FavoritesManager:
    def __init__(self, filepath=None):
        self.filepath = filepath or os.path.join(os.path.dirname(__file__), "favorites.json")
        self.favorites = self.load_favorites()

    def _normalize_item_id(self, kos_item):
        nama = str(kos_item.get("nama_kos", "") or "").strip().lower()
        alamat = str(kos_item.get("alamat", "") or "").strip().lower()
        return nama, alamat

    def _sort_favorites(self, data):
        return sorted(
            data,
            key=lambda item: str(item.get("added_at", "1970-01-01T00:00:00Z")),
            reverse=True,
        )

    def load_favorites(self):
        if not os.path.exists(self.filepath):
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as handle:
                data = json.load(handle)

            if not isinstance(data, list):
                return []

            return self._sort_favorites(data)
        except (json.JSONDecodeError, ValueError, OSError):
            return []

    def save_favorites(self, data):
        safe_data = list(data)
        temp_path = f"{self.filepath}.tmp"

        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(safe_data, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.filepath)
            self.favorites = self._sort_favorites(safe_data)
        except OSError:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def get_all_favorites(self):
        return list(self.favorites)

    def is_favorite(self, kos_item):
        target_id = self._normalize_item_id(kos_item)
        return any(self._normalize_item_id(item) == target_id for item in self.favorites)

    def add_favorite(self, kos_item):
        if self.is_favorite(kos_item):
            return False

        new_item = dict(kos_item)
        if not new_item.get("added_at"):
            new_item["added_at"] = datetime.utcnow().isoformat() + "Z"

        self.favorites.insert(0, new_item)
        self.save_favorites(self.favorites)
        return True

    def remove_favorite(self, kos_item):
        target_id = self._normalize_item_id(kos_item)
        updated = [item for item in self.favorites if self._normalize_item_id(item) != target_id]

        if len(updated) == len(self.favorites):
            return False

        self.save_favorites(updated)
        return True


class FavoritesWindow(ctk.CTkToplevel):
    def __init__(self, parent, favorites_manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.favorites_manager = favorites_manager

        self.title("Favorites Kos")
        self.geometry("920x720")
        self.resizable(True, True)
        self.configure(fg_color=APP_BG)

        container = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        container.pack(fill="both", expand=True, padx=16, pady=16)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(18, 12))

        title_label = ctk.CTkLabel(
            header,
            text="Favorit Kos",
            font=("Arial", 24, "bold"),
            text_color=PRIMARY_COLOR,
            anchor="w",
        )
        title_label.pack(side="left", fill="x", expand=True)

        self.label_count = ctk.CTkLabel(
            header,
            text="",
            font=("Arial", 12),
            text_color=TEXT_SUBTLE,
        )
        self.label_count.pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent",
            border_width=0,
            corner_radius=12,
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.refresh_list()

    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        favorites = self.favorites_manager.get_all_favorites()
        self.label_count.configure(text=f"{len(favorites)} favorit")

        if not favorites:
            empty_label = ctk.CTkLabel(
                self.scroll_frame,
                text="Belum ada kos favorit. Tambahkan favorit dari detail kos.",
                font=("Arial", 14),
                text_color=TEXT_SUBTLE,
                justify="center",
            )
            empty_label.pack(fill="both", expand=True, pady=60)
            return

        for kos_item in favorites:
            wrapper = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            wrapper.pack(fill="x", padx=8, pady=(0, 16))
            wrapper.grid_columnconfigure(0, weight=1)

            card = KosCard(wrapper, kos_item, width=720)
            card.pack(side="left", fill="x", expand=True)

            action_panel = ctk.CTkFrame(wrapper, fg_color="transparent")
            action_panel.pack(side="right", fill="y", padx=(14, 0))

            remove_button = ctk.CTkButton(
                action_panel,
                text="Hapus Favorit",
                fg_color=ACCENT_COLOR,
                hover_color="#B45E24",
                text_color="white",
                corner_radius=12,
                height=40,
                font=("Arial", 12, "bold"),
                command=lambda item=kos_item: self._remove_favorite(item),
            )
            remove_button.pack(anchor="n", pady=(20, 0), padx=4)

    def _remove_favorite(self, kos_item):
        self.favorites_manager.remove_favorite(kos_item)
        self.refresh_list()
