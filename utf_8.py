# 1. Karakter Standar (Huruf A)
karakter_a = "A"

# Mendapatkan desimal Unicode (65) dan mengubahnya ke Heksadesimal (U+0041)
code_point_a = f"U+{ord(karakter_a):04X}"
# Mengubah ke byte UTF-8
utf8_a = karakter_a.encode('utf-8')

print("--- Huruf A ---")
print(f"Unicode Code Point : {code_point_a}")
print(f"Byte UTF-8 (Hex)   : {utf8_a.hex().upper()}")
print(f"Ukuran Penyimpanan : {len(utf8_a)} Byte\n")


# 2. Karakter Kompleks (Emoji 😊)
emoji = "😊"

code_point_emoji = f"U+{ord(emoji):04X}"
utf8_emoji = emoji.encode('utf-8')

print("--- Emoji 😊 ---")
print(f"Unicode Code Point : {code_point_emoji}")
print(f"Byte UTF-8 (Hex)   : {utf8_emoji.hex().upper()}")
print(f"Ukuran Penyimpanan : {len(utf8_emoji)} Byte")
