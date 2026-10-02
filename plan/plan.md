# Impor Proyek dari GitHub

Mengimpor kode dari repositori GitHub yang sudah ada agar bisa dilanjutkan pengembangannya di sini.
Setelah terimpor, pengembangan fitur baru atau perbaikan bisa langsung dikerjakan di atas basis kode tersebut.

## Untuk siapa
Pemilik proyek yang sudah punya kode di GitHub dan ingin meneruskan pekerjaannya di lingkungan Emergent.

## Hal penting yang perlu diketahui
Mengimpor kode dari GitHub adalah **fitur platform Emergent**, bukan sesuatu yang dibangun lewat kode.
Tindakan impor harus dilakukan sendiri oleh pemilik proyek melalui antarmuka, bukan oleh agen pengembang.

Langkah impor (dilakukan oleh pengguna melalui UI):
1. Gunakan fitur **"Import from GitHub"** / **"Save to Github"** yang tersedia di antarmuka chat Emergent.
2. Pilih atau tempelkan repositori GitHub yang ingin diimpor.
3. Tunggu proses impor selesai sehingga kode masuk ke ruang kerja proyek ini.

## Apa yang terjadi setelah impor selesai
Setelah kode repositori berhasil masuk ke ruang kerja:
1. Basis kode ditelusuri untuk memahami struktur, fungsi utama, dan teknologi yang dipakai.
2. Semua dependensi frontend dan backend dipasang.
3. Aplikasi dijalankan ulang untuk memastikan bisa berjalan di lingkungan ini (frontend, backend, database).
4. Masalah startup atau konfigurasi yang muncul (jika ada) diperbaiki agar aplikasi hidup.
5. Konfirmasi tugas berikutnya: fitur apa yang ingin ditambahkan atau bagian mana yang ingin diubah/diperbaiki.

## Yang perlu Anda putuskan / siapkan
- **Repositori mana** yang ingin diimpor (URL atau nama repo di GitHub).
- **Tujuan setelah impor**: fitur baru yang ingin ditambahkan, atau perbaikan/perubahan pada fungsi yang sudah ada.
- Catatan: jika repositori bersifat privat, pastikan akun GitHub sudah terhubung dengan benar melalui platform saat melakukan impor.

## Fase pengerjaan
**Fase 1 (sekarang):**
- Pengguna melakukan impor repositori melalui fitur platform.
- Agen menelusuri kode, memasang dependensi, dan menjalankan aplikasi agar hidup di lingkungan ini.
- Agen mengonfirmasi keadaan aplikasi saat ini dan menanyakan tugas lanjutan.

**Fase 2 (nanti):**
- Mengerjakan tugas pengembangan pertama yang Anda minta (fitur baru atau perbaikan) di atas kode yang sudah diimpor.

**Fase 3 (nanti):**
- Penyempurnaan dan penambahan fitur lanjutan sesuai kebutuhan.

## Asumsi
- Anda akan melakukan tindakan impor sendiri melalui fitur platform; agen tidak dapat menarik repositori secara otomatis dari dalam kode.
- Setelah impor, fokus utama adalah membuat aplikasi berjalan dulu sebelum menambah logika baru.
- Repositori yang diimpor kompatibel dengan susunan React + FastAPI + MongoDB di lingkungan ini (atau akan disesuaikan agar bisa berjalan).
- Belum ada fitur/perubahan spesifik yang ditentukan; itu akan ditanyakan setelah aplikasi berhasil dijalankan.
