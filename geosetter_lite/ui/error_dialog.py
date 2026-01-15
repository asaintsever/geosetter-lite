"""
Error Dialog - Display ExifTool errors and warnings in a table
"""
from typing import List, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class ErrorDialog(QDialog):
    """Dialog for displaying ExifTool errors and warnings in a table"""
    
    def __init__(self, title: str, message: str, error_text: str, parent=None):
        """
        Initialize the error dialog
        
        Args:
            title: Dialog title
            message: Main message to display
            error_text: Error/warning text from ExifTool (may contain multiple lines)
            parent: Parent widget
        """
        super().__init__(parent)
        self.title = title
        self.message = message
        self.error_text = error_text
        
        self.setWindowTitle(title)
        self.setMinimumSize(800, 400)
        self.setModal(True)
        
        self.init_ui()
        self.populate_errors()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Header message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 10px;")
        layout.addWidget(message_label)
        
        # Error table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Type", "Message", "Context"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only
        self.table.setWordWrap(True)
        self.table.verticalHeader().setDefaultSectionSize(50)  # Taller rows for wrapping
        layout.addWidget(self.table)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setMinimumWidth(100)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def parse_errors(self) -> List[Tuple[str, str, str]]:
        """
        Parse error text into structured error items
        
        Returns:
            List of tuples (error_type, message, context)
        """
        errors = []
        lines = self.error_text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Determine error type based on keywords
            error_type = "Info"
            if "warning:" in line.lower():
                error_type = "Warning"
            elif "error:" in line.lower():
                error_type = "Error"
            elif "failed:" in line.lower() or "failed to" in line.lower():
                error_type = "Error"
            
            # Try to extract context (file path) from the line
            context = ""
            message = line
            
            # Look for common patterns like "- /path/to/file.jpg"
            # This handles multi-line errors where the path is on the last line
            if " - " in line and "/" in line:
                parts = line.rsplit(" - ", 1)
                if len(parts) == 2:
                    context = parts[1].strip()
                    # If this line has just the path, check if previous content is part of the message
                    if not parts[0].strip():
                        # Multi-line message - combine previous lines
                        message_parts = []
                        j = i - 1
                        while j >= 0 and lines[j].strip() and " - /" not in lines[j]:
                            message_parts.insert(0, lines[j].strip())
                            j -= 1
                        if message_parts:
                            message = " ".join(message_parts)
                        else:
                            message = context
                            context = ""
                    else:
                        message = parts[0].strip()
            
            # Remove error type prefix from message if present
            for prefix in ["Warning:", "Error:", "Failed:", "warning:", "error:", "failed:"]:
                if message.lower().startswith(prefix.lower()):
                    message = message[len(prefix):].strip()
                    break
            
            # Only add if we have a meaningful message
            if message:
                errors.append((error_type, message, context))
            
            i += 1
        
        return errors
    
    def populate_errors(self):
        """Populate the table with parsed errors"""
        errors = self.parse_errors()
        
        if not errors:
            # If no structured errors found, add the raw error text
            errors = [("Error", self.error_text, "")]
        
        self.table.setRowCount(len(errors))
        
        for row, (error_type, message, context) in enumerate(errors):
            # Type column
            type_item = QTableWidgetItem(error_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Color-code based on type
            if error_type == "Error":
                type_item.setBackground(QColor(255, 200, 200))  # Light red
            elif error_type == "Warning":
                type_item.setBackground(QColor(255, 250, 200))  # Light yellow
            else:
                type_item.setBackground(QColor(220, 240, 255))  # Light blue
            
            # Set text color to black for better readability
            type_item.setForeground(QColor(0, 0, 0))
            
            self.table.setItem(row, 0, type_item)
            
            # Message column
            message_item = QTableWidgetItem(message)
            self.table.setItem(row, 1, message_item)
            
            # Context column
            context_item = QTableWidgetItem(context)
            self.table.setItem(row, 2, context_item)
        
        # Resize rows to fit content
        self.table.resizeRowsToContents()


def show_exiftool_error(title: str, message: str, error_text: str, parent=None) -> int:
    """
    Show an error dialog with ExifTool errors/warnings in a table
    
    Args:
        title: Dialog title
        message: Main message to display
        error_text: Error/warning text from ExifTool
        parent: Parent widget
        
    Returns:
        Dialog result code
    """
    dialog = ErrorDialog(title, message, error_text, parent)
    return dialog.exec()
