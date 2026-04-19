"""
Serial/BioPac event handler for FORT assignment.

report_event() matches TIM/serialHandler.py exactly:
  - prints timestamp + event to console
  - gracefully skips if ser is None (recordPhysio=False)
  - opens port if closed, writes hex code, 50ms pause, writes "RR" reset, closes

BIOPAC event codes
------------------
NPU encoding scheme (used inside the P-condition block):
  Condition base  : P = 100
  CONDITION_START : base + 10   → 110  (block onset)
  CUE_START       : index + 20         (cue onset)
  CUE_END         : index + 30         (cue offset)
  STARTLE         : index + 1          (startle probe)
  SHOCK           : index + 2          (threat onset)
  CALIBRATION     : 99
  INIT            : 255

TIM encoding scheme (used for session-level events):
  PreVas_rating   : 90
  PostRun_rating  : 92
  Fixation_cross  : 95
  Start_Cycle     : 100
"""
import time
import serial

# Session-level event codes (TIM convention)
BIOPAC_EVENTS = {
    'PreVas_rating':  90,
    'PostRun_rating': 92,
    'Fixation_cross': 95,
    'Start_Cycle':    100,
}


def report_event(ser: serial.Serial, event_num: int):
    """Send a BioPac event code over serial.  Matches TIM serialHandler exactly."""
    print(f"{round(time.time(), 2)} - Sending event {event_num} to BioPac - {hex(event_num).encode()}")
    if not ser:
        return
    if not ser.is_open:
        ser.open()
    ser.write(hex(event_num).encode())
    time.sleep(0.05)
    ser.write("RR".encode())
    ser.close()
