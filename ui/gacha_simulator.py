from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from PySide6.QtCore import Qt
import random


class GachaSimulatorTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(30)

        # Header
        title = QLabel("Gacha Simulator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Results Box
        self.result_box = QFrame()
        self.result_box.setStyleSheet("""
            QFrame {
                border: 1px solid #555;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        result_layout = QVBoxLayout(self.result_box)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.result_label = QLabel("No pull yet")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        result_layout.addWidget(self.result_label)

        layout.addWidget(self.result_box)

        # Buttons Row
        buttons = QHBoxLayout()
        buttons.setSpacing(20)
        buttons.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_single = QPushButton("Single Pull")
        btn_reset = QPushButton("Clear Result")

        btn_single.setMinimumWidth(150)
        btn_reset.setMinimumWidth(150)

        btn_single.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 10px 16px;
            }
        """)

        btn_reset.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 10px 16px;
            }
        """)

        buttons.addWidget(btn_single)
        buttons.addWidget(btn_reset)

        layout.addLayout(buttons)

        # Logic
        btn_single.clicked.connect(self.single_pull)
        btn_reset.clicked.connect(self.clear_result)

    def single_pull(self):
        # Example rarity rates
        roll = random.random()

        if roll < 0.01:
            rarity = "Legendary (1%)"
        elif roll < 0.10:
            rarity = "Epic (9%)"
        elif roll < 0.40:
            rarity = "Rare (30%)"
        else:
            rarity = "Common (60%)"

        self.result_label.setText(rarity)

    def clear_result(self):
        self.result_label.setText("No pull yet")