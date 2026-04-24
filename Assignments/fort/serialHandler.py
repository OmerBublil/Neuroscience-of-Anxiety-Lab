"""
Serial/BioPac event handler for FORT assignment.

report_event() matches TIM/serialHandler.py exactly:
  - prints timestamp + event to console
  - gracefully skips if ser is None (recordPhysio=False)
  - opens port if closed, writes hex code, 50ms pause, writes "RR" reset, closes

BIOPAC event codes
------------------
NPU encoding (P-condition block):
  Initialization      : 255
  P condition onset   : 110  (base 100 + CONDITION_START 10)
  Cue onset           : 120  (100 + CUE_START 20)
  Cue offset          : 130  (100 + CUE_END 30)
  Startle             : scenario_index + 1
  Shock               : scenario_index + 2

TIM session-level (BIOPAC_EVENTS):
  PreVas_rating       : 90
  PostRun_rating      : 92
  Fixation_cross      : 95
  Start_Cycle         : 100

TIM trial-level (PARADIGM_2_BIOPAC_EVENTS) — identical to TIM/serialHandler.py:
  T2 series 20–28, T4 series 40–48, T6 series 60–68, T8 series 80–88
  T1_Start 150
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

# Trial-level event codes — copied verbatim from TIM/serialHandler.py
PARADIGM_2_BIOPAC_EVENTS = {
    'break': 16,

    'T2_ITIpre': 20,
    'T2_0': 21,
    'T2_2': 22,
    'T2_4': 23,
    'T2_6': 24,
    'T2_8': 25,
    'T2_heat_pulse': 26,
    'T2_PainRatingScale': 27,
    'T2_ITIpost': 28,

    'T4_ITIpre': 40,
    'T4_0': 41,
    'T4_2': 42,
    'T4_4': 43,
    'T4_6': 44,
    'T4_8': 45,
    'T4_heat_pulse': 46,
    'T4_PainRatingScale': 47,
    'T4_ITIpost': 48,

    'T6_ITIpre': 60,
    'T6_0': 61,
    'T6_2': 62,
    'T6_4': 63,
    'T6_6': 64,
    'T6_8': 65,
    'T6_heat_pulse': 66,
    'T6_PainRatingScale': 67,
    'T6_ITIpost': 68,

    'T8_ITIpre': 80,
    'T8_0': 81,
    'T8_2': 82,
    'T8_4': 83,
    'T8_6': 84,
    'T8_8': 85,
    'T8_heat_pulse': 86,
    'T8_PainRatingScale': 87,
    'T8_ITIpost': 88,

    'PreVas_rating':    90,
    'MidRun_rating':    91,
    'PostRun_rating':   92,
    'Fixation_cross':   95,
    'Start_Cycle':      100,
    'T1_Start':         150,
}


def report_event(ser: serial.Serial, event_num: int):
    """Send a BioPac event code over serial. Matches TIM/serialHandler.py exactly."""
    print(f"{round(time.time(), 2)} - Sending event {event_num} to BioPac - {hex(event_num).encode()}")
    if not ser:
        return
    if not ser.is_open:
        ser.open()
    ser.write(hex(event_num).encode())
    time.sleep(0.05)
    ser.write("RR".encode())
    ser.close()
