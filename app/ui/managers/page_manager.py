from PySide6.QtWidgets import QStackedWidget, QWidget


class PageManager:
    def __init__(self):
        self.stack = QStackedWidget()
        self.pages = {}

    def register_page(
        self,
        name: str,
        widget: QWidget
    ) -> None:
        self.pages[name] = widget
        self.stack.addWidget(widget)

    def show_page(self, name: str) -> None:
        self.stack.setCurrentWidget(
            self.pages[name]
        )