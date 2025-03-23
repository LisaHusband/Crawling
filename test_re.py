import multiprocessing
import os
import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QTextEdit, QProgressBar
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class LyricsScraperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Lyrics Scraper")
        self.setGeometry(100, 100, 500, 400)
        layout = QVBoxLayout()
        # 使用教程
        self.tutorial_label = QLabel("使用教程:")
        layout.addWidget(self.tutorial_label)
        
        self.tutorial_text = QTextEdit(self)
        self.tutorial_text.setReadOnly(True)

        # 设置教程内容
        '''
        # 首先配置数据集文件路径
        # VPN开启全局模式（美国）
        # 可根据CPU配置最大线程数
        # 关闭桌面无用窗口，任务管理器无用进程，托盘无用软件。
        # 把世界调成静音，聆听散热狂放的声音
        '''
        # 使用教程改为英文
        self.tutorial_text.append("1. Firstly, configure the data set file path\n")
        self.tutorial_text.append("2. Open the VPN in global mode (United States)\n")
        self.tutorial_text.append("3. Set the maximum number of threads according to the CPU configuration\n")
        self.tutorial_text.append("4. Close unnecessary desktop windows, unnecessary processes in the task manager, and unnecessary software in the tray.\n")
        self.tutorial_text.append("5. Turn the world into silence and listen to the noise of the fancy fancy fanfare\n")
        layout.addWidget(self.tutorial_text)

        self.label = QLabel("Select CSV File:")
        layout.addWidget(self.label)

        self.file_input = QLineEdit(self)
        layout.addWidget(self.file_input)

        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.select_file)
        layout.addWidget(self.browse_button)

        self.max_workers_label = QLabel("Max Workers:")
        layout.addWidget(self.max_workers_label)

        self.max_workers_input = QLineEdit("10", self)
        layout.addWidget(self.max_workers_input)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.start_button = QPushButton("Start Scraping", self)
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def select_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV files (*.csv)")
        if filename:
            self.file_input.setText(filename)

    def log_callback(self, msg):
        self.log_text.append(msg)

    def progress_callback(self, done, total):
        self.progress_bar.setValue(int((done / total) * 100))

    def start_scraping(self):
        input_path = self.file_input.text()
        max_workers = int(self.max_workers_input.text())

        if not input_path:
            self.log_callback("Please select an input file.")
            return
        if max_workers <= 0:
            self.log_callback("Please enter a valid number of max workers.")
            return

        process = multiprocessing.Process(target=process_in_batches, args=(input_path, input_path, max_workers))
        process.start()


def setup_driver():
    """ 初始化 Chrome WebDriver """
    options = Options()
    # options.add_argument("--headless")  # 无头模式
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


def scrape_lyrics(batch):
    """ 爬取歌词 """
    driver = setup_driver()
    lyrics_list = []

    for _, row in batch.iterrows():
        artist, track_name = row['artists'], row['track_name']
        search_query = f"{artist} {track_name} lyrics"
        driver.get("https://www.google.com/")
        element = wait(driver, 3).until(EC.visibility_of_element_located((By.NAME, 'q')))
        element.send_keys(search_query, Keys.ENTER)

        try:
            lyrics_elem = wait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-attrid="kc:/music/recording_cluster:lyrics"]'))
            )
            lyrics = lyrics_elem.text.split('翻译成中文')[0] if lyrics_elem.text else "Not Found"
        except:
            lyrics = "Not Found"

        lyrics_list.append(lyrics)
        driver.delete_all_cookies()

    driver.quit()
    batch['lyrics'] = lyrics_list
    return batch


def process_in_batches(input_csv, output_csv, max_workers):
    """ 多进程批量爬取 """
    df = pd.read_csv(input_csv)
    batch_size = min(500, len(df) // max_workers)
    batches = [df.iloc[i:i+batch_size] for i in range(0, len(df), batch_size)]

    with multiprocessing.Manager() as manager:
        progress = manager.Value('i', 0)
        total = len(df)

        def update_progress(_):
            with progress.get_lock():
                progress.value += batch_size
                print(f"Progress: {progress.value}/{total}")

        with multiprocessing.Pool(max_workers) as pool:
            results = [pool.apply_async(scrape_lyrics, args=(batch,), callback=update_progress) for batch in batches]
            final_batches = [r.get() for r in results]

        final_df = pd.concat(final_batches, ignore_index=True)
        final_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"Scraping completed. Results saved to {output_csv}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = LyricsScraperGUI()
    window.show()
    sys.exit(app.exec())
