# -------------------------------------------------------------
#  Mercy Tracker
# -------------------------------------------------------------

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QInputDialog,
    QDialog,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QStyleFactory,
    QStackedLayout,
    QButtonGroup,
)
from PySide6.QtCore import Qt, Slot, Signal, QSettings

from ui.shardinventory import ShardInventory


# -------------------------------------------------------------
#  Mercy rules for each shard type
# -------------------------------------------------------------
MERCY_RULES = {
    "Ancient": {
        "base": 0.5,
        "soft": 200,
        "inc": 5.0,
        "hard": 219,
        "rarity": "Legendary",
    },
    "Void": {
        "base": 0.5,
        "soft": 200,
        "inc": 5.0,
        "hard": 219,
        "rarity": "Legendary",
    },
    "Sacred": {
        "base": 6.0,
        "soft": 12,
        "inc": 2.0,
        "hard": 59,
        "rarity": "Legendary",
    },
    "Primal": {
        "base": 0.1,
        "soft": 200,
        "inc": 10.0,
        "hard": 210,
        "rarity": "Mythical",
    },
}


# -------------------------------------------------------------
#  Shard colours + neutral UI colours
# -------------------------------------------------------------
SHARD_COLOURS = {
    "Ancient": "#4da6ff",
    "Void": "#b57bff",
    "Primal": "#ff4c4c",
    "Sacred": "#ffd700",
}

NEUTRAL_BORDER = "#555"
NEUTRAL_TEXT = "#cccccc"
ACTION_BOX_BG = "#333"


