import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QCheckBox, QFileDialog, \
    QInputDialog, QProgressBar, QLabel, QMessageBox, QTabWidget, QListWidgetItem, QMainWindow, \
    QDateTimeEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, \
    QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QDateTime, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from clustering import run_clustering
from graph_visualization import visualize_interactive_graph
from parsing import ParsingThread
from similarity import find_similar
from utils import show_error_message
from files import read_websites_file, clean_content
from vectorization import run_vectorization


class NewsParserApp(QMainWindow):
    tabs: QTabWidget

    sites_tab: QWidget
    site_layout: QVBoxLayout
    buttons_layout: QHBoxLayout
    checkbox_layout: QHBoxLayout
    site_list: QListWidget
    add_site_button: QPushButton
    delete_button: QPushButton
    edit_button: QPushButton

    parsing_tab: QWidget
    parsing_layout: QVBoxLayout
    parse_button: QPushButton
    clear_data_checkbox: QCheckBox
    select_all_checkbox: QCheckBox
    load_button: QPushButton
    datetime_picker: QDateTimeEdit
    parsing_thread: ParsingThread
    progress_bar: QProgressBar

    vectorization_tab: QWidget
    vectorization_layout: QVBoxLayout
    vectorization_methods: list
    vector_method_label: QLabel
    vector_method_combo: QComboBox
    vectorize_button: QPushButton
    vector_output: QTextEdit

    clustering_tab: QWidget
    clustering_layout: QVBoxLayout
    files_layout: QVBoxLayout
    cluster_methods: list
    cluster_method_label: QLabel
    cluster_method_combo: QComboBox
    num_clusters_label: QLabel
    cluster_method_combo: QComboBox
    num_clusters_label: QLabel
    num_clusters_spin: QSpinBox
    # cluster_button: QPushButton
    cluster_output: QTextEdit
    files_label: QLabel
    files_scroll: QScrollArea
    files_widget: QWidget
    files_checkboxes: list

    similarity_tab: QWidget
    similarity_layout: QVBoxLayout
    threshold_label: QLabel
    threshold_spin: QDoubleSpinBox
    find_similar_button: QPushButton
    similarity_output: QTableWidget

    graph_tab: QWidget
    graph_layout: QVBoxLayout
    draw_button: QPushButton
    graph_view: QWebEngineView
    graph_scene: QGraphicsScene

    is_parsing: bool

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Новостной парсер')
        self.setGeometry(1000, 450, 400, 500)

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.sites_tab = QWidget()
        self.tabs.addTab(self.sites_tab, "Сайты")
        self.init_sites_tab()

        self.parsing_tab = QWidget()
        self.tabs.addTab(self.parsing_tab, "Парсинг")
        self.init_parsing_tab()

        # self.vectorization_tab = QWidget()
        # self.tabs.addTab(self.vectorization_tab, "Векторизация")
        # self.init_vectorization_tab()

        # self.clustering_tab = QWidget()
        # self.tabs.addTab(self.clustering_tab, "Кластеризация")
        # self.init_clustering_tab()

        self.similarity_tab = QWidget()
        self.tabs.addTab(self.similarity_tab, "Схожие новости")
        self.init_similarity_tab()

        self.graph_tab = QWidget()
        self.tabs.addTab(self.graph_tab, "Граф сходства")
        self.init_graph_tab()

    def init_sites_tab(self):
        self.site_layout = QVBoxLayout(self.sites_tab)

        self.load_button = QPushButton("Загрузить список сайтов", self)
        # noinspection PyUnresolvedReferences
        self.load_button.clicked.connect(self.load_sites)
        self.site_layout.addWidget(self.load_button)

        self.add_site_button = QPushButton("Добавить сайт вручную", self)
        # noinspection PyUnresolvedReferences
        self.add_site_button.clicked.connect(self.add_site_manually)
        self.site_layout.addWidget(self.add_site_button)

        self.checkbox_layout = QHBoxLayout()

        self.select_all_checkbox = QCheckBox("Выбрать все сайты", self)
        # noinspection PyUnresolvedReferences
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all_sites)
        self.checkbox_layout.addWidget(self.select_all_checkbox)

        # self.only_selected_checkbox = QCheckBox("Только выбранные элементы", self)
        # self.only_selected_checkbox.stateChanged.connect(self.toggle_selection_mode)
        # self.checkbox_layout.addWidget(self.only_selected_checkbox)

        self.site_layout.addLayout(self.checkbox_layout)

        self.buttons_layout = QHBoxLayout()

        self.edit_button = QPushButton("Редактировать сайт", self)
        # noinspection PyUnresolvedReferences
        self.edit_button.clicked.connect(self.edit_selected_site)
        self.buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Удалить сайт", self)
        # noinspection PyUnresolvedReferences
        self.delete_button.clicked.connect(self.delete_selected_site)
        self.buttons_layout.addWidget(self.delete_button)

        self.site_layout.addLayout(self.buttons_layout)

        self.site_list = QListWidget()
        # noinspection PyUnresolvedReferences
        self.site_list.itemChanged.connect(self.on_item_changed)
        self.site_layout.addWidget(self.site_list)

    def init_parsing_tab(self):
        self.parsing_layout = QVBoxLayout(self.parsing_tab)
        self.parsing_layout.setAlignment(Qt.AlignTop)

        self.parse_button = QPushButton("Запустить парсинг", self)
        # noinspection PyUnresolvedReferences
        self.parse_button.clicked.connect(self.start_parsing)
        self.parsing_layout.addWidget(self.parse_button)

        # Прогресс бар
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.parsing_layout.addWidget(self.progress_bar)

        self.datetime_picker = QDateTimeEdit(self)
        self.datetime_picker.setDateTime(QDateTime.currentDateTime())  # Устанавливаем текущую дату по умолчанию
        self.datetime_picker.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.datetime_picker.setCalendarPopup(True)
        self.parsing_layout.addWidget(self.datetime_picker)

        self.clear_data_checkbox = QCheckBox("Обработать полученные данные", self)
        self.parsing_layout.addWidget(self.clear_data_checkbox)

    def init_vectorization_tab(self):
        self.vectorization_layout = QVBoxLayout()

        self.vector_method_label = QLabel("Метод векторизации:")
        self.vector_method_combo = QComboBox()
        # self.vectorization_methods = ["TF-IDF", "Word2Vec", "FastText"]
        self.vectorization_methods = ["TF-IDF"]
        self.vector_method_combo.addItems(self.vectorization_methods)

        self.vectorize_button = QPushButton("Запустить векторизацию")
        # noinspection PyUnresolvedReferences
        self.vectorize_button.clicked.connect(self.run_vectorization)

        self.vector_output = QTextEdit()
        self.vector_output.setReadOnly(True)

        self.vectorization_layout.addWidget(self.vector_method_label)
        self.vectorization_layout.addWidget(self.vector_method_combo)
        self.vectorization_layout.addWidget(self.vectorize_button)
        self.vectorization_layout.addWidget(self.vector_output)

        self.vectorization_tab.setLayout(self.vectorization_layout)

    def init_clustering_tab(self):
        pass

    def init_similarity_tab(self):
        self.clustering_layout = QVBoxLayout()

        self.vector_method_label = QLabel("Метод векторизации:")
        self.vector_method_combo = QComboBox()
        # self.vectorization_methods = ["TF-IDF", "Word2Vec", "FastText"]
        self.vectorization_methods = ["TF-IDF"]
        self.vector_method_combo.addItems(self.vectorization_methods)

        self.cluster_method_label = QLabel("Метод кластеризации:")
        self.cluster_method_combo = QComboBox()
        # self.cluster_methods = ["K-Means", "DBSCAN", "Agglomerative"]
        self.cluster_methods = ["K-Means"]
        self.cluster_method_combo.addItems(self.cluster_methods)

        self.files_label = QLabel("Выберите источники данных:")
        self.files_scroll = QScrollArea()
        self.files_scroll.setWidgetResizable(True)
        self.files_widget = QWidget()
        self.files_layout = QVBoxLayout(self.files_widget)
        self.files_checkboxes = []
        self.files_scroll.setWidget(self.files_widget)

        for file in os.listdir("data"):
            if file.startswith("news_") and file.endswith("_data_cleaned.json"):
                checkbox = QCheckBox(file)
                self.files_layout.addWidget(checkbox)
                self.files_checkboxes.append(checkbox)

        self.num_clusters_label = QLabel("Число кластеров:")
        self.num_clusters_spin = QSpinBox()
        self.num_clusters_spin.setRange(2, 100)
        self.num_clusters_spin.setValue(20)

        # self.cluster_button = QPushButton("Запустить кластеризацию")
        # noinspection PyUnresolvedReferences
        # self.cluster_button.clicked.connect(self.run_clustering)

        # self.cluster_output = QTextEdit()
        # self.cluster_output.setReadOnly(True)

        # self.clustering_layout.addWidget(self.cluster_output)
        # self.clustering_tab.setLayout(self.clustering_layout)

        self.similarity_layout = QVBoxLayout()

        self.threshold_label = QLabel("Порог сходства:")
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 1.0)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setValue(0.75)

        self.find_similar_button = QPushButton("Найти схожие новости")
        # noinspection PyUnresolvedReferences
        self.find_similar_button.clicked.connect(self.run_similarity)

        self.similarity_output = QTableWidget()
        self.similarity_output.setHorizontalHeaderLabels(["Новость 1", "Новость 2", "Сходство"])
        self.similarity_output.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.similarity_output.setEditTriggers(QTableWidget.NoEditTriggers)

        self.similarity_layout.addWidget(self.vector_method_label)
        self.similarity_layout.addWidget(self.vector_method_combo)
        self.similarity_layout.addWidget(self.cluster_method_label)
        self.similarity_layout.addWidget(self.cluster_method_combo)
        self.similarity_layout.addWidget(self.num_clusters_label)
        self.similarity_layout.addWidget(self.num_clusters_spin)
        # self.similarity_layout.addWidget(self.cluster_button)
        self.similarity_layout.addWidget(self.files_label)
        self.similarity_layout.addWidget(self.files_scroll)

        self.similarity_layout.addWidget(self.threshold_label)
        self.similarity_layout.addWidget(self.threshold_spin)
        self.similarity_layout.addWidget(self.find_similar_button)
        self.similarity_layout.addWidget(self.similarity_output)
        self.similarity_tab.setLayout(self.similarity_layout)

    def init_graph_tab(self):
        self.graph_layout = QVBoxLayout(self.graph_tab)
        self.graph_scene = QGraphicsScene(self)

        self.graph_view = QWebEngineView()
        # self.graph_view.linkClicked.connect(self.handle_link_click)

        self.draw_button = QPushButton("Построить граф")
        # noinspection PyUnresolvedReferences
        self.draw_button.clicked.connect(self.draw_graph)

        self.graph_layout.addWidget(self.graph_view)
        self.graph_layout.addWidget(self.draw_button)

    def add_site_to_list(self, site_url):
        item = QListWidgetItem(site_url)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        self.site_list.addItem(item)

    def load_sites(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Загрузить файл", "", "TXT Files (*.txt);;All Files (*)")

        if not file_name:
            return

        try:
            sites = read_websites_file(file_name)

            if not isinstance(sites, list):
                QMessageBox.warning(self, "Ошибка", "Файл должен содержать список сайтов.")
                return

            self.site_list.clear()
            for site in sites:
                self.add_site_to_list(site)

            QMessageBox.information(self, "Успешно", f"Загружено {len(sites)} сайтов.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке файла:\n{e}")

    def add_site_manually(self):
        url, ok = QInputDialog.getText(self, "Добавить сайт", "Введите ссылку на сайт:")
        if ok and url:
            self.add_site_to_list(url)

    def toggle_select_all_sites(self):
        if self.select_all_checkbox.isChecked():
            for i in range(self.site_list.count()):
                item = self.site_list.item(i)
                item.setCheckState(Qt.Checked)
        # else:
        #     for i in range(self.site_list.count()):
        #         item = self.site_list.item(i)
        #         item.setCheckState(Qt.Unchecked)

    # def toggle_selection_mode(self):
    #     if self.only_selected_checkbox.isChecked():
    #         for i in range(self.site_list.count()):
    #             item = self.site_list.item(i)
    #             item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
    #         self.select_all_checkbox.setChecked(False)
    #     else:
    #         for i in range(self.site_list.count()):
    #             item = self.site_list.item(i)
    #             item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)

    def start_parsing(self):
        self.is_parsing = True
        cutoff_datetime = self.datetime_picker.dateTime()
        selected_sites = [self.site_list.item(i).text() for i in range(self.site_list.count()) if
                          self.site_list.item(i).checkState() == Qt.Checked]

        if not selected_sites:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один сайт для парсинга.")
            return

        self.progress_bar.setValue(0)
        self.parsing_thread = ParsingThread(selected_sites, cutoff_datetime)
        self.parsing_thread.progress_updated.connect(self.progress_bar.setValue)
        self.parsing_thread.parsing_finished.connect(self.on_parsing_finished)

        self.parse_button.setDisabled(True)
        self.datetime_picker.setDisabled(True)
        self.clear_data_checkbox.setDisabled(True)
        self.parsing_thread.start()
        if self.clear_data_checkbox.isChecked():
            clean_content()

    def on_parsing_finished(self):
        self.is_parsing = False
        self.parse_button.setEnabled(True)
        self.datetime_picker.setEnabled(True)
        self.clear_data_checkbox.setEnabled(True)
        QMessageBox.information(self, "Готово", "Парсинг завершен!")

    def edit_selected_site(self):
        selected_items = self.site_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            new_url, ok = QInputDialog.getText(self, "Редактировать сайт", "Введите новую ссылку:", text=item.text())
            if ok and new_url:
                item.setText(new_url)
        else:
            show_error_message("Не выбран сайт для редактирования.")

    def delete_selected_site(self):
        selected_items = self.site_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.site_list.takeItem(self.site_list.row(item))
        else:
            show_error_message("Не выбран сайт для удаления.")

    def on_item_changed(self):
        all_checked = True
        for row in range(self.site_list.count()):
            item = self.site_list.item(row)
            if item.checkState() == Qt.Unchecked:
                all_checked = False
                break
        if all_checked:
            self.select_all_checkbox.setChecked(True)
        else:
            self.select_all_checkbox.setChecked(False)

    def run_vectorization(self, files):
        news_data, tfidf_matrix, vectorizer = run_vectorization(vectorization_method=self.vector_method_combo.currentText(),
                                                                files=files)
        return news_data, tfidf_matrix, vectorizer

    def run_clustering(self):
        selected_files = list()
        for sf in self.files_checkboxes:
            if sf.isChecked():
                selected_files.append(sf.text())
        if len(selected_files) < 2:
            QMessageBox.warning(self, "Ошибка", "Нужно выбрать минимум два файла для кластеризации.")
            return None
        else:
            news_data, tfidf_matrix, vectorizer = self.run_vectorization(files=selected_files)
            cluster_labels = run_clustering(tfidf_matrix, num_clusters=self.num_clusters_spin.value(),
                                            clustering_method=self.cluster_method_combo.currentText())
            return news_data, tfidf_matrix, cluster_labels

    def run_similarity(self):
        result = self.run_clustering()
        if result is not None:
            threshold = self.threshold_spin.value()
            self.graph, self.edges, result_text = find_similar(news_data=result[0], tfidf_matrix=result[1],
                                                               cluster_labels=result[2], threshold=threshold)
            self.edges = sorted(self.edges, key=lambda x: x[2], reverse=True)
            self.similarity_output.setRowCount(len(self.edges))
            self.similarity_output.setColumnCount(3)
            for row, (news1, news2, similarity) in enumerate(self.edges):
                self.similarity_output.setItem(row, 0, QTableWidgetItem(news1))
                self.similarity_output.setItem(row, 1, QTableWidgetItem(news2))
                self.similarity_output.setItem(row, 2, QTableWidgetItem(f"{similarity:.2f}"))

    def draw_graph(self):
        output_path = "data/graph.html"
        # result_graph = self.run_clustering()[0]  # Получаем результат кластеризации
        visualize_interactive_graph(self.graph, self.edges, output_path)

        # Загружаем сохраненный HTML файл в QWebEngineView
        self.graph_view.setUrl(QUrl.fromLocalFile(os.path.abspath(output_path)))

