"""Alat uji MQTT SiagaRob (Task 04).

Perintah:
  topics                    tampilkan topic dari PROJECT_ID (offline)
  validate KEY [FILE|-]     validasi payload terhadap kontrak (offline)
  monitor [--duration N]    subscribe siagarob/PROJECT_ID/# dan validasi tiap pesan
  check-unique [--seconds N]  pastikan prefix PROJECT_ID belum dipakai pihak lain
  publish-command ...       kirim command uji ke Edge 2 (QoS1, retain=false, wajib konfirmasi)

PROJECT_ID dibaca dari env PROJECT_ID atau .env root repo (satu sumber).
HiveMQ publik BUKAN broker privat: jangan kirim rahasia. Tidak ada command yang dikirim otomatis.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import siagarob_contract as C  # noqa: E402

DEFAULT_HOST = "broker.hivemq.com"
DEFAULT_PORT = 1883


def describe_message(project_id: str, full_topic: str, payload: bytes, retain: bool, now: datetime | None = None) -> tuple[list[str], bool]:
    """Kembalikan (baris_keluaran, valid). Baris pertama: timestamp lokal, topic, flag retained."""
    now = now or datetime.now().astimezone()
    ts = now.strftime("%Y-%m-%d %H:%M:%S%z")
    text = payload.decode("utf-8", errors="replace")
    head = f"[{ts}] {full_topic}{' (retained)' if retain else ''}"
    key = C.classify_topic(project_id, full_topic)
    lines = [head, f"  payload: {text}"]
    if key is None:
        lines.append("  ? topic di luar kontrak (tidak divalidasi)")
        return lines, True
    v = C.validate_payload(key, payload)
    if v.ok:
        lines.append("  OK sesuai kontrak" + (f" (peringatan: {'; '.join(v.warnings)})" if v.warnings else ""))
    else:
        lines.append("  TIDAK VALID: " + "; ".join(v.errors))
    return lines, v.ok


def _make_client(role: str, project_id: str):
    import paho.mqtt.client as mqtt

    cid = f"siagarob-tool-{role}-{project_id}-{uuid.uuid4().hex[:6]}"
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cid)


def _connect(client, host: str, port: int, timeout: float = 10.0) -> None:
    state = {"rc": None}

    def on_connect(c, u, flags, rc, props):
        state["rc"] = rc

    client.on_connect = on_connect
    client.connect(host, port, keepalive=30)
    client.loop_start()
    t0 = time.time()
    while state["rc"] is None and time.time() - t0 < timeout:
        time.sleep(0.05)
    if state["rc"] is None:
        client.loop_stop()
        raise ConnectionError(f"Timeout {timeout:.0f}s menyambung ke {host}:{port}")
    if getattr(state["rc"], "is_failure", False):
        client.loop_stop()
        raise ConnectionError(f"Broker menolak koneksi: {state['rc']}")


def cmd_topics(args) -> int:
    pid = C.load_project_id()
    print(f"PROJECT_ID = {pid}")
    for key, (_, qos, retain) in C.TOPICS.items():
        print(f"  {key:16s} QoS{qos} retain={str(retain).lower():5s} {C.topic(pid, key)}")
    return 0


def cmd_validate(args) -> int:
    if args.key not in C.TOPICS:
        print(f"Key tidak dikenal: {args.key}. Pilihan: {', '.join(C.TOPICS)}", file=sys.stderr)
        return 2
    src = args.file or "-"
    raw = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    v = C.validate_payload(args.key, raw)
    if v.ok:
        print("OK" + (f" (peringatan: {'; '.join(v.warnings)})" if v.warnings else ""))
        return 0
    print("TIDAK VALID: " + "; ".join(v.errors), file=sys.stderr)
    return 1


def cmd_monitor(args) -> int:
    pid = C.load_project_id()
    sub = C.prefix(pid) + "#"
    client = _make_client("monitor", pid)
    stats = {"n": 0, "bad": 0}

    def on_message(c, u, msg):
        lines, ok = describe_message(pid, msg.topic, msg.payload, bool(msg.retain))
        print("\n".join(lines), flush=True)
        stats["n"] += 1
        stats["bad"] += 0 if ok else 1

    client.on_message = on_message
    try:
        _connect(client, args.host, args.port)
    except Exception as e:  # noqa: BLE001
        print(f"GAGAL menyambung: {e}", file=sys.stderr)
        return 3
    client.subscribe(sub, qos=1)
    print(f"Tersambung ke {args.host}:{args.port}; subscribe {sub}. Ctrl+C untuk berhenti.", flush=True)
    t0 = time.time()
    try:
        while args.duration is None or time.time() - t0 < args.duration:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
    print(f"Selesai: {stats['n']} pesan, {stats['bad']} tidak valid.")
    return 1 if stats["bad"] else 0


def cmd_check_unique(args) -> int:
    """Subscribe sebentar; jika ada pesan non-retained di prefix, kemungkinan ID dipakai pihak lain."""
    pid = C.load_project_id()
    client = _make_client("unique", pid)
    seen: list[str] = []

    def on_message(c, u, msg):
        seen.append(f"{msg.topic}{' (retained)' if msg.retain else ''}")

    client.on_message = on_message
    try:
        _connect(client, args.host, args.port)
    except Exception as e:  # noqa: BLE001
        print(f"GAGAL menyambung: {e}", file=sys.stderr)
        return 3
    client.subscribe(C.prefix(pid) + "#", qos=1)
    print(f"Mendengarkan {C.prefix(pid)}# selama {args.seconds}s (hentikan Edge/AI milik Anda dulu)...", flush=True)
    time.sleep(args.seconds)
    client.loop_stop()
    client.disconnect()
    if seen:
        print("PERINGATAN: ada lalu lintas pada prefix ini. Mungkin dipakai pihak lain (atau sisa retained). Ganti PROJECT_ID bila bukan milik Anda:")
        for s in seen[:10]:
            print("  " + s)
        return 1
    print("Tidak ada lalu lintas terdeteksi pada prefix ini. Catatan: ini bukan jaminan keunikan, hanya indikasi pada jendela waktu tadi.")
    return 0


def _parse_bool(s: str) -> bool:
    if s.lower() in ("true", "1", "yes", "on"):
        return True
    if s.lower() in ("false", "0", "no", "off"):
        return False
    raise argparse.ArgumentTypeError("gunakan true/false")


def confirm(preview: str, yes: bool, stdin_isatty: bool, input_fn=input) -> bool:
    """Konfirmasi eksplisit: --yes atau ketik 'YA'. Tanpa TTY dan tanpa --yes -> batal."""
    if yes:
        return True
    if not stdin_isatty:
        return False
    return input_fn(f"{preview}\nKetik YA untuk mengirim: ").strip() == "YA"


def cmd_publish_command(args) -> int:
    pid = C.load_project_id()
    try:
        payload = C.build_command(args.pump, args.siren, args.mode, args.source)
    except ValueError as e:
        print(f"Command tidak valid: {e}", file=sys.stderr)
        return 2
    t = C.topic(pid, "edge2_commands")
    body = json.dumps(payload)
    preview = f"AKAN MENGIRIM ke {args.host}:{args.port}\n  topic  : {t}\n  payload: {body}\n  QoS=1 retain=false (broker publik, bukan privat; hanya untuk demo)"
    if not confirm(preview, args.yes, sys.stdin.isatty()):
        print(preview)
        print("DIBATALKAN: tidak ada konfirmasi (gunakan --yes atau ketik YA pada terminal interaktif). Tidak ada yang dikirim.", file=sys.stderr)
        return 4
    client = _make_client("publish", pid)
    try:
        _connect(client, args.host, args.port)
    except Exception as e:  # noqa: BLE001
        print(f"GAGAL menyambung: {e}", file=sys.stderr)
        return 3
    info = client.publish(t, body, qos=1, retain=False)
    try:
        info.wait_for_publish(timeout=10)
    except Exception:  # noqa: BLE001
        pass
    ok = info.is_published()
    client.loop_stop()
    client.disconnect()
    if not ok:
        print("GAGAL: PUBACK dari broker tidak diterima dalam 10s.", file=sys.stderr)
        return 3
    print(f"Terkirim (PUBACK diterima): {t} {body}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default=os.environ.get("MQTT_HOST", DEFAULT_HOST))
    p.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", DEFAULT_PORT)))
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("topics").set_defaults(fn=cmd_topics)
    v = sp.add_parser("validate")
    v.add_argument("key")
    v.add_argument("file", nargs="?")
    v.set_defaults(fn=cmd_validate)
    m = sp.add_parser("monitor")
    m.add_argument("--duration", type=float, default=None, help="detik; default sampai Ctrl+C")
    m.set_defaults(fn=cmd_monitor)
    u = sp.add_parser("check-unique")
    u.add_argument("--seconds", type=float, default=15)
    u.set_defaults(fn=cmd_check_unique)
    c = sp.add_parser("publish-command")
    c.add_argument("--pump", required=True, choices=["ON", "OFF"])
    c.add_argument("--siren", required=True, type=_parse_bool)
    c.add_argument("--mode", required=True, choices=["AUTO", "MANUAL"])
    c.add_argument("--source", required=True, choices=["ai", "dashboard"])
    c.add_argument("--yes", action="store_true", help="konfirmasi eksplisit tanpa prompt")
    c.set_defaults(fn=cmd_publish_command)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except C.ProjectIdError as e:
        print(f"Konfigurasi: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