# -------------------------------------------------------------
#  ShardTrackerWidget
# -------------------------------------------------------------
class ShardTrackerWidget(QWidget):
    pity_changed = Signal(str, int)

    def __init__(self, shard_name: str):
        super().__init__()

        self.shard_name = shard_name
        self.settings = QSettings("SketeRAID", "Hydra Companion")
        self.colour = SHARD_COLOURS.get(shard_name, "#2d6cdf")

        # Inventory mapping
        mapping = {
            "Ancient": ("Ancient Shards", "ancient"),
            "Void": ("Void Shards", "void"),
            "Primal": ("Primal Shards", "primal"),
            "Sacred": ("Sacred Shards", "sacred"),
        }
        self.shard_display_name, self.inventory_key = mapping.get(
            shard_name, (shard_name, None)
        )

        # Supported rarities
        if shard_name in ("Ancient", "Void"):
            self.supported_rarities = ["Epic", "Legendary"]
        elif shard_name == "Primal":
            self.supported_rarities = ["Legendary", "Mythical"]
        elif shard_name == "Sacred":
            self.supported_rarities = ["Legendary"]
        else:
            self.supported_rarities = []

        # Pity counters
        self.pity = {r: 0 for r in self.supported_rarities}

        # Load saved pity
        primary_map = {
            "Ancient": ("ancient", "Legendary"),
            "Void": ("void", "Legendary"),
            "Sacred": ("sacred", "Legendary"),
            "Primal": ("primal", "Mythical"),
        }
        if shard_name in primary_map:
            key, rarity = primary_map[shard_name]
            saved = int(self.settings.value(f"pity/{key}", 0))
            self.pity[rarity] = max(saved, 0)

        self.dashboard_tab = None
        self.inventory: ShardInventory | None = None

        # ---------------- UI ----------------
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(15)

        # Inventory label
        self.inventory_label = QLabel("Current inventory: —")
        self.inventory_label.setAlignment(Qt.AlignCenter)
        self.inventory_label.setStyleSheet("font-size: 12px; opacity: 0.8;")
        main_layout.addWidget(self.inventory_label)

        # Pity box
        self.pity_box = QFrame()
        self._apply_pity_box_style(True)

        pity_layout = QVBoxLayout(self.pity_box)
        pity_layout.setAlignment(Qt.AlignTop)
        pity_layout.setSpacing(4)

        title = QLabel("Pity counters (shards since last hit)")
        title.setStyleSheet("font-size: 12px; font-weight: bold;")
        pity_layout.addWidget(title)

        self.pity_labels = {}
        for rarity in self.supported_rarities:
            lbl = QLabel(f"{rarity}: {self.pity[rarity]}")
            lbl.setStyleSheet(f"font-size: 12px; color: {self.colour};")
            pity_layout.addWidget(lbl)
            self.pity_labels[rarity] = lbl

        main_layout.addWidget(self.pity_box)
        main_layout.addItem(
            QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Action box
        button_frame = QFrame()
        button_frame.setStyleSheet(
            "QFrame {"
            f"  border: 1px solid {NEUTRAL_BORDER};"
            "  border-radius: 8px;"
            f"  background-color: {ACTION_BOX_BG};"
            "  padding: 10px;"
            "}"
        )
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(12)
        button_layout.setAlignment(Qt.AlignCenter)

        self.btn_single = QPushButton("+1 Pull")
        self.btn_ten = QPushButton("10 Pulls")
        self.btn_custom = QPushButton("Custom Pulls")
        self.btn_reset = QPushButton("Reset")

        for btn in (self.btn_single, self.btn_ten, self.btn_custom):
            btn.setMinimumWidth(110)
            btn.setStyleSheet(
                "QPushButton {"
                "  font-size: 14px;"
                "  padding: 8px 12px;"
                "  border-radius: 6px;"
                "  background-color: #444;"
                "  color: white;"
                "}"
                "QPushButton:hover { background-color: #555; }"
            )

        self._apply_reset_button_style(True)

        button_layout.addWidget(self.btn_single)
        button_layout.addWidget(self.btn_ten)
        button_layout.addWidget(self.btn_custom)
        button_layout.addWidget(self.btn_reset)
        main_layout.addWidget(button_frame)

        # Connections
        self.btn_single.clicked.connect(self.handle_single_pull)
        self.btn_ten.clicked.connect(self.handle_ten_pull)
        self.btn_custom.clicked.connect(self.handle_custom_pull)
        self.btn_reset.clicked.connect(self.reset_pity)

        self.update_pity_labels()
        self.emit_primary_pity()

    # -------------------------------------------------------------
    #  UI Helpers
    # -------------------------------------------------------------
    def _apply_pity_box_style(self, active: bool):
        border = self.colour if active else NEUTRAL_BORDER
        self.pity_box.setStyleSheet(
            f"QFrame {{ border: 1px solid {border}; border-radius: 8px; padding: 12px; }}"
        )

    def _apply_reset_button_style(self, active: bool):
        self.btn_reset.setMinimumWidth(110)
        self.btn_reset.setStyleSheet(
            "QPushButton {"
            "  font-size: 14px;"
            "  padding: 8px 12px;"
            "  border-radius: 6px;"
            "  background-color: #cc3333;"
            "  color: white;"
            "  border: none;"
            "}"
            "QPushButton:hover { background-color: #dd4444; }"
        )

    def set_active(self, active: bool):
        self._apply_pity_box_style(active)
        self._apply_reset_button_style(active)
        for _, lbl in self.pity_labels.items():
            lbl.setStyleSheet(
                f"font-size: 12px; color: {self.colour if active else NEUTRAL_TEXT};"
            )

    # -------------------------------------------------------------
    #  Inventory
    # -------------------------------------------------------------
    def set_inventory(self, inventory: ShardInventory):
        self.inventory = inventory
        if not self.inventory_key:
            self.inventory_label.setText("Current inventory: —")
            return
        self._update_inventory_label(inventory.to_dict())
        inventory.inventory_changed.connect(self._update_inventory_label)

    def _update_inventory_label(self, data: dict):
        if not self.inventory_key:
            return
        value = data.get(self.inventory_key, 0)
        self.inventory_label.setText(f"Current inventory: {value}")

    def _get_current_inventory(self) -> int:
        if not self.inventory or not self.inventory_key:
            return 0
        return int(self.inventory.to_dict().get(self.inventory_key, 0))

    def _ensure_inventory_for_pulls(self, pulls: int) -> bool:
        if pulls <= 0 or not self.inventory_key:
            return True

        current = self._get_current_inventory()
        if pulls <= current:
            return True

        msg = (
            "You are trying to pull more shards than you currently have tracked.\n\n"
            f"Tracked: {current}\n"
            f"Requested pulls: {pulls}\n\n"
            "How many shards do you actually have in-game right now?"
        )
        new_count, ok = QInputDialog.getInt(
            self, "Not enough shards", msg, current, 0, 999999, 1
        )
        if not ok:
            return False

        diff = new_count - current
        if diff > 0:
            for _ in range(diff):
                self.inventory.add(self.inventory_key)
        elif diff < 0:
            for _ in range(-diff):
                self.inventory.remove(self.inventory_key)

        return pulls <= new_count

    def _deduct_inventory(self, pulls: int):
        if not self.inventory_key or not self.inventory:
            return
        for _ in range(pulls):
            self.inventory.remove(self.inventory_key)

    # -------------------------------------------------------------
    #  Pity + Settings
    # -------------------------------------------------------------
    def update_pity_labels(self):
        for rarity, value in self.pity.items():
            self.pity_labels[rarity].setText(f"{rarity}: {value}")

    def emit_primary_pity(self):
        primary_map = {
            "Ancient": ("Legendary", "ancient"),
            "Void": ("Legendary", "void"),
            "Sacred": ("Legendary", "sacred"),
            "Primal": ("Mythical", "primal"),
        }
        if self.shard_name not in primary_map:
            return

        rarity_key, settings_key = primary_map[self.shard_name]
        if rarity_key not in self.pity:
            return

        value = self.pity[rarity_key]
        self.settings.setValue(f"pity/{settings_key}", value)
        self.pity_changed.emit(self.shard_display_name, value)

    # -------------------------------------------------------------
    #  Reset
    # -------------------------------------------------------------
    def _confirm_reset_pity(self):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Confirm Reset")
        box.setText(
            "Are you sure you want to continue with resetting your pity?\n\n"
            "This action cannot be undone."
        )
        yes_btn = box.addButton("Yes, Reset Pity", QMessageBox.AcceptRole)
        box.addButton("Cancel", QMessageBox.RejectRole)
        box.exec()
        return box.clickedButton() == yes_btn

    @Slot()
    def reset_pity(self):
        if not self._confirm_reset_pity():
            return
        for r in self.pity:
            self.pity[r] = 0
        self.update_pity_labels()
        self.emit_primary_pity()

    # -------------------------------------------------------------
    #  Hard Pity
    # -------------------------------------------------------------
    def _highest_rarity_for_shard(self):
        return {
            "Ancient": "Legendary",
            "Void": "Legendary",
            "Sacred": "Legendary",
            "Primal": "Mythical",
        }.get(self.shard_name)

    def _check_and_handle_hard_pity(self):
        rules = MERCY_RULES.get(self.shard_name)
        highest = self._highest_rarity_for_shard()
        if not rules or not highest:
            return
        if self.pity.get(highest, 0) >= rules["hard"]:
            self._handle_hard_pity_reached()

    def _show_hard_pity_choice_dialog(self, highest_rarity: str):
        msg = (
            "You have reached or exceeded the Hard Pity Level.\n\n"
            f"A guaranteed {highest_rarity} should have occurred.\n\n"
            "Choose an option:\n"
            "- Record Hit: Log the highest rarity pulled.\n"
            "- Reset Pity: Reset your pity counter to 0."
        )
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Hard Pity Reached")
        box.setText(msg)

        record_btn = box.addButton("Record Hit", QMessageBox.AcceptRole)
        reset_btn = box.addButton("Reset Pity", QMessageBox.DestructiveRole)
        box.addButton("Cancel", QMessageBox.RejectRole)

        box.exec()
        clicked = box.clickedButton()

        if clicked == record_btn:
            return "record"
        if clicked == reset_btn:
            return "reset"
        return "cancel"

    def _record_hard_pity_hit(self, highest_rarity: str):
        for r in self.pity:
            self.pity[r] = 0
        self.update_pity_labels()
        self.emit_primary_pity()

        if self.dashboard_tab:
            self.dashboard_tab.register_pull(self.shard_display_name, highest_rarity)

    def _handle_hard_pity_reached(self):
        highest = self._highest_rarity_for_shard()
        if not highest:
            return
        choice = self._show_hard_pity_choice_dialog(highest)
        if choice == "record":
            self._record_hard_pity_hit(highest)
        elif choice == "reset":
            self.reset_pity()

    # -------------------------------------------------------------
    #  Pull Handlers
    # -------------------------------------------------------------
    @Slot()
    def handle_single_pull(self):
        if not self._ensure_inventory_for_pulls(1):
            return

        rarities = list(self.supported_rarities) + ["No Hit"]
        dialog, selected = self._build_rarity_dialog(
            "Single Pull Result",
            "Select the rarity for this pull.",
            rarities,
        )

        if not dialog.exec():
            return

        rarity = selected["rarity"]

        if rarity == "No Hit" or rarity is None:
            for r in self.pity:
                self.pity[r] += 1
        else:
            if rarity in self.pity:
                for r in self.pity:
                    if r == rarity:
                        self.pity[r] = 0
                    else:
                        if r == "Epic" and rarity in ("Legendary", "Mythical"):
                            self.pity[r] = 0
                        if r == "Legendary" and rarity == "Mythical":
                            self.pity[r] = 0

            if self.dashboard_tab:
                self.dashboard_tab.register_pull(self.shard_display_name, rarity)

        self._deduct_inventory(1)
        self.update_pity_labels()
        self.emit_primary_pity()
        self._check_and_handle_hard_pity()

    @Slot()
    def handle_ten_pull(self):
        if not self._ensure_inventory_for_pulls(10):
            return

        hits = self.ask_hits_shards_10pull()

        if not hits:
            for r in self.pity:
                self.pity[r] += 10
        else:
            hits_by_rarity = {r: [] for r in self.pity}

            for pos in hits:
                rarity = self.ask_rarity_for_shard(pos)
                if rarity in hits_by_rarity:
                    hits_by_rarity[rarity].append(pos)
                    if self.dashboard_tab:
                        self.dashboard_tab.register_pull(self.shard_display_name, rarity)

            for rarity in self.pity:
                if hits_by_rarity[rarity]:
                    latest = max(hits_by_rarity[rarity])
                    self.pity[rarity] = 10 - latest
                else:
                    self.pity[rarity] += 10

        self._deduct_inventory(10)
        self.update_pity_labels()
        self.emit_primary_pity()
        self._check_and_handle_hard_pity()

    @Slot()
    def handle_custom_pull(self):
        count, ok = QInputDialog.getInt(
            self, "Custom Pulls", "How many pulls?", 1, 1, 9999, 1
        )
        if not ok:
            return

        if not self._ensure_inventory_for_pulls(count):
            return

        total = count
        remaining = total
        offset = 0

        hits_by_rarity = {r: [] for r in self.pity}

        while remaining > 0:
            block = min(10, remaining)
            start = offset + 1
            end = offset + block

            block_hits = self.ask_hits_shards_block(block, start, end)

            for pos in block_hits:
                rarity = self.ask_rarity_for_shard(pos)
                if rarity in hits_by_rarity:
                    hits_by_rarity[rarity].append(pos)
                    if self.dashboard_tab:
                        self.dashboard_tab.register_pull(self.shard_display_name, rarity)

            remaining -= block
            offset += block

        for rarity in self.pity:
            if hits_by_rarity[rarity]:
                latest = max(hits_by_rarity[rarity])
                self.pity[rarity] = total - latest
            else:
                self.pity[rarity] += total

        self._deduct_inventory(total)
        self.update_pity_labels()
        self.emit_primary_pity()
        self._check_and_handle_hard_pity()

    # -------------------------------------------------------------
    #  Dialogs
    # -------------------------------------------------------------
    def _build_rarity_dialog(self, title: str, message: str, rarities: list[str]):
        dialog = QDialog(self)
        dialog.setStyle(QStyleFactory.create("Fusion"))
        dialog.setWindowTitle(title)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(8)

        info = QLabel(message)
        info.setStyleSheet("font-size: 12px; color: #ccc;")
        layout.addWidget(info)

        style_epic = (
            "QPushButton { background-color: #7b2cff; color: white; "
            "border-radius: 6px; padding: 6px 10px; border: none; }"
        )
        style_legendary = (
            "QPushButton { background-color: #d4af37; color: black; "
            "border-radius: 6px; padding: 6px 10px; border: none; }"
        )
        style_mythical = (
            "QPushButton { background-color: #cc3333; color: white; "
            "border-radius: 6px; padding: 6px 10px; border: none; }"
        )
        style_nohit = (
            "QPushButton { background-color: #444; color: #ccc; "
            "border-radius: 6px; padding: 6px 10px; border: none; }"
        )

        selected = {"rarity": None}
        buttons = {}

        rarity_row = QHBoxLayout()
        rarity_row.setSpacing(8)

        for rarity in rarities:
            if rarity == "Epic":
                base = style_epic
            elif rarity == "Legendary":
                base = style_legendary
            elif rarity == "Mythical":
                base = style_mythical
            else:
                base = style_nohit

            btn = QPushButton(rarity)
            btn.setCheckable(True)
            btn.setStyleSheet(
                base
                + "QPushButton:checked { "
                "background-color: #2d6cdf; "
                "color: white; "
                "border: 2px solid white; "
                "font-weight: bold; "
                "} "
            )

            def handler(r=rarity, b=btn):
                selected["rarity"] = r
                for other in buttons.values():
                    if other is not b:
                        other.setChecked(False)
                b.setChecked(True)

            btn.clicked.connect(handler)
            buttons[rarity] = btn
            rarity_row.addWidget(btn)

        layout.addLayout(rarity_row)

        bottom_row = QHBoxLayout()
        bottom_row.setAlignment(Qt.AlignRight)
        bottom_row.setSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #555; color: #eee; "
            "border-radius: 6px; padding: 6px 10px; }"
        )

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setStyleSheet(
            "QPushButton { background-color: #2d6cdf; color: white; "
            "border-radius: 6px; padding: 6px 10px; }"
        )

        cancel_btn.clicked.connect(dialog.reject)
        confirm_btn.clicked.connect(dialog.accept)

        bottom_row.addWidget(cancel_btn)
        bottom_row.addWidget(confirm_btn)
        layout.addLayout(bottom_row)

        return dialog, selected

    def ask_hits_shards_10pull(self) -> list[int]:
        dialog = QDialog(self)
        dialog.setWindowTitle("10‑Pull: Hit Positions")
        dialog.setStyle(QStyleFactory.create("Fusion"))

        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)

        label = QLabel("Select which shard positions (1–10) were hits.")
        label.setStyleSheet("font-size: 12px; color: #ccc;")
        layout.addWidget(label)

        grid = QGridLayout()
        grid.setSpacing(6)

        buttons = {}
        for i in range(1, 11):
            btn = QPushButton(str(i))
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { background-color: #444; color: #eee; "
                "border-radius: 6px; padding: 6px 10px; }"
                "QPushButton:checked { background-color: #2d6cdf; color: white; }"
            )
            buttons[i] = btn
            grid.addWidget(btn, (i - 1) // 5, (i - 1) % 5)

        layout.addLayout(grid)

        bottom = QHBoxLayout()
        bottom.setAlignment(Qt.AlignRight)

        cancel_btn = QPushButton("Cancel")
        confirm_btn = QPushButton("Confirm")

        cancel_btn.clicked.connect(dialog.reject)
        confirm_btn.clicked.connect(dialog.accept)

        bottom.addWidget(cancel_btn)
        bottom.addWidget(confirm_btn)
        layout.addLayout(bottom)

        if not dialog.exec():
            return []

        return [i for i, b in buttons.items() if b.isChecked()]

    def ask_rarity_for_shard(self, position: int) -> str:
        rarities = list(self.supported_rarities) + ["No Hit"]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Hit at Position {position}")
        dialog.setStyle(QStyleFactory.create("Fusion"))

        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)

        label = QLabel(f"Select the rarity for hit at position {position}:")
        label.setStyleSheet("font-size: 12px; color: #ccc;")
        layout.addWidget(label)

        selected = {"rarity": None}
        buttons = {}

        row = QHBoxLayout()
        row.setSpacing(8)

        style_epic = (
            "QPushButton { background-color: #7b2cff; color: white; "
            "border-radius: 6px; padding: 6px 10px; border: none; }"
        )
        style_legendary = (
            "QPushButton { background-color: #d4af37; color: black; "
            "border-radius: 6px; padding: 6px 10px; border: none; }"
        )
        style_mythical = (
            "QPushButton { background-color: #cc3333; color: white; "
            "border-radius: 6px; padding: 6px 10px; border: none; }"
        )
        style_nohit = (
            "QPushButton { background-color: #444; color: #ccc; "
            "border-radius: 6px; padding: 6px 10px; border: none; }"
        )

        for rarity in rarities:
            if rarity == "Epic":
                base = style_epic
            elif rarity == "Legendary":
                base = style_legendary
            elif rarity == "Mythical":
                base = style_mythical
            else:
                base = style_nohit

            btn = QPushButton(rarity)
            btn.setCheckable(True)
            btn.setStyleSheet(
                base
                + "QPushButton:checked { background-color: #2d6cdf; color: white; "
                "border: 2px solid white; font-weight: bold; }"
            )

            def handler(r=rarity, b=btn):
                selected["rarity"] = r
                for other in buttons.values():
                    if other is not b:
                        other.setChecked(False)
                b.setChecked(True)

            btn.clicked.connect(handler)
            buttons[rarity] = btn
            row.addWidget(btn)

        layout.addLayout(row)

        bottom = QHBoxLayout()
        bottom.setAlignment(Qt.AlignRight)

        cancel_btn = QPushButton("Cancel")
        confirm_btn = QPushButton("Confirm")

        cancel_btn.clicked.connect(dialog.reject)
        confirm_btn.clicked.connect(dialog.accept)

        bottom.addWidget(cancel_btn)
        bottom.addWidget(confirm_btn)
        layout.addLayout(bottom)

        if not dialog.exec():
            return "No Hit"

        return selected["rarity"] or "No Hit"

    def ask_hits_shards_block(self, block_size: int, start: int, end: int) -> list[int]:
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Hits in Positions {start}–{end}")
        dialog.setStyle(QStyleFactory.create("Fusion"))

        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)

        label = QLabel(f"Select which positions ({start}–{end}) were hits:")
        label.setStyleSheet("font-size: 12px; color: #ccc;")
        layout.addWidget(label)

        grid = QGridLayout()
        grid.setSpacing(6)

        buttons = {}
        for i in range(start, end + 1):
            btn = QPushButton(str(i))
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { background-color: #444; color: #eee; "
                "border-radius: 6px; padding: 6px 10px; }"
                "QPushButton:checked { background-color: #2d6cdf; color: white; }"
            )
            buttons[i] = btn
            grid.addWidget(btn, (i - start) // 5, (i - start) % 5)

        layout.addLayout(grid)

        bottom = QHBoxLayout()
        bottom.setAlignment(Qt.AlignRight)

        cancel_btn = QPushButton("Cancel")
        confirm_btn = QPushButton("Confirm")

        cancel_btn.clicked.connect(dialog.reject)
        confirm_btn.clicked.connect(dialog.accept)

        bottom.addWidget(cancel_btn)
        bottom.addWidget(confirm_btn)
        layout.addLayout(bottom)

        if not dialog.exec():
            return []

        return [i for i, b in buttons.items() if b.isChecked()]


# -------------------------------------------------------------
#  MercyTrackerTab
# -------------------------------------------------------------
class MercyTrackerTab(QWidget):
    pity_updated = Signal(str, int)

    def __init__(self):
        super().__init__()

        self.dashboard_tab = None
        self.inventory: ShardInventory | None = None

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(15)

        seg_frame = QFrame()
        seg_frame.setStyleSheet(
            "QFrame {"
            "  border: 1px solid #666;"
            "  border-radius: 8px;"
            "}"
        )

        seg_layout = QHBoxLayout(seg_frame)
        seg_layout.setContentsMargins(0, 0, 0, 0)
        seg_layout.setSpacing(0)

        self.segment_group = QButtonGroup(self)
        self.segment_group.setExclusive(True)
        self.segment_buttons = {}

        def make_segment(name: str, index: int):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._segment_style(name, checked=(index == 0)))
            self.segment_group.addButton(btn, index)
            self.segment_buttons[name] = btn
            seg_layout.addWidget(btn)
            return btn

        make_segment("Ancient", 0)
        make_segment("Void", 1)
        make_segment("Primal", 2)
        make_segment("Sacred", 3)

        main_layout.addWidget(seg_frame)

        self.stack_container = QFrame()
        self.stack_layout = QStackedLayout(self.stack_container)

        self.ancient_tab = ShardTrackerWidget("Ancient")
        self.void_tab = ShardTrackerWidget("Void")
        self.primal_tab = ShardTrackerWidget("Primal")
        self.sacred_tab = ShardTrackerWidget("Sacred")

        self.stack_layout.addWidget(self.ancient_tab)
        self.stack_layout.addWidget(self.void_tab)
        self.stack_layout.addWidget(self.primal_tab)
        self.stack_layout.addWidget(self.sacred_tab)

        main_layout.addWidget(self.stack_container)

        self.ancient_tab.pity_changed.connect(self.pity_updated.emit)
        self.void_tab.pity_changed.connect(self.pity_updated.emit)
        self.primal_tab.pity_changed.connect(self.pity_updated.emit)
        self.sacred_tab.pity_changed.connect(self.pity_updated.emit)

        self.segment_group.idClicked.connect(self._on_segment_clicked)

        self.segment_group.button(0).setChecked(True)
        self._set_active_shard_index(0)

    def _segment_style(self, shard_name: str, checked: bool) -> str:
        colour = SHARD_COLOURS.get(shard_name, "#2d6cdf")
        if checked:
            return (
                "QPushButton {"
                f"  background-color: {colour};"
                "  color: black;"
                "  border: none;"
                "  padding: 8px 12px;"
                "  font-weight: bold;"
                "  border-top-left-radius: 8px;"
                "  border-top-right-radius: 8px;"
                "}"
            )
        else:
            return (
                "QPushButton {"
                "  background-color: #444;"
                "  color: #ccc;"
                "  border: none;"
                "  padding: 8px 12px;"
                "  font-weight: normal;"
                "}"
                "QPushButton:hover {"
                f"  background-color: {colour};"
                "  color: black;"
                "}"
            )

    def _refresh_segment_styles(self, active_index: int):
        names = ["Ancient", "Void", "Primal", "Sacred"]
        for idx, name in enumerate(names):
            btn = self.segment_buttons.get(name)
            if btn:
                btn.setStyleSheet(
                    self._segment_style(name, checked=(idx == active_index))
                )

    @Slot(int)
    def _on_segment_clicked(self, index: int):
        self._set_active_shard_index(index)

    def _set_active_shard_index(self, index: int):
        self.stack_layout.setCurrentIndex(index)
        self._refresh_segment_styles(index)

        widgets = [
            self.ancient_tab,
            self.void_tab,
            self.primal_tab,
            self.sacred_tab,
        ]
        for i, w in enumerate(widgets):
            w.set_active(i == index)

    def set_dashboard(self, dashboard):
        self.dashboard_tab = dashboard
        self.ancient_tab.dashboard_tab = dashboard
        self.void_tab.dashboard_tab = dashboard
        self.primal_tab.dashboard_tab = dashboard
        self.sacred_tab.dashboard_tab = dashboard

    def set_inventory(self, inventory: ShardInventory):
        self.inventory = inventory
        self.ancient_tab.set_inventory(inventory)
        self.void_tab.set_inventory(inventory)
        self.primal_tab.set_inventory(inventory)
        self.sacred_tab.set_inventory(inventory)