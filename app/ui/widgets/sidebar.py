from PySide6.QtWidgets import QListWidget


class Sidebar(QListWidget):
    def __init__(self) -> None:
        super().__init__()

        #add all the pages 
        self.addItem("Documents")
        self.addItem("Research")
        self.addItem("Study Tools")
        self.addItem("Settings")

        self.setFixedWidth(180)

        self.setCurrentRow(0)