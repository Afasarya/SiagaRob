// Logika murni Edge 2 (hujan + aktuator). Hanya bergantung pada ArduinoJson (stack PRD),
// sehingga dapat diuji di PC. Spesifikasi: docs/prd/00-PRD-CONTEXT.md §9.2, §9.4, §10.
#pragma once
#include <ArduinoJson.h>
#include <math.h>
#include <stdint.h>
#include <string.h>

namespace edge2 {

constexpr int ADC_MAX = 4095;
constexpr float RAIN_MAX_MM_H = 80.0f;
constexpr int RAIN_AVG_N = 3;
constexpr size_t COMMAND_MAX_LEN = 256;

enum class Mode { AUTO, MANUAL };

enum class CmdResult {
  APPLIED,
  IGNORED_TOO_LONG,
  IGNORED_BAD_JSON,
  IGNORED_BAD_FIELD,      // field hilang/tipe salah/nilai di luar ON|OFF, AUTO|MANUAL, ai|dashboard
  IGNORED_MANUAL_LOCK,    // source=ai saat mode MANUAL
  IGNORED_AI_NOT_AUTO,    // source=ai tetapi meminta mode MANUAL
};

inline const char *cmdResultText(CmdResult r) {
  switch (r) {
    case CmdResult::APPLIED: return "diterapkan";
    case CmdResult::IGNORED_TOO_LONG: return "diabaikan: payload terlalu panjang";
    case CmdResult::IGNORED_BAD_JSON: return "diabaikan: JSON tidak valid";
    case CmdResult::IGNORED_BAD_FIELD: return "diabaikan: field/nilai tidak valid";
    case CmdResult::IGNORED_MANUAL_LOCK: return "diabaikan: mode MANUAL, command source=ai ditolak";
    case CmdResult::IGNORED_AI_NOT_AUTO: return "diabaikan: source=ai tidak boleh meminta MANUAL";
  }
  return "?";
}

// ADC 0..4095 -> 0..80 mm/jam, linear; nilai di luar rentang dijepit.
inline float adcToRainMmH(int adc) {
  if (adc < 0) adc = 0;
  if (adc > ADC_MAX) adc = ADC_MAX;
  return (float)adc * RAIN_MAX_MM_H / (float)ADC_MAX;
}

class RainAverager {
 public:
  // Rata-rata bergerak 3 pembacaan (kurang dari 3 di awal -> rata-rata yang tersedia).
  float add(float mmh) {
    buf_[pos_ % RAIN_AVG_N] = mmh;
    pos_++;
    if (count_ < RAIN_AVG_N) count_++;
    float s = 0;
    for (int i = 0; i < count_; i++) s += buf_[i];
    return s / (float)count_;
  }

 private:
  float buf_[RAIN_AVG_N] = {0};
  int pos_ = 0;
  int count_ = 0;
};

struct State {
  bool pump = false;
  bool siren = false;
  Mode mode = Mode::AUTO;
};

// Terapkan command ke state. Command tidak valid TIDAK mengubah state sama sekali.
//  - source=dashboard: otoritatif; dapat mengganti mode (MANUAL atau kembali ke AUTO).
//  - source=ai: hanya diterima saat mode AUTO dan meminta mode AUTO.
inline CmdResult applyCommand(State &st, const char *payload, size_t len) {
  if (payload == nullptr || len == 0) return CmdResult::IGNORED_BAD_JSON;
  if (len > COMMAND_MAX_LEN) return CmdResult::IGNORED_TOO_LONG;

  JsonDocument doc;
  if (deserializeJson(doc, payload, len)) return CmdResult::IGNORED_BAD_JSON;
  if (!doc.is<JsonObject>()) return CmdResult::IGNORED_BAD_JSON;

  JsonVariantConst vPump = doc["pump"], vSiren = doc["siren"], vMode = doc["mode"], vSrc = doc["source"];
  if (!vPump.is<const char *>() || !vMode.is<const char *>() || !vSrc.is<const char *>() || !vSiren.is<bool>())
    return CmdResult::IGNORED_BAD_FIELD;

  const char *pump = vPump.as<const char *>();
  const char *mode = vMode.as<const char *>();
  const char *src = vSrc.as<const char *>();

  bool pumpOn;
  if (strcmp(pump, "ON") == 0) pumpOn = true;
  else if (strcmp(pump, "OFF") == 0) pumpOn = false;
  else return CmdResult::IGNORED_BAD_FIELD;

  Mode newMode;
  if (strcmp(mode, "AUTO") == 0) newMode = Mode::AUTO;
  else if (strcmp(mode, "MANUAL") == 0) newMode = Mode::MANUAL;
  else return CmdResult::IGNORED_BAD_FIELD;

  bool fromAi;
  if (strcmp(src, "ai") == 0) fromAi = true;
  else if (strcmp(src, "dashboard") == 0) fromAi = false;
  else return CmdResult::IGNORED_BAD_FIELD;

  if (fromAi) {
    if (st.mode == Mode::MANUAL) return CmdResult::IGNORED_MANUAL_LOCK;
    if (newMode != Mode::AUTO) return CmdResult::IGNORED_AI_NOT_AUTO;
  }

  st.pump = pumpOn;
  st.siren = vSiren.as<bool>();
  st.mode = newMode;
  return CmdResult::APPLIED;
}

// Telemetri Edge 2 sesuai PRD §9.2 (urutan field sama). Mengembalikan panjang JSON
// (0 jika gagal/terpotong).
inline size_t formatTelemetry(char *buf, size_t cap, uint32_t seq, float rain_mm_h, float temp_c,
                              int hum_pct, const State &st, uint32_t uptime_ms) {
  JsonDocument doc;
  doc["device_id"] = "edge2";
  doc["seq"] = seq;
  doc["rain_mm_h"] = roundf(rain_mm_h * 10.0f) / 10.0f;
  doc["temp_c"] = roundf(temp_c * 10.0f) / 10.0f;
  doc["hum_pct"] = hum_pct;
  doc["pump"] = st.pump ? "ON" : "OFF";
  doc["siren"] = st.siren;
  doc["mode"] = st.mode == Mode::AUTO ? "AUTO" : "MANUAL";
  doc["uptime_ms"] = uptime_ms;
  size_t n = serializeJson(doc, buf, cap);
  if (n == 0 || n >= cap) return 0;
  return n;
}

}  // namespace edge2

