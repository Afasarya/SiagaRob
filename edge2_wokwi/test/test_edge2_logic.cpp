// Uji unit logika Edge 2 di PC (lihat edge2_wokwi/README.md).
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include "../edge2_logic.h"

static int fails = 0;
#define CHECK(c, msg) do { bool _ok = (c); printf("%s %s\n", _ok ? "OK  " : "FAIL", msg); if (!_ok) fails++; } while (0)
static bool near(float a, float b, float e = 0.01f) { return std::fabs(a - b) <= e; }

using namespace edge2;

static CmdResult send(State &st, const char *s) { return applyCommand(st, s, strlen(s)); }

static const char *AI_ON = "{\"pump\":\"ON\",\"siren\":false,\"mode\":\"AUTO\",\"source\":\"ai\"}";
static const char *AI_SIREN = "{\"pump\":\"ON\",\"siren\":true,\"mode\":\"AUTO\",\"source\":\"ai\"}";
static const char *AI_OFF = "{\"pump\":\"OFF\",\"siren\":false,\"mode\":\"AUTO\",\"source\":\"ai\"}";
static const char *DASH_OFF_MANUAL = "{\"pump\":\"OFF\",\"siren\":false,\"mode\":\"MANUAL\",\"source\":\"dashboard\"}";
static const char *DASH_AUTO = "{\"pump\":\"OFF\",\"siren\":false,\"mode\":\"AUTO\",\"source\":\"dashboard\"}";

