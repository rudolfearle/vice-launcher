import glob
import os
import re

# VICE's -joydev1/-joydev2 device codes. 4-9 are physical analog joysticks,
# detected dynamically and appended after these fixed keyboard-emulation options.
FIXED_DEVICES = [
    (0, "None"),
    (1, "Numpad"),
    (2, "Keyset 1"),
    (3, "Keyset 2"),
]
ANALOG_DEVICE_BASE = 4     # VICE device code for "Analog joystick 0"
MAX_ANALOG_DEVICES = 6      # VICE supports Analog joystick 0-5


def _read_device_name(js_name):
    path = f"/sys/class/input/{js_name}/device/name"
    try:
        with open(path, "rb") as f:
            raw = f.read().rstrip(b"\n")
    except OSError:
        return None

    text = raw.decode("utf-8", errors="replace")
    printable_ratio = sum(1 for c in text if c.isprintable() and ord(c) < 128) / max(len(text), 1)
    if printable_ratio > 0.9:
        return text

    # Some USB pads report a mis-encoded (effectively UTF-16) name string that
    # surfaces as CJK-looking garbage; this recovers the readable ASCII inside it.
    try:
        recovered = text.encode("utf-16-le", errors="ignore").decode("latin-1")
        recovered = re.sub(r"[\x00-\x1f\x7f-\xa0]+", " ", recovered).strip()
        return recovered or text
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def detect_analog_joysticks():
    """Return a list of (vice_device_code, label) for connected /dev/input/jsN devices."""
    devices = []
    for path in sorted(glob.glob("/dev/input/js*")):
        js_name = os.path.basename(path)
        match = re.match(r"js(\d+)$", js_name)
        if not match:
            continue
        index = int(match.group(1))
        if index >= MAX_ANALOG_DEVICES:
            continue
        name = _read_device_name(js_name) or js_name
        devices.append((ANALOG_DEVICE_BASE + index, f"Analog joystick {index} ({name})"))
    return devices


def available_devices():
    """All selectable -joydevN options: fixed keyboard emulation + detected joysticks."""
    return FIXED_DEVICES + detect_analog_joysticks()


def label_for_device(code):
    for c, label in available_devices():
        if c == code:
            return label
    return f"Device {code}"
