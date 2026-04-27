import json
import os
import re

from ui_main import App
from backend import BackendManager

try:
	from Scraping import KosScraper
except Exception:
	KosScraper = None


DUMMY_DATA = [
	{
		"id": 1,
		"nama": "Kos Dago",
		"harga": 1200000,
		"lokasi": "Bandung",
		"wifi": True,
		"deskripsi": "Kos nyaman dekat kampus",
	},
	{
		"id": 2,
		"nama": "Kos Setiabudi",
		"harga": 950000,
		"lokasi": "Bandung",
		"wifi": False,
		"deskripsi": "Akses mudah ke transportasi umum",
	},
]


class IntegrationController:
	"""Lapisan integrasi sederhana antara UI, backend, dan scraper."""

	def __init__(self):
		self.backend = self._init_backend()
		self.scraped_data = self._load_scraped_data()
		self.backend_data = self._load_backend_data()
		self.dummy_data = [self._normalize_item(item, i + 1) for i, item in enumerate(DUMMY_DATA)]

		if self.scraped_data:
			self.active_data = self.scraped_data
		elif self.backend_data:
			self.active_data = self.backend_data
		else:
			self.active_data = self.dummy_data

	def _init_backend(self):
		try:
			return BackendManager()
		except Exception as e:
			print(f"[WARN] Backend gagal diinisialisasi: {e}")
			return None

	def _to_int_price(self, harga):
		if isinstance(harga, (int, float)):
			return int(harga)
		if not isinstance(harga, str):
			return 0
		angka = re.sub(r"\D", "", harga)
		return int(angka) if angka else 0

	def _format_price(self, harga):
		nilai = self._to_int_price(harga)
		return f"Rp {nilai:,}".replace(",", ".") if nilai > 0 else "-"

	def _normalize_foto(self, value):
		if isinstance(value, list):
			return [str(url).strip() for url in value if str(url).strip()]

		if isinstance(value, str):
			parts = [part.strip() for part in value.split(",") if part.strip()]
			return parts

		return []

	def _normalize_item(self, raw, default_id):
		raw = raw or {}

		item_id = raw.get("id", default_id)
		nama = (
			raw.get("nama")
			or raw.get("nama_kos")
			or raw.get("title")
			or "Kos Tanpa Nama"
		)
		harga = self._to_int_price(raw.get("harga", raw.get("harga_listing", 0)))
		lokasi = raw.get("lokasi") or raw.get("alamat") or "Bandung"

		fasilitas_kamar = raw.get("fasilitas_kamar") or []
		fasilitas_bersama = raw.get("fasilitas_bersama") or []
		wifi_raw = raw.get("wifi")
		if isinstance(wifi_raw, bool):
			wifi = wifi_raw
		else:
			gabung_fasilitas = " ".join(
				[" ".join([str(x) for x in fasilitas_kamar]), " ".join([str(x) for x in fasilitas_bersama])]
			).lower()
			wifi = "wifi" in gabung_fasilitas

		deskripsi = raw.get("deskripsi") or raw.get("alamat") or "-"

		# Simpan format standar + field tambahan agar UI lama tetap kompatibel.
		return {
			"id": item_id,
			"nama": nama,
			"harga": harga,
			"lokasi": lokasi,
			"wifi": wifi,
			"deskripsi": deskripsi,
			"telepon": raw.get("telepon", raw.get("nomor_telepon", "-")),
			"fasilitas_kamar": fasilitas_kamar if isinstance(fasilitas_kamar, list) else ["-"],
			"fasilitas_bersama": fasilitas_bersama if isinstance(fasilitas_bersama, list) else ["-"],
			"foto": self._normalize_foto(raw.get("foto", [])),
		}

	def _to_ui_item(self, item):
		return {
			"id": item.get("id", 0),
			"nama": item.get("nama", "Kos Tanpa Nama"),
			"harga": item.get("harga", 0),
			"lokasi": item.get("lokasi", "Bandung"),
			"wifi": item.get("wifi", False),
			"deskripsi": item.get("deskripsi", "-"),
			"nama_kos": item.get("nama", "Kos Tanpa Nama"),
			"alamat": item.get("lokasi", "Bandung"),
			"telepon": item.get("telepon", "-"),
			"fasilitas_kamar": item.get("fasilitas_kamar", ["-"]),
			"fasilitas_bersama": item.get("fasilitas_bersama", ["-"]),
			"foto": item.get("foto", []),
			"harga_display": self._format_price(item.get("harga", 0)),
		}

	def _normalize_list(self, data_list):
		if not isinstance(data_list, list):
			return []
		return [self._normalize_item(item, idx + 1) for idx, item in enumerate(data_list)]

	def _load_json_if_exists(self, path):
		if not os.path.exists(path):
			return []
		try:
			with open(path, "r", encoding="utf-8") as f:
				return json.load(f)
		except Exception as e:
			print(f"[WARN] Gagal baca {path}: {e}")
			return []

	def _load_scraped_data(self):
		json_path = os.path.join("output_dataKos", "data_kos.json")

		scraped = self._normalize_list(self._load_json_if_exists(json_path))
		if scraped:
			return scraped

		if KosScraper is None:
			return []

		try:
			scraper = KosScraper()
			scraper.jalankan()
			scraped = self._normalize_list(self._load_json_if_exists(json_path))
			return scraped
		except Exception as e:
			print(f"[WARN] Scraper gagal: {e}")
			return []

	def _load_backend_data(self):
		if not self.backend:
			return []

		data = []

		try:
			data = self.backend.cari_kos()
		except Exception:
			data = getattr(self.backend, "data_kos", [])

		return self._normalize_list(data)

	def _search_in_list(self, data_list, keyword):
		if not keyword:
			return data_list

		key = keyword.lower().strip()
		hasil = []

		for item in data_list:
			teks = f"{item.get('nama', '')} {item.get('lokasi', '')} {item.get('deskripsi', '')}".lower()
			if key in teks:
				hasil.append(item)

		return hasil

	def get_all_for_ui(self):
		return [self._to_ui_item(item) for item in self.active_data]

	def search_for_ui(self, keyword):
		key = (keyword or "").strip()
		if not key:
			return self.get_all_for_ui()

		# Alur: coba data scraper dulu, lalu fallback ke backend, lalu dummy.
		hasil_scraper = self._search_in_list(self.scraped_data, key)
		if hasil_scraper:
			return [self._to_ui_item(item) for item in hasil_scraper]

		hasil_backend = []
		if self.backend:
			try:
				hasil_backend = self._normalize_list(self.backend.cari_kos(keyword=key))
			except TypeError:
				try:
					hasil_backend = self._normalize_list(self.backend.cari_kos(key))
				except Exception:
					hasil_backend = []
			except Exception:
				hasil_backend = []

		if hasil_backend:
			return [self._to_ui_item(item) for item in hasil_backend]

		hasil_dummy = self._search_in_list(self.dummy_data, key)
		return [self._to_ui_item(item) for item in hasil_dummy]

	def scrape_for_ui(self):
		"""Jalankan scraping manual dari UI lalu kembalikan data terbaru untuk ditampilkan."""
		json_path = os.path.join("output_dataKos", "data_kos.json")

		if KosScraper is not None:
			try:
				scraper = KosScraper()
				scraper.jalankan()
			except Exception as e:
				print(f"[WARN] Scrape manual gagal: {e}")

		fresh_scraped = self._normalize_list(self._load_json_if_exists(json_path))
		if fresh_scraped:
			self.scraped_data = fresh_scraped
			self.active_data = fresh_scraped
			return [self._to_ui_item(item) for item in fresh_scraped]

		# Fallback aman agar UI tetap bisa refresh walau scraping gagal/empty.
		if self.backend_data:
			self.active_data = self.backend_data
			return [self._to_ui_item(item) for item in self.backend_data]

		self.active_data = self.dummy_data
		return [self._to_ui_item(item) for item in self.dummy_data]


def main():
	controller = IntegrationController()
	app = App(
		search_callback=controller.search_for_ui,
		get_all_callback=controller.get_all_for_ui,
		scrape_callback=controller.scrape_for_ui,
	)
	app.mainloop()


if __name__ == "__main__":
	main()
