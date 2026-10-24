"""Tiny tagged MP3 files for tests: ~1 s of silent MPEG-1 Layer III frames behind an ID3v2.3 tag."""
import struct

# MPEG-1 Layer III, no CRC, 128 kbit/s, 44.1 kHz, mono. An all-zero side info and main
# data block decodes as silence. Frame length = 144 * 128000 / 44100 = 417 bytes.
_FRAME = bytes([0xFF, 0xFB, 0x90, 0xC0]) + bytes(417 - 4)


def _syncsafe(n):
    return bytes([(n >> 21) & 0x7F, (n >> 14) & 0x7F, (n >> 7) & 0x7F, n & 0x7F])


def _text_frame(frame_id, text):
    data = b"\x00" + text.encode("latin-1")
    return frame_id.encode() + struct.pack(">I", len(data)) + b"\x00\x00" + data


def write_mp3(path, title=None, artist=None, album=None, track=None, albumartist=None, frames=40):
    tags = {"TIT2": title, "TPE1": artist, "TALB": album, "TRCK": track, "TPE2": albumartist}
    body = b"".join(_text_frame(k, str(v)) for k, v in tags.items() if v is not None)
    with open(path, "wb") as fh:
        if body:
            fh.write(b"ID3\x03\x00\x00" + _syncsafe(len(body)) + body)
        fh.write(_FRAME * frames)
