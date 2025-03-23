import os
import sys
import multiprocessing
import pandas as pd
import traceback

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel,
    QLineEdit, QTextEdit, QProgressBar, QHBoxLayout, QGridLayout, QScrollArea,
    QMessageBox, QComboBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def log_error(error_msg: str):
    """Log error messages to error_log.txt"""
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write(error_msg + "\n")


def sanitize_filename(name):
    """Remove illegal characters to ensure filename validity"""
    try:
        return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()
    except Exception as e:
        log_error(f"sanitize_filename error: {e}\n{traceback.format_exc()}")
        return "unknown"


def setup_driver():
    try:
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 1,
            "profile.managed_default_content_settings.images": 2
        })
        options.add_argument("--disable-infobars")
        options.page_load_strategy = 'eager'
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--remote-allow-origins=*")
        options.add_argument("--disable-blink-features=AutomationControlled")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        log_error(f"setup_driver error: {e}\n{traceback.format_exc()}")
        raise


class ScraperWorker(QThread):
    progress_signal = pyqtSignal(int, int, int)  # worker_id, done, total
    log_signal = pyqtSignal(int, str)             # worker_id, log message
    finished_signal = pyqtSignal(int)

    SAVE_THRESHOLD = 10000  # Save data every 10,000 records

    def __init__(self, worker_id, batch, lang):
        super().__init__()
        self.worker_id = worker_id
        self.batch = batch
        self.lang = lang  # Official language: "English" or "Chinese"
        self.lyrics_list = []
        self.total = len(batch)
        self.done = 0
        self.lyrics_dir = "lyrics"
        self.driver = None
        self._is_running = True  # Control thread running state

    def run(self):
        try:
            self.driver = setup_driver()
            os.makedirs(self.lyrics_dir, exist_ok=True)

            # Determine the split string based on selected language
            lang_split = "Translate to English" if self.lang.lower() == "english" else "翻译成中文"

            for idx, row in self.batch.iterrows():
                if not self._is_running:
                    self.log_signal.emit(self.worker_id, "Exit request received, terminating scraping early.")
                    break

                try:
                    artist, track_name = row['artists'], row['track_name']
                    search_query = f"{artist} {track_name} lyrics"
                    self.driver.get("https://www.google.com/")

                    lyrics = "Not Found"
                    try:
                        element = wait(self.driver, 3).until(
                            EC.visibility_of_element_located((By.NAME, 'q'))
                        )
                        element.send_keys(search_query, Keys.ENTER)
                        lyrics_elem = wait(self.driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@data-attrid="kc:/music/recording_cluster:lyrics"]'))
                        )
                        if lyrics_elem.text:
                            # Split the text based on the chosen language
                            lyrics = lyrics_elem.text.split(lang_split)[0]
                    except Exception as e:
                        self.log_signal.emit(self.worker_id, f"Error processing {artist} - {track_name}: {e}")

                    self.lyrics_list.append((artist, track_name, lyrics))
                    self.done += 1
                    self.progress_signal.emit(self.worker_id, self.done, self.total)
                    self.log_signal.emit(self.worker_id, f"Processed {self.done}/{self.total} - {artist} - {track_name}")

                    # Save data every SAVE_THRESHOLD records
                    if self.done % self.SAVE_THRESHOLD == 0:
                        self.save_lyrics()
                except Exception as inner_e:
                    self.log_signal.emit(self.worker_id, f"Loop error: {inner_e}")
                    log_error(f"Worker {self.worker_id} loop error: {inner_e}\n{traceback.format_exc()}")

            # Save any remaining data
            self.save_lyrics()
            self.batch['lyrics'] = [lyr[2] for lyr in self.lyrics_list]
        except Exception as e:
            self.log_signal.emit(self.worker_id, f"Run error: {e}")
            log_error(f"Worker {self.worker_id} run error: {e}\n{traceback.format_exc()}")
        finally:
            self.cleanup()
            self.finished_signal.emit(self.worker_id)

    def save_lyrics(self):
        try:
            for artist, track_name, lyrics in self.lyrics_list:
                artist_dir = os.path.join(self.lyrics_dir, sanitize_filename(artist))
                os.makedirs(artist_dir, exist_ok=True)
                lyrics_file = os.path.join(artist_dir, sanitize_filename(track_name) + ".txt")
                if not os.path.exists(lyrics_file):
                    with open(lyrics_file, "w", encoding="utf-8") as f:
                        f.write(lyrics)
            self.log_signal.emit(self.worker_id, f"Saved {self.done} lyrics so far.")
        except Exception as e:
            self.log_signal.emit(self.worker_id, f"save_lyrics error: {e}")
            log_error(f"Worker {self.worker_id} save_lyrics error: {e}\n{traceback.format_exc()}")

    def cleanup(self):
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            log_error(f"Worker {self.worker_id} cleanup error: {e}\n{traceback.format_exc()}")

    def stop(self):
        """Notify the thread to exit early"""
        self._is_running = False


class LyricsScraperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.workers = []
        self.worker_widgets = {}
        self.total_workers = 0
        self.completed_workers = 0
        self.initUI()

    def initUI(self):
        try:
            self.setWindowTitle("Lyrics Scraper")
            self.setGeometry(100, 100, 700, 500)

            # Center the window on the screen
            screen_geometry = QGuiApplication.primaryScreen().geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

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

            # Language selection dropdown
            self.language_selector = QComboBox(self)
            self.language_selector.addItem("Chinese")
            self.language_selector.addItem("English")
            layout.addWidget(QLabel("Official Language:"))
            layout.addWidget(self.language_selector)

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
        except Exception as e:
            log_error(f"initUI error: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Error initializing interface: {e}")

    def select_file(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV files (*.csv)")
            if filename:
                self.file_input.setText(filename)
        except Exception as e:
            log_error(f"select_file error: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Error selecting file: {e}")

    def clear_worker_grid(self):
        """Clear the progress panel (grid layout) from previous tasks."""
        try:
            while self.worker_grid.count():
                item = self.worker_grid.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        except Exception as e:
            log_error(f"clear_worker_grid error: {e}\n{traceback.format_exc()}")

    def start_scraping(self):
        try:
            # Reset previous task's progress panel and internal state
            self.clear_worker_grid()
            self.workers = []
            self.worker_widgets = {}
            self.total_workers = 0
            self.completed_workers = 0

            input_path = self.file_input.text()
            if not input_path:
                QMessageBox.warning(self, "Warning", "Please select a CSV file first.")
                return

            try:
                max_workers = int(self.max_workers_input.text())
            except ValueError:
                max_workers = 5

            # Get the selected language from the dropdown
            selected_language = self.language_selector.currentText()

            df = pd.read_csv(input_path)
            batch_size = len(df) // max_workers if max_workers > 0 else len(df)
            batches = [df.iloc[i:i + batch_size] for i in range(0, len(df), batch_size)]

            self.total_workers = len(batches)
            self.completed_workers = 0

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

                # Pass the selected language to each worker
                worker = ScraperWorker(i, batch, selected_language)
                worker.progress_signal.connect(self.update_worker_progress)
                worker.log_signal.connect(self.update_worker_log)
                worker.finished_signal.connect(self.worker_finished)
                worker.start()
                self.workers.append(worker)
        except Exception as e:
            log_error(f"start_scraping error: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Error starting scraping task: {e}")

    def update_worker_progress(self, worker_id, done, total):
        try:
            if worker_id in self.worker_widgets:
                progress_bar, progress_label, _ = self.worker_widgets[worker_id]
                progress_bar.setValue(int((done / total) * 100))
                progress_label.setText(f"{done}/{total}")
        except Exception as e:
            log_error(f"update_worker_progress error: {e}\n{traceback.format_exc()}")

    def update_worker_log(self, worker_id, message):
        try:
            if worker_id in self.worker_widgets:
                _, _, log_box = self.worker_widgets[worker_id]
                log_box.append(message)
        except Exception as e:
            log_error(f"update_worker_log error: {e}\n{traceback.format_exc()}")

    def worker_finished(self, worker_id):
        try:
            self.completed_workers += 1
            if self.completed_workers == self.total_workers:
                QMessageBox.information(self, "Task Completed", "All lyrics have been scraped and saved!")
        except Exception as e:
            log_error(f"worker_finished error: {e}\n{traceback.format_exc()}")

    def closeEvent(self, event):
        """When exiting the program: notify all threads to stop, save any unsaved data, then exit."""
        try:
            reply = QMessageBox.question(
                self, "Exit", "Are you sure you want to exit?\n\nNote: If any scraping tasks are running, the program will save all scraped data before exiting.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Notify all worker threads to stop running
                for worker in self.workers:
                    if worker.isRunning():
                        worker.stop()
                # Wait for all threads to exit
                for worker in self.workers:
                    worker.quit()
                    worker.wait()

                # Optional: Close any remaining chromedriver processes (example for Windows)
                os.system("taskkill /f /im/chromedriver.exe")
                # For Linux/macOS, you can use: os.system("pkill -f chromedriver")

                event.accept()
                os._exit(0)
            else:
                event.ignore()
        except Exception as e:
            log_error(f"closeEvent error: {e}\n{traceback.format_exc()}")
            os._exit(0)


if __name__ == "__main__":
    try:
        multiprocessing.freeze_support()
        app = QApplication(sys.argv)
        window = LyricsScraperGUI()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        error_message = f"An error occurred: {e}\n{traceback.format_exc()}"
        # Write error log
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(error_message)
        # Show error message box
        QMessageBox.critical(None, "Error", f"If you have any questions, please send error_log.txt to the developer.\n{e}")
    finally:
        os._exit(0)
