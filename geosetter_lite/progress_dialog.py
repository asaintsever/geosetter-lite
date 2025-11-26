"""Progress dialog for AI processing operations"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal


class ProgressDialog(QDialog):
    """Modal dialog showing progress for AI operations"""
    
    cancel_requested = Signal()
    
    def __init__(self, title="Processing", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Prevent closing with X button
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.CustomizeWindowHint | 
            Qt.WindowType.WindowTitleHint
        )
        
        self._cancelled = False
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Detail label (optional, for additional info)
        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.detail_label)
        
        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def set_status(self, message: str):
        """Update the status message"""
        self.status_label.setText(message)
    
    def set_detail(self, message: str):
        """Update the detail message"""
        self.detail_label.setText(message)
    
    def set_progress(self, current: int, total: int):
        """Update progress bar
        
        Args:
            current: Current item number (0-based or 1-based)
            total: Total number of items
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            
            # Update status with count
            if current < total:
                self.set_status(f"Processing image {current}/{total}...")
            else:
                self.set_status(f"Completed {total}/{total} images")
    
    def set_indeterminate(self, indeterminate: bool = True):
        """Set progress bar to indeterminate mode"""
        if indeterminate:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(0)
        else:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self._cancelled = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancelling...")
        self.set_status("Cancelling operation...")
        self.cancel_requested.emit()
    
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested"""
        return self._cancelled
    
    def reset(self):
        """Reset the dialog to initial state"""
        self._cancelled = False
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        self.progress_bar.setValue(0)
        self.set_status("Initializing...")
        self.set_detail("")

