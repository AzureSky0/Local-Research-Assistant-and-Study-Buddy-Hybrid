from PySide6.QtWidgets import QLabel, QMainWindow
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        
        #Temperory we will change it to take values from system
        #(a single file containing all the project info like title dimention etc. )

        self.setWindowTitle(
            "Local Research Assistant + Study Buddy Hybrid"
        )
        self.resize(1200, 800)

        label = QLabel("Phase 1 started successfully.")
        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setCentralWidget(label)