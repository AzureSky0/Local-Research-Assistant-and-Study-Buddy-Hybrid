from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
)


class DocumentsToolbar(QWidget):

    def __init__(self) -> None:
        super().__init__()

        layout = QHBoxLayout(self)

        self.import_files_button = QPushButton("Import Files")
        self.import_folder_button = QPushButton("Import Folder")
        self.refresh_button = QPushButton("Refresh")

        layout.addWidget(self.import_files_button)
        layout.addWidget(self.import_folder_button)
        layout.addStretch()
        layout.addWidget(self.refresh_button)