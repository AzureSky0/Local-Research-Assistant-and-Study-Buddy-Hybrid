from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
)


class DocumentSearchBar(QWidget):

    def __init__(self) -> None:
        super().__init__()

        layout = QHBoxLayout(self)

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search documents..."
        )

        layout.addWidget(self.search_input)