int main() {
  // ADC -> mm/jam
  CHECK(near(adcToRainMmH(0), 0), "ADC 0 -> 0 mm/jam");
  CHECK(near(adcToRainMmH(4095), 80), "ADC 4095 -> 80 mm/jam");
  CHECK(near(adcToRainMmH(2048), 40.0098f, 0.01f), "ADC 2048 -> ~40 mm/jam (linear)");
  CHECK(near(adcToRainMmH(-5), 0) && near(adcToRainMmH(5000), 80), "ADC dijepit ke rentang");

  // moving average 3
  {
    RainAverager a;
    CHECK(near(a.add(30), 30), "rata-rata 1 sampel");
    CHECK(near(a.add(60), 45), "rata-rata 2 sampel");
    CHECK(near(a.add(0), 30), "rata-rata 3 sampel");
    CHECK(near(a.add(90), 50), "jendela bergeser: (60+0+90)/3");
  }

  // state awal
  {
    State s;
    CHECK(!s.pump && !s.siren && s.mode == Mode::AUTO, "state awal: pump OFF, siren off, AUTO");
  }

  // AUTO menerima AI
  {
    State s;
    CHECK(send(s, AI_SIREN) == CmdResult::APPLIED && s.pump && s.siren && s.mode == Mode::AUTO, "AUTO: command AI diterapkan (pump ON, siren ON)");
    CHECK(send(s, AI_OFF) == CmdResult::APPLIED && !s.pump && !s.siren, "AUTO: AI mematikan pompa/sirine");
  }

  // T4: MANUAL menolak AI
  {
    State s;
    send(s, AI_ON);
    CHECK(s.pump, "pra-kondisi: pompa ON oleh AI");
    CHECK(send(s, DASH_OFF_MANUAL) == CmdResult::APPLIED && !s.pump && s.mode == Mode::MANUAL, "T4: dashboard MANUAL pump OFF diterapkan");
    CHECK(send(s, AI_ON) == CmdResult::IGNORED_MANUAL_LOCK, "T4: command AI ditolak saat MANUAL");
    CHECK(!s.pump && !s.siren && s.mode == Mode::MANUAL, "T4: state tidak berubah oleh AI");
    CHECK(send(s, AI_SIREN) == CmdResult::IGNORED_MANUAL_LOCK && !s.siren, "T4: AI siren juga ditolak");
    // dashboard tetap bisa mengubah dalam MANUAL
    CHECK(send(s, "{\"pump\":\"ON\",\"siren\":true,\"mode\":\"MANUAL\",\"source\":\"dashboard\"}") == CmdResult::APPLIED && s.pump && s.siren, "MANUAL: dashboard tetap otoritatif");
    // T5: kembali AUTO
    CHECK(send(s, DASH_AUTO) == CmdResult::APPLIED && s.mode == Mode::AUTO, "T5: dashboard memilih AUTO");
    CHECK(send(s, AI_ON) == CmdResult::APPLIED && s.pump, "T5: AI kembali mengendalikan pompa");
  }

  // AI tidak boleh meminta MANUAL
  {
    State s;
    CHECK(send(s, "{\"pump\":\"ON\",\"siren\":false,\"mode\":\"MANUAL\",\"source\":\"ai\"}") == CmdResult::IGNORED_AI_NOT_AUTO && s.mode == Mode::AUTO && !s.pump, "AI meminta MANUAL ditolak");
  }

  // validasi: semua invalid mengabaikan tanpa mengubah state
  {
    State s;
    send(s, AI_ON);
    const char *bad[] = {
        "",
        "bukan json",
        "{\"pump\":\"ON\"",
        "[1,2,3]",
        "\"teks\"",
        "{}",
        "{\"pump\":\"ON\",\"siren\":false,\"mode\":\"AUTO\"}",                              // tanpa source
        "{\"pump\":\"on\",\"siren\":false,\"mode\":\"AUTO\",\"source\":\"ai\"}",            // huruf kecil
        "{\"pump\":\"MAYBE\",\"siren\":false,\"mode\":\"AUTO\",\"source\":\"ai\"}",
        "{\"pump\":1,\"siren\":false,\"mode\":\"AUTO\",\"source\":\"ai\"}",
        "{\"pump\":\"ON\",\"siren\":\"yes\",\"mode\":\"AUTO\",\"source\":\"ai\"}",
        "{\"pump\":\"ON\",\"siren\":false,\"mode\":\"HYBRID\",\"source\":\"ai\"}",
        "{\"pump\":\"ON\",\"siren\":false,\"mode\":\"AUTO\",\"source\":\"hacker\"}",
        "{\"pump\":null,\"siren\":false,\"mode\":\"AUTO\",\"source\":\"dashboard\"}",
    };
    bool allIgnored = true, unchanged = true;
    for (const char *b : bad) {
      CmdResult r = applyCommand(s, b, strlen(b));
      if (r == CmdResult::APPLIED) { allIgnored = false; printf("   diterapkan: %s\n", b); }
      if (!(s.pump && !s.siren && s.mode == Mode::AUTO)) unchanged = false;
    }
    CHECK(allIgnored, "14 payload invalid semuanya diabaikan");
    CHECK(unchanged, "state tidak berubah oleh payload invalid");
    CHECK(applyCommand(s, nullptr, 5) == CmdResult::IGNORED_BAD_JSON, "payload null aman");
    std::string big(300, 'x');
    CHECK(applyCommand(s, big.c_str(), big.size()) == CmdResult::IGNORED_TOO_LONG, "payload >256 byte diabaikan");
    // payload tanpa terminator null: panjang dipakai, bukan strlen
    char raw[] = {'{', '"', 'p', 'u', 'm', 'p', '"'};
    CHECK(applyCommand(s, raw, sizeof raw) == CmdResult::IGNORED_BAD_JSON, "payload tanpa NUL aman");
  }

  // telemetri sesuai PRD 9.2
  {
    State s;
    s.pump = true;
    char buf[256];
    size_t n = formatTelemetry(buf, sizeof buf, 40, 24.0f, 27.5f, 91, s, 80000);
    CHECK(n > 0 && n < 256, "telemetri muat buffer");
    JsonDocument d;
    CHECK(!deserializeJson(d, buf), "telemetri JSON valid");
    CHECK(strcmp(d["device_id"] | "", "edge2") == 0 && d["seq"] == 40 && near(d["rain_mm_h"], 24.0f) &&
              near(d["temp_c"], 27.5f) && d["hum_pct"] == 91 && strcmp(d["pump"] | "", "ON") == 0 &&
              d["siren"] == false && strcmp(d["mode"] | "", "AUTO") == 0 && d["uptime_ms"] == 80000,
          "nilai telemetri = contoh PRD 9.2");
    CHECK(d.as<JsonObject>().size() == 9, "tepat 9 field");
    // urutan field sama dengan PRD
    const char *order[] = {"device_id", "seq", "rain_mm_h", "temp_c", "hum_pct", "pump", "siren", "mode", "uptime_ms"};
    size_t pos = 0; bool ordered = true;
    for (const char *k : order) {
      std::string key = std::string("\"") + k + "\"";
      const char *f = strstr(buf + pos, key.c_str());
      if (!f) { ordered = false; break; }
      pos = f - buf;
    }
    CHECK(ordered, "urutan field = PRD");
    printf("   %s\n", buf);

    // state dilaporkan setelah command
    State m;
    send(m, DASH_OFF_MANUAL);
    formatTelemetry(buf, sizeof buf, 41, 0, 27.5f, 91, m, 82000);
    JsonDocument d2;
    deserializeJson(d2, buf);
    CHECK(strcmp(d2["mode"] | "", "MANUAL") == 0 && strcmp(d2["pump"] | "", "OFF") == 0, "telemetri melaporkan mode/pump terbaru");
    CHECK(formatTelemetry(buf, 20, 1, 0, 0, 0, m, 0) == 0, "buffer terlalu kecil -> 0");
  }

  printf(fails ? "\nGAGAL: %d\n" : "\nSEMUA LULUS\n", fails);
  return fails ? 1 : 0;
}

