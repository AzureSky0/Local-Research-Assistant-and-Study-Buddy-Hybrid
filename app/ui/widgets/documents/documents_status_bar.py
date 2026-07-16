from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
)


class DocumentsStatusBar(QWidget):

    def __init__(self) -> None:
        super().__init__()

        layout = QHBoxLayout(self)

        self.total_label = QLabel("Documents: 0")
        self.indexed_label = QLabel("Indexed: 0")
        self.failed_label = QLabel("Failed: 0")

        layout.addWidget(self.total_label)
        layout.addStretch()
        layout.addWidget(self.indexed_label)
        layout.addWidget(self.failed_label)