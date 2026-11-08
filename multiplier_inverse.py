# 1. Menentukan ruang (modulus) dan kunci pengacak
SPACE = 7
MULTIPLIER = 3

# 2. Menghitung kunci pembuka menggunakan kode yang Anda tanyakan
# pow(3, -1, 7) akan menghasilkan angka 5
MULTIPLIER_INVERSE = pow(MULTIPLIER, -1, SPACE)
print(f"Kunci Pengacak (Multiplier): {MULTIPLIER}")
print(f"Kunci Pembuka (Inverse)   : {MULTIPLIER_INVERSE}\n")

# --- PROSES 1: ENKRIPSI (MENGACAK PESAN) ---
# Bayangkan rahasia kita adalah angka 2
PESAN_ASLI = 2 

# Kita acak dengan cara dikali MULTIPLIER, lalu di-modulus SPACE
PESAN_ACAK = (PESAN_ASLI * MULTIPLIER) % SPACE
print(f"Pesan Asli       : {PESAN_ASLI}")
print(f"Pesan Setelah Diacak: {PESAN_ACAK}  <-- (Karena 2 * 3 = 6, 6 % 7 = 6)\n")

# --- PROSES 2: DEKRIPSI (MEMBUKA PESAN) ---
# Di dunia matematika biasa, untuk mengembalikan angka 6 ke angka 2, kita harus membaginya dengan 3 (6 / 3 = 2).
# Tapi di dunia modular, kita TIDAK BOLEH membagi. Kita harus MENGALIKANNYA dengan INVERS-nya.
pesan_kembali = (PESAN_ACAK * MULTIPLIER_INVERSE) % SPACE
print(f"Pesan Setelah Dibuka: {pesan_kembali}  <-- Angka 2 berhasil kembali!")
