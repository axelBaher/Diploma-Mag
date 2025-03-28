import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QLabel, QCheckBox, QSplitter, QListWidgetItem, QInputDialog, QMessageBox, QTabWidget
from PyQt5.QtCore import Qt

class NewsParserApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Инициализация интерфейса
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Новостной парсер')
        self.setGeometry(300, 200, 800, 600)

        # Центральный виджет
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Создаем TabWidget для вкладок
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        # Вкладка 1: Управление сайтами
        self.sites_tab = QWidget()
        self.tabs.addTab(self.sites_tab, "Сайты")

        # Вкладка 2: Парсинг сайтов
        self.parsing_tab = QWidget()
        self.tabs.addTab(self.parsing_tab, "Парсинг")

        # Инициализация первой вкладки
        self.init_sites_tab()

        # Инициализация второй вкладки
        self.init_parsing_tab()

    def init_sites_tab(self):
        # Основной layout для вкладки сайтов
        self.site_layout = QVBoxLayout(self.sites_tab)

        # Заголовок
        self.header_label = QLabel("Парсинг новостей по сайтам", self)
        self.site_layout.addWidget(self.header_label)

        # Кнопка для загрузки списка сайтов из файла
        self.load_button = QPushButton("Загрузить список сайтов", self)
        self.load_button.clicked.connect(self.load_sites)
        self.site_layout.addWidget(self.load_button)

        # Кнопка для добавления нового сайта вручную
        self.add_site_button = QPushButton("Добавить сайт вручную", self)
        self.add_site_button.clicked.connect(self.add_site_manually)
        self.site_layout.addWidget(self.add_site_button)

        # Чекбоксы для выбора режимов
        self.checkbox_layout = QHBoxLayout()

        # Чекбокс для выбора всех элементов
        self.select_all_checkbox = QCheckBox("Выбрать все сайты", self)
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all_sites)
        self.checkbox_layout.addWidget(self.select_all_checkbox)

        # Чекбокс для переключения между режимами: все сайты или только выбранные
        self.only_selected_checkbox = QCheckBox("Только выбранные элементы", self)
        self.only_selected_checkbox.stateChanged.connect(self.toggle_selection_mode)
        self.checkbox_layout.addWidget(self.only_selected_checkbox)

        # Добавляем чекбоксы в layout вкладки
        self.site_layout.addLayout(self.checkbox_layout)

        # Создаем QSplitter для изменения высоты части с сайтом
        self.splitter = QSplitter(Qt.Vertical)

        # Список сайтов для парсинга
        self.site_list = QListWidget(self)

        # Пример добавления сайтов
        self.add_site_to_list("https://example1.com")
        self.add_site_to_list("https://example2.com")
        self.add_site_to_list("https://example3.com")

        # Добавляем список сайтов в QSplitter
        self.splitter.addWidget(self.site_list)

        # Добавляем QSplitter в основной layout
        self.site_layout.addWidget(self.splitter)

        # Кнопки для удаления и редактирования сайта
        self.buttons_layout = QHBoxLayout()

        self.edit_button = QPushButton("Редактировать сайт", self)
        self.edit_button.clicked.connect(self.edit_selected_site)
        self.buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Удалить сайт", self)
        self.delete_button.clicked.connect(self.delete_selected_site)
        self.buttons_layout.addWidget(self.delete_button)

        # Добавляем кнопки в основной layout вкладки
        self.site_layout.addLayout(self.buttons_layout)

        # Устанавливаем режим "Все сайты" по умолчанию
        self.select_all_checkbox.setChecked(True)
        self.only_selected_checkbox.setChecked(False)

    def init_parsing_tab(self):
        # Основной layout для вкладки парсинга
        self.parsing_layout = QVBoxLayout(self.parsing_tab)

        # Заголовок
        self.parsing_label = QLabel("Запуск парсинга сайтов", self)
        self.parsing_layout.addWidget(self.parsing_label)

        # Кнопка для запуска парсинга
        self.parse_button = QPushButton("Запустить парсинг", self)
        self.parse_button.clicked.connect(self.start_parsing)
        self.parsing_layout.addWidget(self.parse_button)

    def add_site_to_list(self, site_url):
        """Функция для добавления сайта в список с чекбоксом"""
        item = QListWidgetItem(site_url)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # Устанавливаем флаг для чекбокса
        item.setCheckState(Qt.Unchecked)  # Чекбокс не выбран по умолчанию
        self.site_list.addItem(item)

    def load_sites(self):
        """Заглушка для загрузки списка сайтов из файла"""
        file_name, _ = QFileDialog.getOpenFileName(self, "Загрузить файл", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            # Тут будет логика для загрузки данных из файла
            print(f"Загружен файл: {file_name}")

    def add_site_manually(self):
        """Функция для добавления сайта вручную"""
        # Окно ввода ссылки
        url, ok = QInputDialog.getText(self, "Добавить сайт", "Введите ссылку на сайт:")
        if ok and url:
            self.add_site_to_list(url)

    def toggle_select_all_sites(self):
        """Переключение состояния выбора всех сайтов"""
        if self.select_all_checkbox.isChecked():
            # Выбираем все сайты в списке
            for i in range(self.site_list.count()):
                item = self.site_list.item(i)
                item.setSelected(True)
                item.setCheckState(Qt.Checked)  # Устанавливаем галочку
            # Отключаем чекбокс "Только выбранные элементы"
            self.only_selected_checkbox.setChecked(False)
        else:
            # Снимаем выделение со всех сайтов
            for i in range(self.site_list.count()):
                item = self.site_list.item(i)
                item.setCheckState(Qt.Unchecked)  # Убираем галочку
                item.setSelected(False)

    def toggle_selection_mode(self):
        """Переключение между режимами: все сайты или только выбранные"""
        if self.only_selected_checkbox.isChecked():
            print("Режим: только выбранные сайты")
            # Включаем чекбоксы для выбора сайтов
            for i in range(self.site_list.count()):
                item = self.site_list.item(i)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # Включаем чекбокс
            # Отключаем чекбокс "Выбрать все сайты"
            self.select_all_checkbox.setChecked(False)
        else:
            print("Режим: все сайты")
            # Отключаем чекбоксы для выбора сайтов
            for i in range(self.site_list.count()):
                item = self.site_list.item(i)
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)  # Убираем чекбокс

    def start_parsing(self):
        """Запуск парсинга с выбранными сайтами"""
        if self.only_selected_checkbox.isChecked():
            selected_sites = [self.site_list.item(i).text() for i in range(self.site_list.count()) if self.site_list.item(i).checkState() == Qt.Checked]
            print(f"Парсинг выбранных сайтов: {selected_sites}")
        else:
            # Парсим все сайты
            all_sites = [self.site_list.item(i).text() for i in range(self.site_list.count())]
            print(f"Парсинг всех сайтов: {all_sites}")

    def edit_selected_site(self):
        """Редактирование выбранного сайта"""
        selected_items = self.site_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            new_url, ok = QInputDialog.getText(self, "Редактировать сайт", "Введите новую ссылку:", text=item.text())
            if ok and new_url:
                item.setText(new_url)
        else:
            self.show_error_message("Не выбран сайт для редактирования.")

    def delete_selected_site(self):
        """Удаление выбранного сайта"""
        selected_items = self.site_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.site_list.takeItem(self.site_list.row(item))  # Удаляем элемент
        else:
            self.show_error_message("Не выбран сайт для удаления.")

    def show_error_message(self, message):
        """Показ сообщения об ошибке"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Ошибка")
        msg.exec_()

# Запуск приложения
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NewsParserApp()
    window.show()
    sys.exit(app.exec_())
