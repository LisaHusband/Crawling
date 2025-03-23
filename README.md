
# Lyrics Scraper - User Manual

## 📌 About
**Lyrics Scraper** is a desktop application that automates the process of fetching song lyrics from Google search results based on a given dataset of songs. The lyrics are categorized and saved into structured **text files** under artist-specific folders. The application supports **multi-threading** for faster performance, provides **real-time progress tracking**, and allows users to choose their official language (English or Chinese) for lyric translation. Additionally, the application includes an autosave mechanism and robust error handling for a seamless user experience.

---

## 📌 System Requirements
- **Operating System:** Windows 10/11 (64-bit)
- **RAM:** 4GB minimum (8GB+ recommended)
- **Internet Connection:** Required (VPN recommended for unrestricted access)
- **Google Chrome:** Must be installed (latest version recommended)

---

## 📌 Installation

### 1️⃣ Install the Application
1. Run **`LyricsScraperInstaller.exe`** to start the installation.
2. Follow the on-screen instructions to complete the setup.
3. After installation, launch **Lyrics Scraper** from the **Start Menu** or **Desktop Shortcut**.

### 2️⃣ Included Dependencies & Dataset
- The installation package includes a preprocessed **[Spotify Tracks Genre](https://www.kaggle.com/datasets/thedevastator/spotify-tracks-genre-dataset/)** dataset for testing.
- After installation, the dataset can be found in the application's **dependencies** folder:
  ```
  YourInstallationPath\LyricsScraper\dependencies\
  ```
- The dataset contains three files for different testing scales:
  - **library_dataset.csv** → Full processed dataset
  - **micro_library.csv** → First **100** songs (quick test)
  - **mini_library.csv** → First **10,000** songs

---

## 📌 How to Use

### 1️⃣ Select a Dataset
1. Click the **"Browse"** button and select a **CSV file** (e.g., from the `dependencies/` folder).
2. The file path will be displayed in the text box.

### 2️⃣ Set the Number of Workers
- Enter the number of **parallel threads** for scraping.
- Recommended values:
  - **Low-end PC:** 5-10 threads
  - **High-end PC:** 15-20 threads

### 3️⃣ Choose Official Language
- Select your preferred official language from the dropdown menu:
  - **Chinese** (for splitting on `翻译成中文`)
  - **English** (for splitting on `Translate to English`)

### 4️⃣ Start Scraping
1. Click **"Start Scraping"** to begin the process.
2. The application will open **Google Search** and automatically extract lyrics.
3. Real-time progress bars and logs will display the scraping status.
4. If a new scraping session is started after completion, the progress panel and internal states are reset automatically.

### 5️⃣ Output & Autosave
- **Lyrics are saved in the `lyrics/` directory.**
- Each **artist** is allocated a separate folder, with each **song** saved as a `.txt` file.
- **Autosave Mechanism:**
  - Lyrics are **automatically saved every 10,000 songs** to prevent data loss.
  - The final batch is saved **when scraping is complete**.
- Example file structure:
  ```
  lyrics/
  ├── The Beatles/
  │   ├── Hey Jude.txt
  │   ├── Let It Be.txt
  ├── Queen/
  │   ├── Bohemian Rhapsody.txt
  │   ├── We Will Rock You.txt
  ├── Adele/
      ├── Hello.txt
      ├── Someone Like You.txt
  ```

---

## 📌 Notes & Troubleshooting

### ⚠️ Google Blocking Issues
- **Google may temporarily block automated searches** after too many requests.
- If you encounter **CAPTCHAs** or errors:
  - Reduce the number of **threads**.
  - Use a **VPN (Recommended: USA Server)** to avoid IP bans.
  - Restart your router to change your **IP address**.

### ⚠️ ChromeDriver Issues
- Ensure that **Google Chrome** is installed and updated.
- If the scraper fails to start:
  - Download the latest **ChromeDriver** from [here](https://chromedriver.chromium.org/downloads).
  - Replace the outdated **chromedriver.exe** in the **application directory**.

### ⚠️ Program Exit & Resource Cleanup
- **When closing the app:**
  - All threads and WebDriver instances are forcefully terminated to prevent lingering background processes.
- **If the program does not exit properly:**
  - Open **Task Manager** → End **chromedriver.exe**
  - Or run the command:
    ```
    taskkill /f /im chromedriver.exe
    ```
  - **Linux/macOS:**
    ```
    pkill -f chromedriver
    ```

---

## 📌 Disclaimer
- This software is for **educational and research purposes only**.
- **Do not use it for commercial purposes** or in violation of **Google’s scraping policies**.
- The developer is **not responsible** for any misuse of this tool.

---

## 📌 Support, Contact & Donations

### Support & Contact
- If you encounter any issues:
  - Check **GitHub Issues**.
  - **Contact via Email:** [zongchen3528@outlook.com](mailto:zongchen3528@outlook.com)
- Contributions and bug reports are **welcome**!

### Accepting Donations
If you find **Lyrics Scraper** useful and would like to support further development, please consider making a donation. Your support helps maintain and improve the application.  
- **Donation Options:**
  - **PayPal:** <a href="https://paypal.me/YourPayPalID" style="text-decoration: line-through;">paypal.me/YourPayPalID</a>
  - **Patreon:** <a href="https://patreon.com/YourPatreonPage" style="text-decoration: line-through;">patreon.com/YourPatreonPage</a>
  - **Bitcoin:** <span style="text-decoration: line-through;">YourBitcoinAddress</span>
  - **ALIPAY/WeChat:** <p align="center">
  <img src="alp.jpg" alt="Image 1" width="216" height="324" />
  <img src="wc.png" alt="Image 2" width="223.6" height="304.8" />
</p>



For easier processing, please include your username or contact details along with your donation.
Thank you for your support!


