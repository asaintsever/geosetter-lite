"""
Date/Time Shift Dialog - Shift date/time of photos
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QSpinBox, QGroupBox
)

class DateTimeShiftDialog(QDialog):
    """Dialog for shifting date/time of photos"""

    def __init__(self, parent=None):
        """
        Initialize the date/time shift dialog
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.time_shift = {}
        self.operation = None  # 'increase' or 'decrease'

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Date/Time Shift")
        self.setMinimumSize(400, 250)

        layout = QVBoxLayout()

        # Time shift input group
        shift_group = QGroupBox("Time Shift Amount")
        grid_layout = QGridLayout()

        # Input fields for time shift
        self.years_spin = QSpinBox()
        self.months_spin = QSpinBox()
        self.days_spin = QSpinBox()
        self.hours_spin = QSpinBox()
        self.minutes_spin = QSpinBox()
        self.seconds_spin = QSpinBox()

        # Set ranges for spin boxes
        for spin_box in [self.years_spin, self.months_spin, self.days_spin,
                         self.hours_spin, self.minutes_spin, self.seconds_spin]:
            spin_box.setRange(0, 9999)
            spin_box.setFixedWidth(100)

        grid_layout.addWidget(QLabel("Years:"), 0, 0)
        grid_layout.addWidget(self.years_spin, 0, 1)
        grid_layout.addWidget(QLabel("Months:"), 1, 0)
        grid_layout.addWidget(self.months_spin, 1, 1)
        grid_layout.addWidget(QLabel("Days:"), 2, 0)
        grid_layout.addWidget(self.days_spin, 2, 1)
        grid_layout.addWidget(QLabel("Hours:"), 0, 2)
        grid_layout.addWidget(self.hours_spin, 0, 3)
        grid_layout.addWidget(QLabel("Minutes:"), 1, 2)
        grid_layout.addWidget(self.minutes_spin, 1, 3)
        grid_layout.addWidget(QLabel("Seconds:"), 2, 2)
        grid_layout.addWidget(self.seconds_spin, 2, 3)

        shift_group.setLayout(grid_layout)
        layout.addWidget(shift_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        self.decrease_button = QPushButton("Decrease")
        self.decrease_button.clicked.connect(self.decrease_date_time)
        button_layout.addWidget(self.decrease_button)

        self.increase_button = QPushButton("Increase")
        self.increase_button.setDefault(True)
        self.increase_button.clicked.connect(self.increase_date_time)
        button_layout.addWidget(self.increase_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_time_shift(self):
        """
        Get the time shift values from the dialog
        
        Returns:
            A tuple containing the time shift dictionary and the operation ('increase' or 'decrease')
        """
        self.time_shift = {
            'years': self.years_spin.value(),
            'months': self.months_spin.value(),
            'days': self.days_spin.value(),
            'hours': self.hours_spin.value(),
            'minutes': self.minutes_spin.value(),
            'seconds': self.seconds_spin.value()
        }
        return self.time_shift, self.operation

    def increase_date_time(self):
        """Set operation to 'increase' and accept the dialog"""
        if self._is_input_valid():
            self.operation = 'increase'
            self.accept()

    def decrease_date_time(self):
        """Set operation to 'decrease' and accept the dialog"""
        if self._is_input_valid():
            self.operation = 'decrease'
            self.accept()
            
    def _is_input_valid(self):
        """Check if at least one spinbox has a value."""
        return any(spinbox.value() > 0 for spinbox in [
            self.years_spin, self.months_spin, self.days_spin,
            self.hours_spin, self.minutes_spin, self.seconds_spin
        ])

