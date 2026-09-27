# Land Radar Agents

Sekumpulan agen yang berjalan otomatis setiap hari di GitHub Actions untuk memantau prospek tanah di seluruh Indonesia, dengan prioritas Bali, NTB, dan NTT. Hasilnya diterbitkan ke dashboard GitHub Pages dan dikirim ke Telegram.

## Agen

| Agen | File | Tugas |
|---|---|---|
| Harga | `agents/price_agent.py` | Membaca halaman iklan tanah, mengekstrak harga per m² dan per are, menghitung p10, median, p90, lalu memperbarui harga di dashboard. |
| Berita | `agents/news_agent.py` | Mencari berita 30 hari terakhir per katalis (tol, bandara, KEK) lewat Google News RSS. |
| Analis | `agents/analyst_agent.py` | Claude membaca berita baru dan menilai apakah tahap proyek berubah (misalnya penlok ke konstruksi) atau muncul katalis baru. |
| Skor | `agents/scorer.py` | Menghitung ulang skor dan proyeksi harga, membandingkan dengan kemarin, menulis `docs/data.js`. |
| Notifikasi | `agents/notify.py` | Mengirim ringkasan perubahan ke Telegram. |

Urutannya diatur `run_all.py`: harga, berita, analis, skor, notifikasi.

## Cara memasang

1. Buat repo baru di GitHub dan unggah isi folder ini.
2. Di **Settings > Secrets and variables > Actions**, tambahkan:
   - `ANTHROPIC_API_KEY` untuk agen analis (opsional, tanpa ini agen analis dilewati).
   - `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` untuk notifikasi (opsional).
3. Di **Settings > Pages**, pilih sumber *Deploy from a branch*, cabang `main`, folder `/docs`.
4. Buka tab **Actions**, pilih *Land Radar agents*, klik **Run workflow** untuk percobaan pertama. Setelah itu berjalan otomatis setiap hari pukul 05.00 WIB.

Menjalankan di komputer sendiri:

```bash
pip install -r requirements.txt
python run_all.py          # semua agen
python run_all.py skor     # hanya hitung ulang skor dan dashboard
python run_all.py harga    # agen harga + skor
```

## Mengubah data

- `config/hotspots.json` adalah sumber data utama: provinsi, titik, indikator (1–5), katalis dan tahapnya, serta harga.
- `config/settings.json` mengatur model Claude, ambang peringatan, dan URL sumber harga per titik (`price_sources`). Tambahkan URL untuk titik lain agar harganya ikut dipantau.
- `auto_apply_stage_changes` bawaannya `false`: perubahan tahap dari agen analis hanya dikirim sebagai usulan. Ubah ke `true` jika ingin diterapkan otomatis untuk usulan berkeyakinan tinggi.

## Batasan yang perlu diketahui

- Harga dari portal adalah harga penawaran, biasanya 10–30% di atas harga transaksi. Iklan yang tidak menyebut harga per m² atau per are tidak terbaca.
- Portal iklan bisa memblokir akses otomatis atau mengubah tampilan halamannya. Periksa syarat penggunaan tiap portal, beri jeda antarpermintaan, dan isi email kontak di `UA` pada `price_agent.py`.
- Agen berita hanya membaca judul dan ringkasan RSS, bukan isi artikel.
- Proyeksi harga adalah model kasar berbasis asumsi (lihat `UPLIFT` dan `SISA` di `config/hotspots.json`), bukan ramalan. Bukan nasihat investasi.
