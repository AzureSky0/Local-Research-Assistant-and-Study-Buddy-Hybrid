from PySide6.QtWidgets import (
    QListWidget,
)


class DocumentListWidget(QListWidget):

    def __init__(self) -> None:
        super().__init__()

        self.addItem(
            "📚 No documents imported yet.\n"
            "Import PDFs or folders to start building your research library."
        )