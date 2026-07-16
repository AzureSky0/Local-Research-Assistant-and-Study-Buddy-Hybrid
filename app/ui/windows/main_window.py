from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.ui.pages.documents_page import DocumentsPage
from app.ui.pages.research_page import ResearchPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.study_page import StudyPage
from app.ui.widgets.sidebar import Sidebar
from app.database.init_db import initialize_database



class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()


        initialize_database()   

        self.setWindowTitle(
            "Local Research Assistant + Study Buddy Hybrid"
        )

        self.resize(1200, 800)

        central_widget = QWidget()
        layout = QHBoxLayout()

        self.sidebar = Sidebar()

        # will create a seperate file that will contain all variable related to pages 
        # if there is a  need for that or if this script becomes unnecessory big
        
        self.pages = QStackedWidget()

        self.pages.addWidget(DocumentsPage())
        self.pages.addWidget(ResearchPage())
        self.pages.addWidget(StudyPage())
        self.pages.addWidget(SettingsPage())

        self.sidebar.currentRowChanged.connect(
            self.pages.setCurrentIndex
        )

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages)

        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)