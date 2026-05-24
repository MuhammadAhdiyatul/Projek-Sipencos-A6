import sqlite3
import json
import os
import datetime
import re

DB_NAME = "sipencos.db"

def _item_key(kos_item):
    if not isinstance(kos_item, dict):
        return None
    nama = str(kos_item.get("nama_kos") or kos_item.get("nama") or "").strip().lower()
    alamat = str(kos_item.get("alamat") or kos_item.get("lokasi") or "").strip().lower()
    return f"{nama}_{alamat}"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create data_kos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_kos (
            id_kos TEXT PRIMARY KEY,
            nama_kos TEXT,
            tipe TEXT,
            wilayah TEXT,
            alamat TEXT,
            harga_saat_ini INTEGER,
            fasilitas TEXT,
            kontak TEXT,
            link_foto TEXT
        )
    """)
    
    # Create favorit table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorit (
            id_favorit INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            id_kos TEXT,
            tanggal_simpan DATETIME,
            FOREIGN KEY (id_kos) REFERENCES data_kos(id_kos)
        )
    """)
    
    # Seed data_kos if empty
    cursor.execute("SELECT COUNT(*) FROM data_kos")
    if cursor.fetchone()[0] == 0:
        json_path = os.path.join("output_dataKos", "data_kos_bersih.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        id_kos = _item_key(item)
                        if not id_kos: continue
                        nama = item.get("nama_kos", "")
                        tipe = item.get("tipe", "")
                        kota = item.get("kota", "")
                        alamat = item.get("alamat", "")
                        
                        # Parsing harga
                        harga_str = item.get("harga", "")
                        harga = 0
                        if isinstance(harga_str, (int, float)):
                            harga = int(harga_str)
                        elif isinstance(harga_str, str):
                            angka = re.sub(r"\D", "", harga_str)
                            harga = int(angka) if angka else 0
                            
                        # Fasilitas
                        fk = item.get("fasilitas_kamar", [])
                        fb = item.get("fasilitas_bersama", [])
                        if isinstance(fk, str): fk = [fk]
                        if isinstance(fb, str): fb = [fb]
                        fasilitas = json.dumps(fk + fb)
                        
                        kontak = item.get("telepon", "")
                        foto = json.dumps(item.get("foto", []))
                        
                        cursor.execute("""
                            INSERT OR IGNORE INTO data_kos 
                            (id_kos, nama_kos, tipe, wilayah, alamat, harga_saat_ini, fasilitas, kontak, link_foto)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (id_kos, nama, tipe, kota, alamat, harga, fasilitas, kontak, foto))
            except Exception as e:
                print(f"Error seeding database: {e}")
                
    conn.commit()
    conn.close()

def add_favorite(username, kos_item):
    id_kos = _item_key(kos_item)
    if not id_kos or not username:
        return
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Check duplicate
    cursor.execute("SELECT id_favorit FROM favorit WHERE username=? AND id_kos=?", (username, id_kos))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO favorit (username, id_kos, tanggal_simpan) VALUES (?, ?, ?)",
                       (username, id_kos, datetime.datetime.now()))
        conn.commit()
    conn.close()

def remove_favorite(username, kos_item):
    id_kos = _item_key(kos_item)
    if not id_kos or not username:
        return
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorit WHERE username=? AND id_kos=?", (username, id_kos))
    conn.commit()
    conn.close()

def get_user_favorites(username, all_kos_data):
    """Returns a list of dicts from all_kos_data that match the user's favorites"""
    if not username:
        return []
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id_kos FROM favorit WHERE username=? ORDER BY tanggal_simpan DESC", (username,))
    rows = cursor.fetchall()
    conn.close()
    
    # Match back to the rich dicts to preserve UI compatibility
    result = []
    fav_list = [r[0] for r in rows]
    lookup = {_item_key(item): item for item in all_kos_data if _item_key(item)}
    
    for fid in fav_list:
        if fid in lookup:
            result.append(lookup[fid])
            
    return result

# Initialize DB on import
init_db()
