from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.theme import tokens as t
from app.ui.widgets.common import button, hbox, label, vbox
from app.workspace.domain.workspace import Workspace

MAX_NAME_LENGTH = 100  # matches the database column


@dataclass(frozen=True, slots=True)
class WorkspaceFormData:
    name: str
    description: str
    color: str


class WorkspaceDialog(QDialog):
    """Create a workspace, or edit an existing one."""

    def __init__(
        self,
        parent: QWidget | None = None,
        workspace: Workspace | None = None,
    ) -> None:
        super().__init__(parent)
        editing = workspace is not None

        self.setWindowTitle("Edit workspace" if editing else "New workspace")
        self.setModal(True)
        self.setMinimumWidth(520)

        title = label(self.windowTitle(), "dialogTitle")
        intro = label(
            "A workspace holds the documents for one project or subject.",
            "muted",
            wrap=True,
        )

        self._name = QLineEdit(workspace.name if workspace else "")
        self._name.setProperty("size", "large")
        self._name.setMaxLength(MAX_NAME_LENGTH)
        self._name.setPlaceholderText("For example: Machine Learning")
        self._name.textChanged.connect(self._update_create_button)

        self._description = QLineEdit((workspace.description or "") if workspace else "")
        self._description.setProperty("size", "large")
        self._description.setPlaceholderText("For example: Course papers and lecture notes")

        name_label = label("Name")
        name_label.setStyleSheet("font-weight: 500;")
        name_label.setBuddy(self._name)

        description_label = label("Description (optional)")
        description_label.setStyleSheet("font-weight: 500;")
        description_label.setBuddy(self._description)

        color_label = label("Color")
        color_label.setStyleSheet("font-weight: 500;")

        self._colors = QButtonGroup(self)
        self._colors.setExclusive(True)
        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(10)

        selected_color = workspace.color if workspace else t.DEFAULT_WORKSPACE_COLOR

        for key, swatch in t.WORKSPACE_COLORS.items():
            swatch_button = QPushButton()
            swatch_button.setProperty("variant", "swatch")
            swatch_button.setProperty("colorKey", key)
            swatch_button.setCheckable(True)
            swatch_button.setChecked(key == selected_color)
            swatch_button.setToolTip(swatch.label)
            swatch_button.setAccessibleName(f"{swatch.label} color")
            swatch_button.setCursor(Qt.CursorShape.PointingHandCursor)
            swatch_button.setStyleSheet(
                f"QPushButton {{ background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, "
                f"fx:0.5, fy:0.5, stop:0 {swatch.color}, stop:0.4 {swatch.color}, "
                f"stop:0.42 {swatch.tint}, stop:1 {swatch.tint}); }}"
            )
            self._colors.addButton(swatch_button)
            swatch_row.addWidget(swatch_button)

        swatch_row.addStretch(1)

        cancel = button("Cancel", "secondary")
        cancel.clicked.connect(self.reject)

        self._submit = button("Save" if editing else "Create workspace", "primary")
        self._submit.setDefault(True)
        self._submit.clicked.connect(self.accept)

        footer = hbox(
            label("You can change this later.", "small") if not editing else None,
            1,
            cancel,
            self._submit,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(22)
        layout.addLayout(vbox(title, intro, spacing=6))
        layout.addLayout(vbox(name_label, self._name, spacing=8))
        layout.addLayout(vbox(description_label, self._description, spacing=8))
        layout.addLayout(vbox(color_label, swatch_row, spacing=10))
        layout.addLayout(footer)

        self._update_create_button()
        self._name.setFocus()

    def form_data(self) -> WorkspaceFormData:
        checked = self._colors.checkedButton()
        color = checked.property("colorKey") if checked else t.DEFAULT_WORKSPACE_COLOR

        return WorkspaceFormData(
            name=self._name.text().strip(),
            description=self._description.text().strip(),
            color=str(color),
        )

    def _update_create_button(self) -> None:
        self._submit.setEnabled(bool(self._name.text().strip()))
