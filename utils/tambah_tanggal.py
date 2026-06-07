# tambah_tanggal.py
import json
import re

DATA_PATH = "output_dataKos/data_kos.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

bulan_nama = {
    "01": "Januari",  "02": "Februari", "03": "Maret",
    "04": "April",    "05": "Mei",       "06": "Juni",
    "07": "Juli",     "08": "Agustus",   "09": "September",
    "10": "Oktober",  "11": "November",  "12": "Desember"
}

for item in data:
    tanggal = "-"
    foto = item.get("foto", [])
    if isinstance(foto, list):
        for url in foto:
            m = re.search(r'/listings/(\d{2}-\d{4})/', url)
            if m:
                bulan, tahun = m.group(1).split("-")
                tanggal = f"{bulan_nama.get(bulan, bulan)} {tahun}"
                break
    item["tanggal_posting"] = tanggal

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Selesai! {len(data)} data diperbarui.")