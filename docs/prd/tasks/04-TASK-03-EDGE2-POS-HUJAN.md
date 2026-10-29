# TASK 03 — Firmware Edge 2 Pos Hujan dan aktuator

## Tujuan
Implementasikan Edge 2 dengan DHT22, potensiometer sebagai simulasi hujan, relay/LED pompa, buzzer, telemetri dan kontrol dua arah.

## Scope
- DHT22 GPIO 15; potensiometer ADC GPIO 34; relay/LED GPIO 26; buzzer GPIO 27.
- ADC 0–4095 dipetakan linear 0–80 mm/jam; moving average 3 pembacaan.
- MQTT telemetry, LWT, reconnect, command subscription.
- AUTO mengikuti AI; MANUAL mengikuti dashboard dan tidak ditimpa AI.
- Telemetri melaporkan pump/siren/mode.

## Acceptance criteria
- Payload tepat sesuai kontrak.
- Command valid ON/OFF, AUTO/MANUAL divalidasi.
- Perintah invalid diabaikan aman dan dicatat serial.
- MANUAL tidak dapat ditimpa command `source=ai`.
- Pin dan diagram konsisten.

## Prompt siap pakai

```text
TASK 03 — EDGE 2 POS HUJAN + AKTUATOR

Baca PRD induk, handoff Task 01–02, dan task ini. Implementasikan hanya edge2_wokwi/.
Pin: DHT22 DATA GPIO15; potensiometer SIG GPIO34; relay atau LED merah GPIO26; buzzer GPIO27. Map ADC 0..4095 ke 0..80 mm/jam dan gunakan moving average 3 sampel. Kirim temp_c, hum_pct, rain_mm_h, pump, siren, mode, uptime_ms, device_id dan seq ke topic edge/edge2/telemetry setiap 2 detik.
Gunakan WiFi Wokwi, broker MQTT, client ID unik, LWT retained offline, publish online, reconnect 3 detik, buffer 512. Subscribe edge/edge2/commands. Validasi JSON dan nilai pump ON/OFF serta mode AUTO/MANUAL. Dalam AUTO, terima keputusan AI. Dalam MANUAL, command dashboard source=dashboard menjadi otoritatif dan command source=ai tidak boleh menimpa status. Laporkan keadaan aktual pada telemetry berikutnya.
Buat diagram Wokwi dan libraries yang cocok. Jangan menambah aktuator fisik atau pin baru. Jalankan compile/static checks yang tersedia dan berikan instruksi uji command, termasuk bukti bagaimana MANUAL menolak override AI. Jangan klaim pengujian hardware nyata. Buat handoff.
```
