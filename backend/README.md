# SiagaRob Backend Data Adapter (Task 08)

Backend adapter berbasis **FastAPI** (Port 8000) yang berfungsi sebagai jembatan resmi antara sumber data eksternal publik dan Dashboard Next.js.

Sesuai aturan PRD Induk §2, §3, dan §8:
- Mengatasi pembatasan browser CORS.
- Menyediakan in-memory caching (TTL 30 menit) dan perlindungan rate-limit.
- Menstandarkan metadata kesegaran data: `source`, `source_type=official`, `fetched_at`, `status` (`LIVE`, `STALE`, `UNAVAILABLE`), dan atribusi hak cipta resmi.
- Menghindari web-scraping agresif; jika portal tidak menyediakan API publik resmi (seperti PantauBanjir Semarang dan BIG Pasang Surut), adapter secara transparan melaporkan status `UNAVAILABLE` beserta tautan portal resmi.
- Prakiraan cuaca BMKG diberi label tegas sebagai `FORECAST`, bukan pengukuran curah hujan terukur.

## Struktur
```text
backend/
├── app/
│   ├── main.py              # FastAPI app & endpoint routing
│   ├── models.py            # Pydantic schemas metadata PRD §3
│   ├── cache.py             # In-memory TTL cache dengan fallback STALE
│   └── adapters/
│       ├── bmkg.py          # Adapter BMKG cuaca (Semarang Utara Bandarharjo)
│       ├── pantaubanjir.py  # Adapter PantauBanjir (Status: UNAVAILABLE)
│       └── big_tides.py     # Adapter BIG Pasang Surut (Status: UNAVAILABLE)
├── fixtures/
│   └── bmkg_sample.json     # Fixture offline untuk pengujian deterministik
├── tests/
│   └── test_adapters.py     # Unit test pytest offline
└── requirements.txt
```

## Cara Menjalankan

### 1. Instalasi Dependensi
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
```

### 2. Jalankan Server FastAPI (Port 8000)
```powershell
uvicorn app.main:app --app-dir backend --reload --port 8000
```
- Dokumentasi Swagger UI: `http://localhost:8000/docs`
- Endpoint Data Bundle: `http://localhost:8000/api/external-data`

### 3. Pengujian Unit
```powershell
python -m pytest backend/tests -q
```

