import multiprocessing
import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel,
    QLineEdit, QTextEdit, QProgressBar, QHBoxLayout, QGridLayout, QScrollArea, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class ScraperWorker(QThread):
    progress_signal = pyqtSignal(int, int, int)  # worker_id, done, total
    log_signal = pyqtSignal(int, str)  # worker_id, log message
    finished_signal = pyqtSignal(int)

    def __init__(self, worker_id, batch):
        super().__init__()
        self.worker_id = worker_id
        self.batch = batch

    def run(self):
        driver = setup_driver()
        lyrics_list = []
        total = len(self.batch)
        done = 0

        for _, row in self.batch.iterrows():
            artist, track_name = row['artists'], row['track_name']
            search_query = f"{artist} {track_name} lyrics"
            driver.get("https://www.google.com/")
            
            try:
                element = wait(driver, 3).until(EC.visibility_of_element_located((By.NAME, 'q')))
                element.send_keys(search_query, Keys.ENTER)
                lyrics_elem = wait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@data-attrid="kc:/music/recording_cluster:lyrics"]'))
                )
                lyrics = lyrics_elem.text.split('翻译成中文')[0] if lyrics_elem.text else "Not Found"
            except:
                lyrics = "Not Found"
            
            lyrics_list.append(lyrics)
            done += 1
            self.progress_signal.emit(self.worker_id, done, total)
            self.log_signal.emit(self.worker_id, f"Processed {done}/{total} - {artist} - {track_name}")
        
        driver.quit()
        self.batch['lyrics'] = lyrics_list
        self.finished_signal.emit(self.worker_id)


def setup_driver():
    options = Options()
    options.add_experimental_option("detach", True)
    options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 1, "profile.managed_default_content_settings.images": 2})
    options.add_argument("--disable-infobars")
    options.page_load_strategy = 'eager'

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--remote-allow-origins=*")
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


class LyricsScraperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Lyrics Scraper")
        self.setGeometry(100, 100, 700, 500)
        layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit(self)
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.select_file)
        file_layout.addWidget(QLabel("CSV File:"))
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_button)
        layout.addLayout(file_layout)
        
        self.max_workers_input = QLineEdit("5", self)
        layout.addWidget(QLabel("Max Workers:"))
        layout.addWidget(self.max_workers_input)
        
        self.worker_grid = QGridLayout()
        self.worker_widgets = {}
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.worker_grid)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        self.start_button = QPushButton("Start Scraping", self)
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)
        
        self.setLayout(layout)
        self.workers = []

    def select_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV files (*.csv)")
        if filename:
            self.file_input.setText(filename)

    def start_scraping(self):
        input_path = self.file_input.text()
        max_workers = int(self.max_workers_input.text())
        
        if not input_path:
            return
        
        df = pd.read_csv(input_path)
        batch_size = len(df) // max_workers
        batches = [df.iloc[i:i+batch_size] for i in range(0, len(df), batch_size)]
        
        for i, batch in enumerate(batches):
            progress_bar = QProgressBar()
            progress_label = QLabel("0/0")
            log_box = QTextEdit()
            log_box.setReadOnly(True)
            
            self.worker_grid.addWidget(QLabel(f"Worker {i+1}"), i, 0)
            self.worker_grid.addWidget(progress_bar, i, 1)
            self.worker_grid.addWidget(progress_label, i, 2)
            self.worker_grid.addWidget(log_box, i, 3)
            
            self.worker_widgets[i] = (progress_bar, progress_label, log_box)
            
            worker = ScraperWorker(i, batch)
            worker.progress_signal.connect(self.update_worker_progress)
            worker.log_signal.connect(self.update_worker_log)
            worker.start()
            self.workers.append(worker)
    
    def update_worker_progress(self, worker_id, done, total):
        if worker_id in self.worker_widgets:
            progress_bar, progress_label, _ = self.worker_widgets[worker_id]
            progress_bar.setValue(int((done / total) * 100))
            progress_label.setText(f"{done}/{total}")
    
    def update_worker_log(self, worker_id, message):
        if worker_id in self.worker_widgets:
            _, _, log_box = self.worker_widgets[worker_id]
            log_box.append(message)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = LyricsScraperGUI()
    window.show()
    sys.exit(app.exec())