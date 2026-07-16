from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout

class ResearchPage(QWidget):

    def __init__(self) -> None:
        super().__init__()
        
        layout = QVBoxLayout()

        title = QLabel("Research Page")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)

        self.setLayout(layout)
