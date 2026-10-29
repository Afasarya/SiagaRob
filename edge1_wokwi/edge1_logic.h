// Logika murni Edge 1 (tanpa dependensi Arduino) agar dapat diuji di PC.
// Spesifikasi: docs/prd/00-PRD-CONTEXT.md §9.1 dan §10 (Edge 1).
#pragma once
#include <stdint.h>
#include <stdio.h>

namespace edge1 {

constexpr float TINGGI_PASANG_CM = 200.0f;
constexpr float JARAK_MIN_CM = 2.0f;
constexpr float JARAK_MAX_CM = 400.0f;
constexpr float LONJAKAN_MAX_CM = 50.0f;
constexpr int MEDIAN_N = 5;
constexpr int RATE_N = 5;  // selisih terhadap level 5 sampel sebelumnya

struct Result {
  float level_cm;
  float rate_cm_min;
  bool sensor_ok;
};

// Median dari n (<=5) nilai; n harus >= 1.
inline float median(const float *v, int n) {
  float a[MEDIAN_N];
  for (int i = 0; i < n; i++) a[i] = v[i];
  for (int i = 1; i < n; i++) {  // insertion sort
    float k = a[i];
    int j = i - 1;
    while (j >= 0 && a[j] > k) {
      a[j + 1] = a[j];
      j--;
    }
    a[j + 1] = k;
  }
  return a[n / 2];
}

// Jarak 0, di luar 2..400 cm, atau NaN dianggap tidak valid.
inline bool jarakValid(float d) {
  return d == d && d != 0.0f && d >= JARAK_MIN_CM && d <= JARAK_MAX_CM;
}

class Processor {
 public:
  // Dipanggil sekali per sampel (tiap 2 detik nyata = 1 menit simulasi).
  // distance_cm: pembacaan mentah HC-SR04 (0 jika timeout).
  Result process(float distance_cm) {
    bool ok = jarakValid(distance_cm);
    if (ok && haveValid_ && fabsf_(distance_cm - lastRawValid_) > LONJAKAN_MAX_CM) ok = false;

    if (ok) {
      lastRawValid_ = distance_cm;
      haveValid_ = true;
      // jendela median hanya berisi pembacaan valid
      if (winCount_ < MEDIAN_N) {
        win_[winCount_++] = distance_cm;
      } else {
        for (int i = 1; i < MEDIAN_N; i++) win_[i - 1] = win_[i];
        win_[MEDIAN_N - 1] = distance_cm;
      }
      lastLevel_ = TINGGI_PASANG_CM - median(win_, winCount_);
    }
    // Jika tidak ok: pertahankan lastLevel_ (nilai valid terakhir).
    // Belum pernah ada pembacaan valid: lastLevel_ = 0 dan sensor_ok=false.

    // Waktu tetap berjalan walau sensor error -> level tertahan masuk riwayat.
    float rate = 0.0f;
    if (histCount_ >= RATE_N) {
      rate = (lastLevel_ - hist_[(histPos_) % RATE_N]) / (float)RATE_N;
    }
    hist_[histPos_ % RATE_N] = lastLevel_;
    histPos_++;
    if (histCount_ < RATE_N) histCount_++;

    return Result{lastLevel_, rate, ok};
  }

 private:
  static float fabsf_(float x) { return x < 0 ? -x : x; }
  float win_[MEDIAN_N] = {0};
  int winCount_ = 0;
  float lastRawValid_ = 0;
  bool haveValid_ = false;
  float lastLevel_ = 0;
  float hist_[RATE_N] = {0};  // buffer melingkar level 5 sampel terakhir
  int histPos_ = 0;
  int histCount_ = 0;
};

// Tulis JSON telemetri Edge 1 persis sesuai kontrak (urutan field PRD §9.1).
// Mengembalikan jumlah karakter; < 0 atau >= cap berarti gagal/terpotong.
inline int formatTelemetry(char *buf, size_t cap, uint32_t seq, const Result &r, uint32_t uptime_ms) {
  return snprintf(buf, cap,
                  "{\"device_id\":\"edge1\",\"seq\":%lu,\"level_cm\":%.1f,\"rate_cm_min\":%.1f,"
                  "\"sensor_ok\":%s,\"uptime_ms\":%lu}",
                  (unsigned long)seq, (double)r.level_cm, (double)r.rate_cm_min,
                  r.sensor_ok ? "true" : "false", (unsigned long)uptime_ms);
}

}  // namespace edge1

