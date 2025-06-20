QSS_STYLES = """
QMainWindow {
    background-color: #2e2e2e;
    color: #f0f0f0;
}

QFrame#HeaderFrame {
    background-color: #3a3a3a;
    border-bottom: 1px solid #505050;
}

QLabel#TitleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#FioStatusLabel {
    font-size: 14px;
    font-weight: bold;
}

QFrame#CardFrame {
    background-color: #3a3a3a;
    border: 1px solid #505050;
    border-radius: 8px;
    margin: 10px;
}

QLabel#CardTitleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 10px;
}

QComboBox {
    background-color: #4a4a4a;
    color: #f0f0f0;
    border: 1px solid #505050;
    border-radius: 4px;
    padding: 5px;
}

QComboBox::drop-down {
    border: 0px;
}

QComboBox::down-arrow {
    image: url(./resources/down_arrow.png); /* Placeholder for an actual arrow icon */
}

QPushButton {
    background-color: #007bff;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
    font-size: 16px;
}

QPushButton:hover {
    background-color: #0056b3;
}

QPushButton:disabled {
    background-color: #6c757d;
    color: #cccccc;
}

QProgressBar {
    text-align: center;
    color: #f0f0f0;
    background-color: #4a4a4a;
    border: 1px solid #505050;
    border-radius: 5px;
}

QProgressBar::chunk {
    background-color: #28a745;
    border-radius: 5px;
}

QLabel#LogOutputLabel, QLabel#ResultsTextLabel, QTextEdit#LogOutputLabel, QTextEdit#ResultsTextLabel {
    background-color: #2e2e2e;
    color: #f0f0f0;
    border: 1px solid #505050;
    padding: 15px;
    border-radius: 8px;
    font-family: "Monaco", "Menlo", "Courier New", "monospace";
    font-size: 13px;
    line-height: 1.6;
}

QLabel#ProfileDescription {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    font-size: 13px;
    color: #495057;
    line-height: 1.5;
    margin: 5px 0px;
}

QTextEdit#LogOutputLabel {
    font-size: 12px;
    line-height: 1.4;
    padding: 12px;
}

QTextEdit#ResultsTextLabel {
    font-size: 12px;
    line-height: 1.4;
    padding: 12px;
    font-family: "SF Mono", "Monaco", "Menlo", "Courier New", "monospace";
}

QTextEdit {
    selection-background-color: #4a4a4a;
    selection-color: #ffffff;
}

pg.PlotWidget {
    border: 1px solid #505050;
    border-radius: 5px;
}
"""
