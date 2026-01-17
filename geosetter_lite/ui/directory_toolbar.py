"""
Directory Toolbar - Browse and select directories
"""
from pathlib import Path
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import Signal, Qt


class DirectoryToolbar(QWidget):
    """Toolbar widget for browsing and selecting directories"""
    
    directory_changed = Signal(Path)  # Emitted when a new directory is selected
    
    def __init__(self, initial_directory: Path, parent=None):
        """
        Initialize the directory toolbar
        
        Args:
            initial_directory: Initial directory path to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.current_directory = initial_directory
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Read-only line edit showing current path
        self.path_field = QLineEdit()
        self.path_field.setReadOnly(True)
        self.path_field.setText(str(self.current_directory))
        self.path_field.setPlaceholderText("No directory selected")
        
        # Browse button with folder icon
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setToolTip("Select a directory to browse")
        self.browse_button.clicked.connect(self._on_browse_clicked)
        
        # Add widgets to layout
        layout.addWidget(self.path_field, stretch=1)
        layout.addWidget(self.browse_button)
    
    def _on_browse_clicked(self):
        """Handle browse button click - open directory selection dialog"""
        # Open directory selection dialog
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            str(self.current_directory),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if selected_dir:
            new_path = Path(selected_dir)
            if new_path != self.current_directory:
                self.set_directory(new_path)
                self.directory_changed.emit(new_path)
    
    def set_directory(self, directory: Path):
        """
        Set the current directory and update the display
        
        Args:
            directory: New directory path
        """
        self.current_directory = directory
        self.path_field.setText(str(directory))
    
    def get_directory(self) -> Path:
        """
        Get the current directory
        
        Returns:
            Current directory path
        """
        return self.current_directory
