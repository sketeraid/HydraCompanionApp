from functools import partial

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QFrame, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QSettings

from ui.shardinventory import ShardInventory


SHARD_DISPLAY_NAMES = [
    "Ancient",
    "Void",
    "Primal",
    "Sacred",
]

SHARD_KEY_MAP = {
    "Ancient": "ancient",
    "Void": "void",
    "Primal": "primal",
    "Sacred": "sacred",
}


class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()

        # Persistent storage
        self.settings = QSettings("SketeRAID", "Hydra Companion")

        # Pity values
        self.pity_data = {
            "Ancient": int(self.settings.value("pity/ancient", 0)),
            "Void": int(self.settings.value("pity/void", 0)),
            "Primal": int(self.settings.value("pity/primal", 0)),
            "Sacred": int(self.settings.value("pity/sacred", 0)),
        }

        # Stats
        self.total_pulls = int(self.settings.value("stats/total_pulls", 0))
        self.last_hits = {
            "epic": int(self.settings.value("hits/last_epic", -1)),
            "legendary": int(self.settings.value("hits/last_legendary", -1)),
            "mythical": int(self.settings.value("hits/last_mythical", -1)),
        }

        # Inventory (external)
        self.inventory: ShardInventory | None = None
        self.inventory_labels = {}
        self.summary_labels = {}

        self._build_ui()
        self._refresh_last_hit_labels()

    # ---------------------------------------------------------
    # UI BUILD
    # ---------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(16)
        layout.setContentsMargins(12, 12, 12, 12)

        # Welcome
        welcome = QLabel(
            "Welcome to Hydra Companion\n"
            "Your central hub for tracking, simulation, and live shard insights."
        )
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(welcome)

        subtext = QLabel(
            "Your pity values update automatically as you track pulls.\n"
            "Use the navigation bar above to explore tools and features."
        )
        subtext.setAlignment(Qt.AlignCenter)
        subtext.setStyleSheet("font-size: 14px; opacity: 0.8;")
        layout.addWidget(subtext)

        # Divider
        self.top_divider = QFrame()
        self.top_divider.setFrameShape(QFrame.HLine)
        self.top_divider.setFixedHeight(2)
        layout.addWidget(self.top_divider)

        # Shard bar
        layout.addWidget(self._build_shard_bar())

        # Row: last hit + inventory
        row_frame = QFrame()
        row_layout = QHBoxLayout(row_frame)
        row_layout.setSpacing(16)

        self.last_hit_frame = self._build_last_hit_box()
        self.inventory_frame = self._build_inventory_box()

        row_layout.addWidget(self.last_hit_frame, 1)
        row_layout.addWidget(self.inventory_frame, 1)

        layout.addWidget(row_frame)

        # Recent activity
        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-left: 4px;")
        layout.addWidget(activity_title)

        self.activity_list = QListWidget()
        self.activity_list.setFixedHeight(140)
        layout.addWidget(self.activity_list)

        # Bottom divider + shadow
        self.bottom_divider = QFrame()
        self.bottom_divider.setFrameShape(QFrame.HLine)
        self.bottom_divider.setFixedHeight(1)
        layout.addWidget(self.bottom_divider)

        self.bottom_shadow = QLabel()
        self.bottom_shadow.setFixedHeight(12)
        layout.addWidget(self.bottom_shadow)

    def _build_shard_bar(self):
        bar_frame = QFrame()
        bar_layout = QHBoxLayout(bar_frame)
        bar_layout.setSpacing(16)
        bar_layout.setAlignment(Qt.AlignCenter)

        bar_layout.addStretch(1)

        # Colour map for shard bar titles
        colour_map = {
            "Ancient": "#4da6ff",   # Blue
            "Void": "#b57bff",      # Purple
            "Primal": "#ff4c4c",    # Red
            "Sacred": "#ffd700",    # Gold
        }

        for shard in SHARD_DISPLAY_NAMES:
            segment = QFrame()
            segment.setObjectName("segmentBox")
            segment.setFixedWidth(160)
            segment.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            seg_layout = QVBoxLayout(segment)
            seg_layout.setAlignment(Qt.AlignCenter)
            seg_layout.setSpacing(4)

            title = QLabel(shard)
            title.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: {colour_map[shard]};"
            )

            pity_value = self.pity_data.get(shard, 0)
            pity = QLabel(f"Pity: {pity_value}")
            pity.setStyleSheet("font-size: 12px; opacity: 0.9;")

            seg_layout.addWidget(title)
            seg_layout.addWidget(pity)

            self.summary_labels[shard] = pity
            bar_layout.addWidget(segment)

        bar_layout.addStretch(1)
        return bar_frame

    def _build_last_hit_box(self):
        frame = QFrame()
        frame.setObjectName("lastHitBox")

        layout = QVBoxLayout(frame)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Last Hit Summary")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # Epic first
        self.last_epic_label = QLabel()
        self.last_epic_label.setStyleSheet("font-size: 12px; color: #b57bff;")
        self.last_epic_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.last_epic_label)

        # Legendary second
        self.last_legendary_label = QLabel()
        self.last_legendary_label.setStyleSheet("font-size: 12px; color: #ffd700;")
        self.last_legendary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.last_legendary_label)

        # Mythical last
        self.last_mythical_label = QLabel()
        self.last_mythical_label.setStyleSheet("font-size: 12px; color: #ff4c4c;")
        self.last_mythical_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.last_mythical_label)

        return frame

    def _build_inventory_box(self):
        frame = QFrame()
        frame.setObjectName("inventoryBox")

        layout = QVBoxLayout(frame)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Shard Inventory")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        colour_map = {
            "Ancient": "#4da6ff",   # Blue
            "Void": "#b57bff",      # Purple
            "Primal": "#ff4c4c",    # Red
            "Sacred": "#ffd700",    # Gold
        }

        for shard_name in SHARD_DISPLAY_NAMES:
            row = QHBoxLayout()
            row.setSpacing(4)

            name_label = QLabel(shard_name)
            name_label.setStyleSheet(f"font-size: 12px; color: {colour_map[shard_name]};")

            count_label = QLabel("0")
            count_label.setStyleSheet("font-size: 12px; min-width: 28px;")
            count_label.setAlignment(Qt.AlignCenter)

            btn_minus = QPushButton("-")
            btn_minus.setFixedWidth(24)
            btn_minus.clicked.connect(partial(self.adjust_inventory, shard_name, -1))

            btn_plus = QPushButton("+")
            btn_plus.setFixedWidth(24)
            btn_plus.clicked.connect(partial(self.adjust_inventory, shard_name, +1))

            row.addWidget(name_label)
            row.addStretch(1)
            row.addWidget(btn_minus)
            row.addWidget(count_label)
            row.addWidget(btn_plus)

            layout.addLayout(row)
            self.inventory_labels[shard_name] = count_label

        return frame

    # ---------------------------------------------------------
    # INVENTORY INTEGRATION
    # ---------------------------------------------------------
    def set_inventory(self, inventory: ShardInventory):
        self.inventory = inventory
        inventory.inventory_changed.connect(self.update_inventory)
        self.update_inventory(inventory.to_dict())

    def update_inventory(self, data: dict):
        for shard_name, key in SHARD_KEY_MAP.items():
            value = data.get(key, 0)
            if shard_name in self.inventory_labels:
                self.inventory_labels[shard_name].setText(str(value))

    def adjust_inventory(self, shard_name: str, delta: int):
        if not self.inventory:
            return

        key = SHARD_KEY_MAP.get(shard_name)
        if not key:
            return

        if delta > 0:
            self.inventory.add(key)
        else:
            self.inventory.remove(key)

    # ---------------------------------------------------------
    # LAST HIT TRACKING
    # ---------------------------------------------------------
    def register_pull(self, shard_name: str, rarity: str):
        self.total_pulls += 1
        self.settings.setValue("stats/total_pulls", self.total_pulls)

        r = (rarity or "").strip().lower()

        if r.startswith("myth") or r == "m":
            self.last_hits["mythical"] = self.total_pulls
            self.settings.setValue("hits/last_mythical", self.total_pulls)
        elif r.startswith("legend") or r == "l":
            self.last_hits["legendary"] = self.total_pulls
            self.settings.setValue("hits/last_legendary", self.total_pulls)
        elif r.startswith("epic") or r == "e":
            self.last_hits["epic"] = self.total_pulls
            self.settings.setValue("hits/last_epic", self.total_pulls)

        self._refresh_last_hit_labels()

    def _refresh_last_hit_labels(self):
        def fmt(label, key):
            idx = self.last_hits[key]
            if idx < 0 or self.total_pulls <= 0 or idx > self.total_pulls:
                return f"{label}: no data"
            return f"{label}: {self.total_pulls - idx} pulls ago"

        self.last_epic_label.setText(fmt("Epic", "epic"))
        self.last_legendary_label.setText(fmt("Legendary", "legendary"))
        self.last_mythical_label.setText(fmt("Mythical", "mythical"))

    # ---------------------------------------------------------
    # PITY UPDATES
    # ---------------------------------------------------------
    def update_pity(self, shard_name: str, pity_value: int):
        if shard_name not in self.pity_data:
            return

        key = SHARD_KEY_MAP[shard_name]
        self.settings.setValue(f"pity/{key}", pity_value)

        self.pity_data[shard_name] = pity_value
        self.summary_labels[shard_name].setText(f"Pity: {pity_value}")

        item = QListWidgetItem(f"{shard_name}: pity updated to {pity_value}")
        self.activity_list.insertItem(0, item)

    # ---------------------------------------------------------
    # THEME
    # ---------------------------------------------------------
    def set_theme(self, theme: str):
        if theme == "dark":
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def apply_dark_theme(self):
        glow = "#99ff99"

        self.setStyleSheet(
            f"""
            QLabel {{
                color: #f0f0f0;
                background: transparent;
            }}

            QFrame#segmentBox {{
                border: 2px solid {glow};
                border-radius: 8px;
                background-color: #202020;
                padding: 6px;
                margin-left: auto;
                margin-right: auto;
            }}

            QFrame#lastHitBox, QFrame#inventoryBox {{
                border: 1px solid {glow};
                border-radius: 10px;
                background-color: #111111;
                padding: 12px;
            }}

            QPushButton {{
                background-color: #222222;
                color: #f0f0f0;
                border: 1px solid {glow};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #2b2b2b;
            }}
            """
        )

        self.top_divider.setStyleSheet(f"background-color: {glow};")
        self.bottom_divider.setStyleSheet(f"background-color: {glow};")

        self.bottom_shadow.setStyleSheet(
            """
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(153,255,153,60),
                stop:1 rgba(0,0,0,0)
            );
            """
        )

        self.activity_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: transparent;
                border: 1px solid {glow};
                border-radius: 6px;
                padding: 6px;
            }}
            """
        )

    def apply_light_theme(self):
        green = "#225522"

        self.setStyleSheet(
            f"""
            QLabel {{
                color: #202020;
                background: transparent;
            }}

            QFrame#segmentBox {{
                border: 2px solid {green};
                border-radius: 8px;
                background-color: #f4faf4;
                padding: 6px;
                margin-left: auto;
                margin-right: auto;
            }}

            QFrame#lastHitBox, QFrame#inventoryBox {{
                border: 1px solid {green};
                border-radius: 10px;
                background-color: #f0f5f0;
                padding: 12px;
            }}

            QPushButton {{
                background-color: #ffffff;
                color: #202020;
                border: 1px solid {green};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #f0f5f0;
            }}
            """
        )

        self.top_divider.setStyleSheet(f"background-color: {green};")
        self.bottom_divider.setStyleSheet(f"background-color: {green};")

        self.bottom_shadow.setStyleSheet(
            """
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(34,85,34,60),
                stop:1 rgba(0,0,0,0)
            );
            """
        )

        self.activity_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: transparent;
                border: 1px solid {green};
                border-radius: 6px;
                padding: 6px;
            }}
            """
        )