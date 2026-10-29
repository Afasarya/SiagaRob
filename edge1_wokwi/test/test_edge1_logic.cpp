// Uji unit logika Edge 1 di PC: g++ -std=c++17 ... (lihat edge1_wokwi/README.md)
#include <cmath>
#include <cstdio>
#include <cstring>
#include "../edge1_logic.h"

static int fails = 0;
#define CHECK(c, msg) do { bool _ok = (c); printf("%s %s\n", _ok ? "OK  " : "FAIL", msg); if (!_ok) fails++; } while (0)
static bool near(float a, float b, float e = 0.01f) { return std::fabs(a - b) <= e; }

int main() {
  using namespace edge1;

  // median
  float a[5] = {5, 1, 4, 2, 3};
  CHECK(median(a, 5) == 3, "median 5 nilai");
  float b[2] = {10, 20};
  CHECK(median(b, 2) == 20, "median 2 nilai (indeks n/2)");
  float c[1] = {7};
  CHECK(median(c, 1) == 7, "median 1 nilai");

  // validasi jarak
  CHECK(!jarakValid(0), "jarak 0 tidak valid");
  CHECK(!jarakValid(1.9f), "jarak <2 tidak valid");
  CHECK(!jarakValid(400.1f), "jarak >400 tidak valid");
  CHECK(jarakValid(2) && jarakValid(400), "batas 2 dan 400 valid");
  CHECK(!jarakValid(NAN), "NaN tidak valid");

  // level = 200 - jarak
  {
    Processor p;
    Result r = p.process(120);
    CHECK(near(r.level_cm, 80) && r.sensor_ok, "level=200-120=80, sensor_ok");
    CHECK(r.rate_cm_min == 0, "rate 0 sebelum ada 5 sampel sebelumnya");
  }

  // median meredam outlier valid tunggal (dalam batas lonjakan)
  {
    Processor p;
    float d[5] = {120, 120, 150, 120, 120};
    Result r{};
    for (float x : d) r = p.process(x);
    CHECK(near(r.level_cm, 80), "median 5 menolak pencilan 150");
  }

  // rate: naik 2 cm/menit selama 6 sampel
  {
    Processor p;
    Result r{};
    // jarak turun 2 per sampel -> level naik; median menunda, jadi cek akhir
    for (int i = 0; i < 12; i++) r = p.process(150 - 2 * i);
    // median 5 dari jarak berurutan = nilai tengah; level naik 2 cm per sampel setelah jendela penuh
    CHECK(near(r.rate_cm_min, 2.0f, 0.05f), "rate_cm_min = +2.0 saat level naik 2 cm/sampel");
  }

  // rate = (now - level 5 sampel lalu)/5 persis, level tetap -> 0
  {
    Processor p;
    Result r{};
    for (int i = 0; i < 10; i++) r = p.process(100);
    CHECK(near(r.rate_cm_min, 0), "level konstan -> rate 0");
  }

  // error: jarak 0 -> sensor_ok=false, pertahankan level terakhir
  {
    Processor p;
    for (int i = 0; i < 5; i++) p.process(120);
    Result r = p.process(0);
    CHECK(!r.sensor_ok && near(r.level_cm, 80), "jarak 0: sensor_ok=false, level valid terakhir dipertahankan");
    r = p.process(500);
    CHECK(!r.sensor_ok && near(r.level_cm, 80), "jarak 500: sensor_ok=false, level dipertahankan");
    r = p.process(1);
    CHECK(!r.sensor_ok && near(r.level_cm, 80), "jarak 1 (<2): sensor_ok=false");
  }

  // lonjakan >50 cm
  {
    Processor p;
    for (int i = 0; i < 5; i++) p.process(120);
    Result r = p.process(171);  // selisih 51
    CHECK(!r.sensor_ok && near(r.level_cm, 80), "lonjakan 51 cm ditolak, level dipertahankan");
    r = p.process(170);  // selisih 50 dari valid terakhir (120) -> boleh
    CHECK(r.sensor_ok, "lonjakan tepat 50 cm diterima");
  }

  // pemulihan setelah error
  {
    Processor p;
    for (int i = 0; i < 5; i++) p.process(120);
    p.process(0);
    Result r = p.process(118);
    CHECK(r.sensor_ok, "pulih saat pembacaan valid kembali");
  }

  // belum pernah valid
  {
    Processor p;
    Result r = p.process(0);
    CHECK(!r.sensor_ok && r.level_cm == 0, "belum ada nilai valid: sensor_ok=false, level 0");
  }

  // format JSON sesuai kontrak PRD 9.1
  {
    char buf[256];
    Result r{82.4f, 1.8f, true};
    int n = formatTelemetry(buf, sizeof buf, 42, r, 84000);
    const char *exp = "{\"device_id\":\"edge1\",\"seq\":42,\"level_cm\":82.4,\"rate_cm_min\":1.8,\"sensor_ok\":true,\"uptime_ms\":84000}";
    CHECK(n > 0 && strcmp(buf, exp) == 0, "JSON = contoh PRD 9.1 persis");
    CHECK(n < 256, "JSON muat buffer");
    Result r2{80.0f, 0.0f, false};
    formatTelemetry(buf, sizeof buf, 1, r2, 2000);
    CHECK(strstr(buf, "\"sensor_ok\":false") != nullptr, "sensor_ok=false diserialisasi");
  }

  printf(fails ? "\nGAGAL: %d\n" : "\nSEMUA LULUS\n", fails);
  return fails ? 1 : 0;
}

