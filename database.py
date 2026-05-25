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
    
    # Create riwayat table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS riwayat (
            id_riwayat INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            keyword TEXT,
            filter TEXT,
            timestamp TEXT,
            item_data TEXT
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

def add_history_db(username, keyword, filter_type, item_data_dict):
    if not username or str(username).lower() == "guest":
        return
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    
    cursor.execute("SELECT id_riwayat, keyword, filter FROM riwayat WHERE username = ? ORDER BY id_riwayat DESC LIMIT 1", (username,))
    last_row = cursor.fetchone()
    
    item_str = json.dumps(item_data_dict) if item_data_dict else "{}"
    
    if last_row:
        last_id, last_kw, last_filter = last_row
        if filter_type == "DETAIL":
            if last_kw == keyword and last_filter == "DETAIL":
                cursor.execute("UPDATE riwayat SET timestamp = ? WHERE id_riwayat = ?", (timestamp, last_id))
                conn.commit()
                conn.close()
                return
        else:
            if last_kw == keyword and last_filter != "DETAIL":
                cursor.execute("UPDATE riwayat SET timestamp = ?, filter = ? WHERE id_riwayat = ?", (timestamp, filter_type, last_id))
                conn.commit()
                conn.close()
                return
                
    cursor.execute("INSERT INTO riwayat (username, keyword, filter, timestamp, item_data) VALUES (?, ?, ?, ?, ?)",
                   (username, keyword, filter_type, timestamp, item_str))
    conn.commit()
    conn.close()

def get_history_db(username):
    if not username or str(username).lower() == "guest":
        return []
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT keyword, filter, timestamp, item_data FROM riwayat WHERE username = ? ORDER BY id_riwayat DESC", (username,))
    rows = cursor.fetchall()
    conn.close()
    
    histories = []
    for row in rows:
        kw, flt, ts, item_str = row
        try:
            item_data = json.loads(item_str)
        except Exception:
            item_data = {}
        histories.append({
            "keyword": kw,
            "filter": flt,
            "timestamp": ts,
            "item_data": item_data if item_data else None
        })
    return histories

def clear_history_db(username):
    if not username or str(username).lower() == "guest":
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM riwayat WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True

# Initialize DB on import
init_db()
