"""Output switching against a real PipeWire + WirePlumber (run by installer-checks.sh).

Null sinks stand in for the DAC and a Bluetooth device (same node names and card name as
on the Pi); two paplay streams stand in for go-librespot and MPD.
"""
import os
import subprocess
import sys
import tempfile
import time
import wave

import audio_output
import bt_manager

DAC = "alsa_output.platform-soc_sound.stereo-fallback"
MAC = "AA:BB:CC:DD:EE:01"
BT = "bluez_output.AA_BB_CC_DD_EE_01.1"


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()


def null_sink(name, props):
    return sh("pactl", "load-module", "module-null-sink", f"sink_name={name}",
              f"sink_properties={props}")


def stream_sinks():
    names = {line.split("\t")[0]: line.split("\t")[1] for line in sh("pactl", "list", "short", "sinks").splitlines()}
    return sorted(names.get(line.split("\t")[1], "?") for line in sh("pactl", "list", "short", "sink-inputs").splitlines())


def wait_for(what, check, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if check():
            return
        time.sleep(0.2)
    raise AssertionError(f"{what}: default={sh('pactl', 'get-default-sink')} streams={stream_sinks()}")


def chose(output):
    result = audio_output.select(output)
    if result != (True, ""):
        sinks = bt_manager.audio_sinks()
        diag = [f"select({output}) -> {result}", f"audio_sinks: {sinks}",
                subprocess.run(["wpctl", "status"], capture_output=True, text=True).stdout]
        for s in sinks:
            p = subprocess.run(["wpctl", "set-default", str(s["id"])], capture_output=True, text=True)
            diag.append(f"wpctl set-default {s['id']} ({s['name']}): rc={p.returncode} {p.stdout}{p.stderr}")
        raise AssertionError("\n".join(diag))


def on(sink):
    return lambda: sh("pactl", "get-default-sink") == sink and stream_sinks() == [sink, sink]


def main():
    dac_module = null_sink(DAC, "device.description=FakeDAC alsa.card_name=snd_rpi_rpi_dac")
    bt_module = null_sink(BT, "device.description=FakeSpeaker device.api=bluez5")
    silence = os.path.join(tempfile.mkdtemp(), "silence.wav")
    with wave.open(silence, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\0" * 4 * 44100 * 120)
    players = [subprocess.Popen(["paplay", f"--client-name={name}", silence])
               for name in ("go-librespot", "mpd")]
    try:
        wait_for("two streams", lambda: len(stream_sinks()) == 2)
        sinks = {}
        for _ in range(60):  # pw-dump can lag behind pactl on a slow runner
            sinks = {s["name"]: s for s in bt_manager.audio_sinks()}
            if DAC in sinks and BT in sinks:
                break
            time.sleep(0.5)
        assert DAC in sinks and BT in sinks, f"sinks in pw-dump: {sorted(sinks)}"
        assert sinks[DAC]["card"] == "snd_rpi_rpi_dac" and sinks[BT]["bluetooth"], sinks
        assert audio_output.wired_sink(list(sinks.values()))["name"] == DAC

        chose(MAC)
        wait_for("streams on Bluetooth", on(BT))

        chose(audio_output.WIRED)
        wait_for("streams on the jack", on(DAC))
        dac_id = next(s["id"] for s in bt_manager.audio_sinks() if s["name"] == DAC)
        assert sh("wpctl", "get-volume", str(dac_id)).startswith("Volume: 1.00"), "jack sink not at 100 %"

        audio_output.poll()  # Bluetooth still connected: the choice stays
        wait_for("jack choice kept", on(DAC))

        chose(MAC)
        wait_for("back on Bluetooth", on(BT))
        sh("pactl", "unload-module", bt_module)  # the speaker disconnects
        bt_module = None
        audio_output.poll()
        wait_for("fallback to the jack", on(DAC))
        print("routing scenario: all passed")
    finally:
        for p in players:
            p.terminate()
        for module in (bt_module, dac_module):
            if module:
                subprocess.run(["pactl", "unload-module", module], check=False)


if __name__ == "__main__":
    sys.exit(main())
