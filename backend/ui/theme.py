"""
Protheon UI Theme definitions.
"""
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt

class Colors:
    BG_BASE = "#0D1117"       # Main background
    BG_PANEL = "#161B22"      # Cards / Panels
    BG_PANEL_HOVER = "#21262D"
    
    TEXT_MAIN = "#E6EDF3"
    TEXT_MUTED = "#7D8590"
    
    ACCENT = "#3bbfa6"        # Information / Selected / Cyan
    GREEN = "#238636"         # Healthy / Connected / Running
    AMBER = "#D29922"         # Warning
    RED = "#d64455"           # Fault / Emergency
    GRAY = "#30363D"          # Inactive

    BORDER = "#30363D"

class Typography:
    FAMILY = "Inter, -apple-system, sans-serif"
    MONO_FAMILY = "JetBrains Mono, Consolas, monospace"

    @classmethod
    def get_font(cls, size, bold=False, mono=False):
        f = QFont(cls.MONO_FAMILY if mono else cls.FAMILY, size)
        f.setBold(bold)
        return f

    @classmethod
    def app_title(cls): return cls.get_font(20, bold=True)
    @classmethod
    def page_title(cls): return cls.get_font(24, bold=True)
    @classmethod
    def section_title(cls): return cls.get_font(16, bold=True)
    @classmethod
    def body(cls): return cls.get_font(13)
    @classmethod
    def metadata(cls): return cls.get_font(11, mono=True)

GLOBAL_STYLESHEET = f"""
QWidget {{
    background-color: {Colors.BG_BASE};
    color: {Colors.TEXT_MAIN};
    font-family: {Typography.FAMILY};
    font-size: 13px;
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    border: none;
    background: {Colors.BG_BASE};
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {Colors.BORDER};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    border: none;
    background: {Colors.BG_BASE};
    height: 10px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {Colors.BORDER};
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QSplitter::handle {{
    background-color: {Colors.BORDER};
    margin: 2px;
}}
QGroupBox {{
    border: 1px solid {Colors.BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 10px;
    background-color: {Colors.BG_PANEL};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    left: 8px;
    color: {Colors.TEXT_MUTED};
    font-weight: bold;
}}
QLabel {{
    background-color: transparent;
}}
"""
