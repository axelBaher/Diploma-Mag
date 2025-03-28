import sys
from PyQt5.QtWidgets import QApplication
from ui_components import NewsParserApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NewsParserApp()
    window.show()
    sys.exit(app.exec_())
