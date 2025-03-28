from PyQt5.QtWidgets import QMessageBox


def show_error_message(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(message)
    msg.setWindowTitle("Ошибка")
    msg.exec_()
