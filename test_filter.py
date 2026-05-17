# test_filter.py
import json
import re

HARGA_MIN = 100_000
HARGA_MAX = 50_000_000

def bersihkan_data(data):
    hasil_bersih = []
    duplikat     = set()
    anomali = {
        "duplikat"           : 0,
        "namaTakWajar"   : 0,
        "karakterAneh"      : 0,
        "hargaTakWajar"  : 0,
        "hargaJanggal"      : 0,
        "teleponTidakValid": 0,
        "fotoKosong"        : 0,
        "alamatKosong"      : 0,
    }

    for item in data:
        nama    = item.get("nama_kos", "-")
        harga   = item.get("harga", "-")
        telepon = item.get("telepon", "-")
        alamat  = item.get("alamat", "-")
        foto    = item.get("foto", ["-"])

        kunci = f"{nama.lower()}_{item.get('kota', '').lower()}"
        if kunci in duplikat:
            anomali["duplikat"] += 1
            continue
        duplikat.add(kunci)

        nama_bersih = re.sub(r"&[a-z]+;", "", nama).strip()
        if len(nama_bersih) < 5:
            anomali["namaTakWajar"] += 1
            continue
        item["nama_kos"] = nama_bersih

        if re.search(r"[<>{}\\|@#$%^*]", nama_bersih):
            anomali["karakterAneh"] += 1
            continue

        angka_harga = re.sub(r"[^\d]", "", str(harga))
        if angka_harga:
            val = int(angka_harga)
            if val < HARGA_MIN or val > HARGA_MAX:
                anomali["hargaTakWajar"] += 1
                item["harga"] = "-"

            harga_listing = re.sub(r"[^\d]", "", str(item.get("harga_listing", "")))
            if harga_listing:
                selisih = abs(int(angka_harga) - int(harga_listing))
                if selisih > 10_000_000:
                    anomali["hargaJanggal"] += 1
                    item["harga"] = item.get("harga_listing", "-")

        if telepon and telepon != "-":
            angka_telp = re.sub(r"[^\d]", "", telepon)
            if len(angka_telp) < 9 or len(angka_telp) > 15:
                anomali["teleponTidakValid"] += 1
                item["telepon"] = "-"

        if isinstance(foto, list):
            foto_valid = [f for f in foto if f != "-" and f.startswith("http")]
            item["foto"] = foto_valid if foto_valid else ["-"]
            if not foto_valid:
                anomali["fotoKosong"] += 1

        if not alamat or alamat == "-" or len(alamat) < 5:
            anomali["alamatKosong"] += 1
            item["alamat"] = "-"

        hasil_bersih.append(item)

    print("\n────────── Hasil Filter ──────────")
    print(f"  Data sebelum : {len(data)}")
    for k, v in anomali.items():
        print(f"  {k:<22}: {v}")
    print(f"  Data bersih  : {len(hasil_bersih)}")
    print("────────────────────────────────────")
    return hasil_bersih

# Jalankan
with open("output_dataKos/data_kos.json", encoding="utf-8") as f:
    data = json.load(f)

hasil = bersihkan_data(data)

with open("output_dataKos/data_kos_bersih.json", "w", encoding="utf-8") as f:
    json.dump(hasil, f, indent=2, ensure_ascii=False)

print("Tersimpan: output_dataKos/data_kos_bersih.json")