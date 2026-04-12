from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_mamikos_bandung_test():
    print("Membuka browser...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    url = "https://mamikos.com/kost/kost-bandung-kota-murah"
    driver.get(url)

    try:
        print("Menunggu halaman dimuat...")
        # UPDATE 1: Menunggu class pembungkus yang baru
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "kost-rc__content")) 
        )
        
        # Scroll untuk memuat lazy-loading
        for i in range(2):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # UPDATE 2: Menggunakan class pembungkus yang baru
        cards = soup.find_all('div', class_='kost-rc__content') 
        print(f"--- Ditemukan {len(cards)} data kos. Mulai print ke terminal --- \n")

        for card in cards:
            # Ekstraksi Nama
            nama_elem = card.find('span', class_='rc-info__name')
            nama = nama_elem.text.strip() if nama_elem else "Nama Tidak Tersedia"

            # Ekstraksi Lokasi
            lokasi_elem = card.find('span', class_='rc-info__location')
            lokasi = lokasi_elem.text.strip() if lokasi_elem else "Lokasi Tidak Tersedia"

            # Ekstraksi Harga (Sementara pakai pencarian teks general jika class belum pasti)
            # Kita coba cari elemen yang mengandung teks "Rp"
            harga_elem = card.find(string=lambda text: "Rp" in text if text else False)
            harga = harga_elem.strip() if harga_elem else "Harga Belum Dicek"

            # Print hasilnya ke terminal (TIDAK MASUK JSON DULU)
            print(f"Nama   : {nama}")
            print(f"Lokasi : {lokasi}")
            print(f"Harga  : {harga}")
            print("-" * 40)

    except Exception as e:
        print(f"Terjadi kesalahan di terminal: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_mamikos_bandung_test()