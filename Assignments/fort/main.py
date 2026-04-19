"""
FORT Task — main entry point.

Session structure (TIM-style, single session):
  1. Config dialog
  2. Welcome screen  (NPU-style, space to continue)
  3. Pre-session mood VAS  →  BioPac event PreVas_rating (90)
  4. Instruction slides (optional, NPU-style slides)
  5. Fixation cross  →  BioPac event Fixation_cross (95), duration configurable
  6. P-condition block  (NPU predictable threat, 120 s)
        Block onset   →  BioPac 110  (P-base 100 + CONDITION_START 10)
        Cue onset     →  BioPac 120  (100 + CUE_START 20)
        Cue offset    →  BioPac 130  (100 + CUE_END 30)
        Startle       →  BioPac +1 relative to current scenario index
        Shock/Threat  →  BioPac +2 relative to current scenario index
  7. Post-session mood VAS  →  BioPac event PostRun_rating (92)
  8. Finish screen
  9. Export fullDF, miniDF (NPU-style) + Mood (TIM-style)

Run from fort/ directory:
    python3 main.py
"""
import os
import json
import time

import serial
import pandas as pd
from psychopy.iohub import launchHubServer
from psychopy import visual, core
import configDialog
import dataHandler
import helpers
import blockP
import VAS
import serialHandler

# ---------------------------------------------------------------------------
# Startup & configuration
# ---------------------------------------------------------------------------
io = launchHubServer()

debug = False
configDialogBank = configDialog.get_user_input(debug)

params = {
    "Subject":           configDialogBank[0],
    "session":           configDialogBank[1],
    "gender":            configDialogBank[2],
    "language":          configDialogBank[3],
    "shockType":         configDialogBank[4],
    "skipStartle":       configDialogBank[5],
    "recordPhysio":      configDialogBank[6],
    "skipInstructions":  configDialogBank[7],
    "fixationDuration":  int(configDialogBank[8]) if configDialogBank[8] not in (None, "") else configDialog.FIXATION_DURATION_DEFAULT,
    "fullScreen":        configDialogBank[9] if debug else True,
    "screenSize":        (1024, 768),
    "startTime":         time.time(),
    "port":              "COM4",
}

if not os.path.exists("./data"):
    os.mkdir("data")
with open("./data/FORTconfig.json", "w") as f:
    json.dump(params, f, indent=3)

print(f"===========================================\n"
      f"Starting FORT for Subject {params['Subject']}\n"
      f"===========================================")

# ---------------------------------------------------------------------------
# Physiology / serial
# ---------------------------------------------------------------------------
ser = (serial.Serial(params["port"], 115200, bytesize=serial.EIGHTBITS, timeout=1)
       if params["recordPhysio"] else None)

# Initialization event (255) — same as both NPU and TIM
serialHandler.report_event(ser, 255)

# ---------------------------------------------------------------------------
# Data frames
# ---------------------------------------------------------------------------
params, df, mini_df, mood_df = dataHandler.setup_data_frames(params)
params["startTime"] = time.time()

# Initial record
temp_dict = dataHandler.create_dict_for_df(params, Step="Start")
temp_dict["CurrentTime"] = 0.0
mini_df = pd.concat([mini_df, pd.DataFrame.from_records([temp_dict])])
del temp_dict

# ---------------------------------------------------------------------------
# Window & welcome screen
# ---------------------------------------------------------------------------
window = visual.Window(
    size=params["screenSize"], monitor="testMonitor",
    color=(0.6, 0.6, 0.6), winType="pyglet",
    fullscr=params["fullScreen"], units="pix")

image = visual.ImageStim(
    win=window,
    image=f"./img/instructions/Welcome_{params['gender'][0]}{params['language'][0]}.jpeg",
    units="norm", size=(2, 2))
image.draw()
window.update()
window.mouseVisible = False
helpers.wait_for_space_no_df(window, io)

# ---------------------------------------------------------------------------
# Pre-session mood VAS  (TIM-style, event code 90)
# ---------------------------------------------------------------------------
serialHandler.report_event(ser, serialHandler.BIOPAC_EVENTS['PreVas_rating'])
pre_scores = VAS.run_mood_vas(window, io, params)
mood_df = dataHandler.insert_data_mood("pre", pre_scores, mood_df)

# ---------------------------------------------------------------------------
# Instructions  (NPU-style numbered slides, optional)
# ---------------------------------------------------------------------------
if not params["skipInstructions"]:
    pref = f"{params['gender'][0]}{params['language'][0]}"
    keyboard = io.devices.keyboard
    for slide_num in range(1, 4):
        slide_path = f"./img/instructions/{slide_num}{pref}.jpeg"
        image.image = slide_path
        image.setSize((2, 2))
        image.draw()
        window.update()
        window.mouseVisible = False
        helpers.wait_for_space_no_df(window, io)

# ---------------------------------------------------------------------------
# Fixation cross before the P-block  (TIM-style, event code 95)
# Duration is the configurable fixationDuration parameter.
# ---------------------------------------------------------------------------
serialHandler.report_event(ser, serialHandler.BIOPAC_EVENTS['Fixation_cross'])
fixation_img = visual.ImageStim(
    win=window, image="./img/plus.jpeg", units="norm", size=(2, 2))
fixation_img.draw()
window.mouseVisible = False
window.flip()

# Wait exactly fixationDuration seconds using core.wait — identical to TIM's fixation_before_block
core.wait(float(params["fixationDuration"]))

# ---------------------------------------------------------------------------
# Single P-condition block  (NPU predictable-threat logic)
# Event codes inside block: 110 block-start, 120 cue-on, 130 cue-off,
#                            +1 startle, +2 shock  — all NPU conventions
# ---------------------------------------------------------------------------
sound_path = helpers.randomize_sounds()[0]
fear_level, df, mini_df = blockP.run_p_block(
    window=window, image=image, params=params, io=io,
    df=df, mini_df=mini_df, block_num=1,
    ser=ser, fear_level=5, sound=sound_path)

# Brief blank screen between block and post-VAS
blank = visual.ImageStim(win=window, image="./img/blank.jpeg", units="norm", size=(2, 2))
blank.draw()
window.update()
core.wait(2.0)

# ---------------------------------------------------------------------------
# Post-session mood VAS  (TIM-style, event code 92)
# ---------------------------------------------------------------------------
serialHandler.report_event(ser, serialHandler.BIOPAC_EVENTS['PostRun_rating'])
post_scores = VAS.run_mood_vas(window, io, params)
mood_df = dataHandler.insert_data_mood("post", post_scores, mood_df)

# ---------------------------------------------------------------------------
# Finish screen & data export
# ---------------------------------------------------------------------------
finish_image = visual.ImageStim(
    win=window,
    image=f"./img/finish{params['gender'][0]}{params['language'][0]}.jpeg",
    units="norm", size=(2, 2))
finish_image.draw()
window.mouseVisible = False
window.update()
helpers.wait_for_space_no_df(window, io)

dataHandler.export_data(params, fullDF=df, miniDF=mini_df, Mood=mood_df)

print("===========================================\nFORT task complete.\n===========================================")
window.close()
core.quit()
