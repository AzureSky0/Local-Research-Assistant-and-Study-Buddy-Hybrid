from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout

class SettingsPage(QWidget):

    def __init__(self) -> None:
        super().__init__()
        
        layout = QVBoxLayout()

        title = QLabel("Setting Page")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)

        self.setLayout(layout)
