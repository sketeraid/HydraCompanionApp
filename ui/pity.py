from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QComboBox,
    QHBoxLayout,
    QFrame,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSettings
from PySide6.QtWidgets import QGraphicsOpacityEffect


class PityPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Persistent storage
        self.settings = QSettings("SketeRAID", "Hydra Companion")

        # Theme awareness
        self.current_theme = "dark"

        # Mercy rules
        self.banners = {
            "Ancient Shards": {
                "current": 0,
                "base": 0.5,
                "soft": 200,
                "inc": 5.0,
                "hard": 219,
                "rarity": "Legendary",
            },
            "Void Shards": {
                "current": 0,
                "base": 0.5,
                "soft": 200,
                "inc": 5.0,
                "hard": 219,
                "rarity": "Legendary",
            },
            "Sacred Shards": {
                "current": 0,
                "base": 6.0,
                "soft": 12,
                "inc": 2.0,
                "hard": 59,
                "rarity": "Legendary",
            },
            "Primal Shards": {
                "current": 0,
                "base": 0.1,
                "soft": 200,
                "inc": 10.0,
                "hard": 210,
                "rarity": "Mythical",
            },
        }

        # Load saved pity
        key_map = {
            "Ancient Shards": "ancient",
            "Void Shards": "void",
            "Sacred Shards": "sacred",
            "Primal Shards": "primal",
        }

        for banner, key in key_map.items():
            saved = int(self.settings.value(f"pity/{key}", 0))
            self.banners[banner]["current"] = saved

        # Load curve history
        self.curve_history = self._load_curve_history()

        self.current_banner = "Ancient Shards"
        self.last_chance_value = 0.0

        self.pulse_effect = None
        self.pulse_animation = None
        self.value_animation = None

        # ------------------------------
        # Main Layout
        # ------------------------------
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(14)

        # --- Shard type selector row ---
        banner_row = QHBoxLayout()
        shard_label = QLabel("Shard Type:")
        shard_label.setStyleSheet("font-size: 14px;")
        banner_row.addWidget(shard_label)

        self.banner_selector = QComboBox()
        self.banner_selector.addItem("Ancient", "Ancient Shards")
        self.banner_selector.addItem("Void", "Void Shards")
        self.banner_selector.addItem("Sacred", "Sacred Shards")
        self.banner_selector.addItem("Primal", "Primal Shards")
        self.banner_selector.setCurrentIndex(0)
        self.banner_selector.currentIndexChanged.connect(self._on_banner_changed)
        banner_row.addWidget(self.banner_selector)
        banner_row.addStretch()
        main_layout.addLayout(banner_row)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #444;")
        main_layout.addWidget(divider)

        # --- Progress bar block ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        # Combined label
        self.combined_label = QLabel()
        self.combined_label.setAlignment(Qt.AlignCenter)
        self.combined_label.setStyleSheet("font-size: 13px;")
        main_layout.addWidget(self.combined_label)

        # Increment label
        self.increment_label = QLabel()
        self.increment_label.setAlignment(Qt.AlignCenter)
        self.increment_label.setStyleSheet("font-size: 12px; color: #A0A0A0;")
        main_layout.addWidget(self.increment_label)

        # --- Status box ---
        self.status_frame = QFrame()
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setContentsMargins(8, 6, 8, 6)
        status_layout.setAlignment(Qt.AlignCenter)

        self.rarity_preview = QLabel()
        self.rarity_preview.setAlignment(Qt.AlignCenter)
        self.rarity_preview.setStyleSheet("font-size: 14px;")
        status_layout.addWidget(self.rarity_preview)

        main_layout.addWidget(self.status_frame)

        # --- Milestone box ---
        self.milestone_frame = QFrame()
        milestone_layout = QVBoxLayout(self.milestone_frame)
        milestone_layout.setContentsMargins(8, 6, 8, 6)
        milestone_layout.setSpacing(2)

        self.milestone_soft = QLabel()
        self.milestone_hard = QLabel()
        self.milestone_next = QLabel()

        for lbl in (self.milestone_soft, self.milestone_hard, self.milestone_next):
            lbl.setStyleSheet("font-size: 12px;")
            milestone_layout.addWidget(lbl)

        main_layout.addWidget(self.milestone_frame)

        # ---------------------------------------------------------
        # NEW: Pity Curve Frame (replaces sparkline)
        # ---------------------------------------------------------
        self.curve_frame = QFrame()
        curve_layout = QVBoxLayout(self.curve_frame)
        curve_layout.setContentsMargins(8, 6, 8, 6)
        curve_layout.setSpacing(4)

        self.curve_title = QLabel("Pity Curve")
        self.curve_title.setAlignment(Qt.AlignCenter)
        self.curve_title.setStyleSheet("font-size: 13px; font-weight: bold;")
        curve_layout.addWidget(self.curve_title)

        # 6 rows of hybrid curve
        self.curve_rows = []
        for _ in range(6):
            row = QLabel()
            row.setAlignment(Qt.AlignCenter)
            row.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 11px;")
            self.curve_rows.append(row)
            curve_layout.addWidget(row)

        self.curve_explanation = QLabel(
            "Current pity shown bold. Previous cycles appear as faint ghost lines."
        )
        self.curve_explanation.setAlignment(Qt.AlignCenter)
        self.curve_explanation.setStyleSheet("font-size: 11px; color: #A0A0A0;")
        curve_layout.addWidget(self.curve_explanation)

        main_layout.addWidget(self.curve_frame)

        # Apply theme + UI
        self.apply_theme_styles()
        self.refresh_ui(initial=True)
    # ---------------------------------------------------------
    # Theme handling
    # ---------------------------------------------------------

    def set_theme(self, theme: str):
        self.current_theme = theme
        self.apply_theme_styles()
        self.refresh_ui(initial=True)

    def apply_theme_styles(self):
        """
        Applies theme styling to all UI elements, including the new Pity Curve frame.
        """
        if self.current_theme == "dark":
            track_bg = "#222222"
            text_color = "#FFFFFF"

            tooltip_style = """
                QToolTip {
                    background-color: #333333;
                    color: #f0f0f0;
                    border: 1px solid #888;
                    padding: 6px;
                    font-size: 12px;
                }
            """

            status_bg = "#222222"
            status_border = "#555555"
            milestone_bg = "#1b1b1b"
            milestone_border = "#555555"

        else:
            track_bg = "#EEEEEE"
            text_color = "#202020"

            tooltip_style = """
                QToolTip {
                    background-color: #fdfdfd;
                    color: #202020;
                    border: 1px solid #aaa;
                    padding: 6px;
                    font-size: 12px;
                }
            """

            status_bg = "#f0f0f0"
            status_border = "#CCCCCC"
            milestone_bg = "#f5f5f5"
            milestone_border = "#CCCCCC"

        # Apply tooltip theme
        if self.window():
            current = self.window().styleSheet()
            self.window().setStyleSheet(current + tooltip_style)

        # Global widget theme
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: transparent;
                color: {text_color};
            }}
            QComboBox {{
                background-color: {track_bg};
                color: {text_color};
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {track_bg};
                color: {text_color};
                selection-background-color: #555555;
            }}
        """
        )

        # Progress bar base style
        self.base_progress_stylesheet = f"""
            QProgressBar {{
                border: 1px solid #444;
                border-radius: 6px;
                background-color: {track_bg};
                text-align: center;
                color: {text_color};
            }}
            QProgressBar::chunk {{
                background-color: #4CAF50;
                border-radius: 6px;
            }}
        """
        self.progress_bar.setStyleSheet(self.base_progress_stylesheet)

        # Status frame
        self.status_frame.setStyleSheet(
            f"""
            QFrame {{
                border: 1px solid {status_border};
                border-radius: 8px;
                padding: 8px;
                background-color: {status_bg};
            }}
        """
        )

        # Milestone frame
        self.milestone_frame.setStyleSheet(
            f"""
            QFrame {{
                border: 1px solid {milestone_border};
                border-radius: 8px;
                padding: 6px;
                background-color: {milestone_bg};
            }}
        """
        )

        # NEW: Curve frame theme
        self.curve_frame.setStyleSheet(
            f"""
            QFrame {{
                border: 1px solid {milestone_border};
                border-radius: 8px;
                padding: 6px;
                background-color: {milestone_bg};
            }}
        """
        )

    # ---------------------------------------------------------
    # Mercy logic
    # ---------------------------------------------------------

    def compute_chance(self, banner_name: str) -> float:
        data = self.banners[banner_name]
        pulls = data["current"]
        base = data["base"]
        soft = data["soft"]
        inc = data["inc"]
        hard = data["hard"]

        if pulls <= soft:
            chance = base
        else:
            extra = min(pulls, hard) - soft
            chance = base + extra * inc

        if pulls >= hard:
            chance = 100.0

        return max(0.0, min(chance, 100.0))

    # ---------------------------------------------------------
    # Progress bar animation
    # ---------------------------------------------------------

    def animate_progress(self, new_chance: float, initial: bool = False):
        new_value = int(round(new_chance))

        if initial or self.value_animation is None:
            self.progress_bar.setValue(new_value)
            return

        if self.value_animation.state() == QPropertyAnimation.Running:
            self.value_animation.stop()

        self.value_animation = QPropertyAnimation(self.progress_bar, b"value", self)
        self.value_animation.setDuration(700)
        self.value_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.value_animation.setStartValue(self.progress_bar.value())
        self.value_animation.setEndValue(new_value)
        self.value_animation.start()

    # ---------------------------------------------------------
    # Glow + pulse
    # ---------------------------------------------------------

    def apply_glow_and_pulse(self, chance: float, rarity: str):
        # Reset to base style
        self.progress_bar.setStyleSheet(self.base_progress_stylesheet)

        # Stop previous pulse
        if self.pulse_animation and self.pulse_animation.state() == QPropertyAnimation.Running:
            self.pulse_animation.stop()
        if self.pulse_effect:
            self.progress_bar.setGraphicsEffect(None)
            self.pulse_effect = None

        # Only glow at high chance
        if chance < 75.0:
            return

        chunk_color = "#FFD700" if rarity == "Legendary" else "#FF3B3B"

        if self.current_theme == "dark":
            track_bg = "#222222"
            text_color = "#FFFFFF"
        else:
            track_bg = "#EEEEEE"
            text_color = "#202020"

        glow_stylesheet = f"""
            QProgressBar {{
                border: 1px solid #888;
                border-radius: 6px;
                background-color: {track_bg};
                text-align: center;
                color: {text_color};
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
                border-radius: 6px;
            }}
        """
        self.progress_bar.setStyleSheet(glow_stylesheet)

        # Pulse effect
        self.pulse_effect = QGraphicsOpacityEffect(self.progress_bar)
        self.progress_bar.setGraphicsEffect(self.pulse_effect)

        self.pulse_animation = QPropertyAnimation(self.pulse_effect, b"opacity", self)
        self.pulse_animation.setDuration(1600)
        self.pulse_animation.setStartValue(0.7)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.pulse_animation.setLoopCount(-1)
        self.pulse_animation.start()

    # ---------------------------------------------------------
    # UI refresh
    # ---------------------------------------------------------

    def refresh_ui(self, initial: bool = False):
        data = self.banners[self.current_banner]
        pulls = data["current"]
        soft = data["soft"]
        inc = data["inc"]
        hard = data["hard"]
        rarity = data["rarity"]

        chance = self.compute_chance(self.current_banner)

        # Progress bar animation
        self.animate_progress(chance, initial=initial)

        # Combined label
        self.combined_label.setText(f"{pulls} pulls — {chance:.1f}% chance")
        self.increment_label.setText(f"+{inc:.1f}% per pull after {soft} pulls")

        # Status text
        if chance >= 75.0:
            preview_text = f"High chance of {rarity}"
        elif chance >= 40.0:
            preview_text = f"Growing chance of {rarity}"
        else:
            preview_text = f"Low chance of {rarity}"

        color = "#FFD700" if rarity == "Legendary" else "#FF3B3B"
        self.rarity_preview.setText(preview_text)
        self.rarity_preview.setStyleSheet(f"font-size: 14px; color: {color};")

        # Milestones
        self.milestone_soft.setText(f"Soft Pity: {soft}")
        self.milestone_hard.setText(f"Hard Pity: {hard}")

        if pulls < soft:
            self.milestone_next.setText(f"Next: {soft - pulls} until soft pity")
        elif pulls < hard:
            self.milestone_next.setText(f"Next: {hard - pulls} until hard pity")
        else:
            self.milestone_next.setText("Next: At or beyond hard pity")

        # NEW: Render the hybrid pity curve
        self._render_pity_curve(self.current_banner)

        # Tooltips
        self.progress_bar.setToolTip(
            f"Chance: Your probability of pulling a {rarity} on the next shard.\n"
            f"Currently {chance:.1f}%."
        )

        self.combined_label.setToolTip(
            "Shows your current pity count and the resulting chance for the next pull."
        )

        self.rarity_preview.setToolTip(
            f"Indicates how likely you are to pull a {rarity} based on your current pity."
        )

        # Glow + pulse
        self.apply_glow_and_pulse(chance, rarity)

        self.last_chance_value = chance

    # ---------------------------------------------------------
    # Hybrid 6-row pity curve renderer
    # ---------------------------------------------------------

    def _render_pity_curve(self, banner_name: str):
        """
        Renders a 6-row text-based curve:
        - Current cycle: bold █ characters
        - Previous cycles: faint · ghost lines
        """
        data = self.banners[banner_name]
        pulls = data["current"]
        soft = data["soft"]
        hard = data["hard"]

        rows = 6
        cols = 32  # horizontal resolution

        # Compute normalized chance (0..1)
        def norm_chance(pull: int) -> float:
            if pull <= soft:
                return 0.0
            extra = min(pull, hard) - soft
            span = max(1, hard - soft)
            return max(0.0, min(extra / span, 1.0))

        # Build empty grid
        grid = [[" " for _ in range(cols)] for _ in range(rows)]

        # Map normalized value to row index (0 = top)
        def value_to_row(v: float) -> int:
            return max(0, min(rows - 1, rows - 1 - int(round(v * (rows - 1)))))

        # 1) Draw ghost history
        ghost_cycles = getattr(self, "curve_history", [])[-4:]
        for cycle in ghost_cycles:
            for i in range(cols):
                t = i / max(1, cols - 1)
                virtual_pull = int(t * hard)
                if virtual_pull > len(cycle) - 1:
                    continue
                v = norm_chance(virtual_pull)
                r = value_to_row(v)
                if grid[r][i] == " ":
                    grid[r][i] = "·"

        # 2) Draw current cycle
        for i in range(cols):
            t = i / max(1, cols - 1)
            virtual_pull = int(t * hard)
            if virtual_pull > pulls:
                continue
            v = norm_chance(virtual_pull)
            r = value_to_row(v)
            grid[r][i] = "█"

        # Theme colours
        if self.current_theme == "dark":
            current_color = "#FFFFFF"
            ghost_color = "#777777"
        else:
            current_color = "#202020"
            ghost_color = "#888888"

        # Convert rows to HTML
        for row_idx in range(rows):
            text = "".join(grid[row_idx])
            html = []
            for ch in text:
                if ch == "█":
                    html.append(f'<span style="color:{current_color}">█</span>')
                elif ch == "·":
                    html.append(f'<span style="color:{ghost_color}">·</span>')
                else:
                    html.append("&nbsp;")
            self.curve_rows[row_idx].setText("".join(html))
            self.curve_rows[row_idx].setTextFormat(Qt.RichText)

    # ---------------------------------------------------------
    # Banner switching + pity updates
    # ---------------------------------------------------------

    def _on_banner_changed(self, index: int):
        key = self.banner_selector.itemData(index)
        if key:
            self.update_banner_view(key)

    def update_banner_view(self, banner_name: str):
        if banner_name not in self.banners:
            return
        self.current_banner = banner_name
        self.refresh_ui(initial=True)

    def update_pity(self, banner_name: str, pulls: int):
        if banner_name not in self.banners:
            return

        data = self.banners[banner_name]
        data["current"] = max(0, min(pulls, data["hard"]))

        # Detect completed cycles
        self._record_cycle_if_completed(banner_name, data["current"])

        # Save pity
        key_map = {
            "Ancient Shards": "ancient",
            "Void Shards": "void",
            "Sacred Shards": "sacred",
            "Primal Shards": "primal",
        }

        if banner_name in key_map:
            self.settings.setValue(f"pity/{key_map[banner_name]}", data["current"])

        if banner_name == self.current_banner:
            self.refresh_ui(initial=False)

    # ---------------------------------------------------------
    # Curve history (persistent JSON storage)
    # ---------------------------------------------------------

    def _load_curve_history(self):
        """Load stored pity curve history from QSettings."""
        import json
        raw = self.settings.value("pity_curve/history", "[]")
        try:
            history = json.loads(raw)
            if isinstance(history, list):
                return history
        except Exception:
            pass
        return []

    def _save_curve_history(self):
        """Save curve history to QSettings."""
        import json
        try:
            encoded = json.dumps(self.curve_history)
            self.settings.setValue("pity_curve/history", encoded)
        except Exception:
            pass

    # ---------------------------------------------------------
    # Cycle detection (records completed pity cycles)
    # ---------------------------------------------------------

    def _record_cycle_if_completed(self, banner_name: str, new_pulls: int):
        """
        Detects when a pity cycle completes:
        - previous pulls > 0
        - new pulls == 0
        Stores the completed cycle as a ghost-line entry.
        """
        data = self.banners[banner_name]
        prev = data.get("_previous_pulls", 0)

        # Cycle completed
        if prev > 0 and new_pulls == 0:
            completed = list(range(prev + 1))
            self.curve_history.append(completed)
            self.curve_history = self.curve_history[-4:]  # keep last 4 cycles
            self._save_curve_history()

        # Update previous pulls
        data["_previous_pulls"] = new_pulls