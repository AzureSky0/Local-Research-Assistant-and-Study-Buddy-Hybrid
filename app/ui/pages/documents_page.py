from app.ui.pages.base_page import BasePage
from app.ui.widgets.documents import (
    DocumentsToolbar,
    DocumentSearchBar,
    DocumentListWidget,
    DocumentsStatusBar,
)

class DocumentsPage(BasePage):
    def __init__(self):
        super().__init__("Documents")
        
        self.toolbar = DocumentsToolbar()
        self.search_bar = DocumentSearchBar()
        self.document_list = DocumentListWidget()
        self.status_bar = DocumentsStatusBar()

        self.content_layout.addWidget(self.toolbar)
        self.content_layout.addWidget(self.search_bar)
        self.content_layout.addWidget(self.document_list,1)
        self.content_layout.addWidget(self.status_bar)