from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt

from ui.app_metadata import APP_VERSION, APP_BUILD, APP_THEME_KEY


class SettingsPage(QWidget):
    def __init__(self, settings, build_number):
        super().__init__()

        self.settings = settings
        self.build_number = build_number

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # Scroll area for long license text
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                background: #222;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
        """)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignTop)
        container_layout.setSpacing(15)

        # Title
        title = QLabel("Settings")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        container_layout.addWidget(title)

        # Build + version + theme info (store as instance variable)
        current_theme = self.settings.value(APP_THEME_KEY, "Dark")
        self.info_label = QLabel(
            f"Version: {APP_VERSION}\n"
            f"Build Number: {APP_BUILD}\n"
            f"Current Theme: {current_theme}"
        )
        self.info_label.setStyleSheet("font-size: 14px;")
        container_layout.addWidget(self.info_label)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #555;")
        container_layout.addWidget(divider)

        # Creator & partnership
        creator = QLabel(
            "Created by SketeRAID\n"
            "In partnership with Binx2679\n\n"
            "Software and code are owned by SketeRAID.\n"
        )
        creator.setStyleSheet("font-size: 14px;")
        container_layout.addWidget(creator)

        # MIT License
        mit_title = QLabel("MIT License")
        mit_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        container_layout.addWidget(mit_title)

        mit_text = QLabel("""
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included 
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS 
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
THE SOFTWARE.
        """)
        mit_text.setStyleSheet("font-size: 12px;")
        mit_text.setWordWrap(True)
        container_layout.addWidget(mit_text)

        # GPLv3 License
        gpl_title = QLabel("GNU General Public License v3.0")
        gpl_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        container_layout.addWidget(gpl_title)

        gpl_text = QLabel("""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3 as 
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see https://www.gnu.org/licenses/.
        """)
        gpl_text.setStyleSheet("font-size: 12px;")
        gpl_text.setWordWrap(True)
        container_layout.addWidget(gpl_text)

        # CC BY-NC License
        cc_title = QLabel("Creative Commons BY‑NC 4.0")
        cc_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        container_layout.addWidget(cc_title)

        cc_text = QLabel("""
Creative Commons Attribution–NonCommercial 4.0 International (CC BY‑NC 4.0)

You are free to:
• Share — copy and redistribute the material in any medium or format
• Adapt — remix, transform, and build upon the material

Under the following terms:
• Attribution — You must give appropriate credit.
• NonCommercial — You may not use the material for commercial purposes.

No additional restrictions — You may not apply legal terms or technological 
measures that legally restrict others from doing anything the license permits.

Full license text: https://creativecommons.org/licenses/by-nc/4.0/
        """)
        cc_text.setStyleSheet("font-size: 12px;")
        cc_text.setWordWrap(True)
        container_layout.addWidget(cc_text)

        # Footer
        footer = QLabel(
            "© 2026 SketeRAID. All rights reserved.\n"
            "This software and all associated code belong to SketeRAID."
        )
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 12px; color: #888; margin-top: 20px;")
        container_layout.addWidget(footer)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    # NEW: Refresh method
    def refresh_theme_label(self):
        current_theme = self.settings.value(APP_THEME_KEY, "Dark")
        self.info_label.setText(
            f"Version: {APP_VERSION}\n"
            f"Build Number: {APP_BUILD}\n"
            f"Current Theme: {current_theme}"
        )