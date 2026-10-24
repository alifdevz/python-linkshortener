import sqlite3
import string

# =====================================================================
# 1. KONFIGURASI GLOBAL & KARAKTER BASE62
# =====================================================================
# Karakter Base62: total 62 karakter unik (0-9, a-z, A-Z)
BASE62 = string.digits + string.ascii_lowercase + string.ascii_uppercase

DATABASE_FILE = "url_shortener.db"


# =====================================================================
# 2. FUNGSI PEMBUATAN DATABASE & TABEL (SQLITE)
# =====================================================================
def init_database():
    """
    Membuat file database dan tabel 'urls' jika belum ada.
    Kolom 'long_url' diberi aturan UNIQUE untuk mencegah duplikasi data.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Eksekusi perintah SQL untuk membuat tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_url TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Opsional: Mengatur ID awal SQLite agar mulai dari angka besar (misal: 100000)
    # Ini dilakukan agar panjang kode URL pendek yang dihasilkan langsung 4 karakter
    cursor.execute("SELECT COUNT(*) FROM urls")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('urls', 99999)")
        
    conn.commit()
    conn.close()
    print("[DATABASE] Database dan tabel berhasil diinisialisasi.")


# =====================================================================
# 3. FUNGSI INTI ALGORITMA BASE62
# =====================================================================
def encode_base62(num: int) -> str:
    """Mengubah angka ID database menjadi string pendek Base62"""
    if num == 0:
        return BASE62[0]
    
    arr = []
    base = len(BASE62)
    while num:
        num, rem = divmod(num, base)
        arr.append(BASE62[rem])
    arr.reverse()
    return ''.join(arr)


def decode_base62(short_str: str) -> int:
    """Mengubah string pendek Base62 kembali menjadi angka ID database"""
    base = len(BASE62)
    num = 0
    for char in short_str:
        num = num * base + BASE62.index(char)
    return num


# =====================================================================
# 4. FUNGSI LOGIKA SISTEM (INSERT UNIQUE & SELECT)
# =====================================================================
def shorten_url(long_url: str) -> str:
    """
    Menyimpan URL panjang ke database asli.
    Jika URL sudah ada, database akan menolak duplikasi berkat aturan UNIQUE,
    dan sistem akan langsung mengambil ID yang lama.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        # Coba masukkan URL baru ke database
        cursor.execute("INSERT INTO urls (long_url) VALUES (?)", (long_url,))
        conn.commit()
        assigned_id = cursor.lastrowid
        print(f"[SUCCESS] URL baru disimpan ke database dengan ID: {assigned_id}")
    
    except sqlite3.IntegrityError:
        # Jika error IntegrityError dipicu, berarti URL sudah ada (Melanggar aturan UNIQUE)
        # Sistem akan langsung mengambil ID dari URL yang sudah terdaftar tersebut
        cursor.execute("SELECT id FROM urls WHERE long_url = ?", (long_url,))
        assigned_id = cursor.fetchone()[0]
        print(f"[INFO] URL sudah terdaftar di database. Menggunakan ID lama: {assigned_id}")
    
    finally:
        conn.close()
        
    # Konversi ID database menjadi kode pendek Base62
    return encode_base62(assigned_id)


def get_original_url(short_code: str) -> str:
    """Mendecode kode pendek dan mencari URL aslinya di database SQLite"""
    # 1. Decode string menjadi ID angka
    db_id = decode_base62(short_code)
    
    # 2. Cari di database berdasarkan ID tersebut
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT long_url FROM urls WHERE id = ?", (db_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    else:
        return "ERROR: URL Tidak Ditemukan di Database!"


# =====================================================================
# 5. SIMULASI JALANNYA PROGRAM (PENGUJIAN)
# =====================================================================
if __name__ == "__main__":
    # Langkah pertama: Siapkan databasenya
    init_database()
    print("\n--- SIMULASI INPUT URL ---")
    
    # Input 1: Memasukkan URL baru (Google)
    code1 = shorten_url("https://google.com")
    print(f"-> URL Pendek: https://minilink.id{code1}\n")
    
    # Input 2: Memasukkan URL baru yang berbeda (Wikipedia)
    code2 = shorten_url("https://wikipedia.org")
    print(f"-> URL Pendek: https://minilink.id{code2}\n")
    
    # Input 3: Memasukkan kembali URL Google (Menguji proteksi UNIQUE database)
    code3 = shorten_url("https://google.com")
    print(f"-> URL Pendek: https://minilink.id{code3}\n")
    
    print("--- SIMULASI REDIRECT / AMBIL DATA ---")
    # Mengambil data dari database menggunakan kode pendek
    print(f"Membuka /{code1} -> Diarahkan ke: {get_original_url(code1)}")
    print(f"Membuka /{code2} -> Diarahkan ke: {get_original_url(code2)}")
