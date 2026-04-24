"""
FORT Task — main entry point.

Session structure:
  1. Config dialog
  2. Welcome screen  (space to continue)
  3. Pre-session mood VAS  →  BioPac PreVas_rating (90)
  4. Instruction slides (optional)
  5. Fixation cross  →  BioPac Fixation_cross (95), configurable duration
  6. P-condition block  (NPU predictable threat, 120 s)
  7. TIM block  (single block, 6 trials, ~235-240 s)
  8. Post-session mood VAS  →  BioPac PostRun_rating (92)
  9. Finish screen
 10. Export fullDF, miniDF (NPU), Mood, Pain (TIM)

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
import timBlock
import npuInstructions
import timInstructions

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
    "fmriVersion":       configDialogBank[9],
    "T2temp":            configDialogBank[10],
    "T4temp":            configDialogBank[11],
    "T8temp":            configDialogBank[12],
    "painSupport":       configDialogBank[13],
    "fullScreen":        configDialogBank[14] if debug else True,
    "screenSize":        (1024, 768),
    "startTime":         time.time(),
    "port":              "COM4",
    # TIM block params
    'nTrials':                      6,
    'temps':                        [configDialogBank[10], configDialogBank[11], configDialogBank[12]],
    'Ts':                           ['T2', 'T4', 'T8'],
    'colors':                       ['Green', 'Yellow', 'Red'],
    'fixationBeforeBlock':          8,
    'preITIMin':                    3,
    'preITIMax':                    5,
    'postITIMin':                   7,
    'postITIMax':                   9,
    'painRateDuration':             7.0,
    'secondParadigmSquareOnset':    2,
    'secondParadigmSquareBlankScreen': 8,
    'secondParadigmJitterMin':      0,
    'secondParadigmJitterMax':      1,
    'preRatingITI':                 2,
    'fmriStartTime':                0,
    # NPU instruction params
    'calibrationTime':              int(configDialogBank[8]) if configDialogBank[8] not in (None, "") else configDialog.FIXATION_DURATION_DEFAULT,
    'skipCalibration':              True,   # calibration handled by separate fixation screen
    'videosTiming':                 'After',
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
params['serialBiopac'] = ser

serialHandler.report_event(ser, 255)

# ---------------------------------------------------------------------------
# Data frames
# ---------------------------------------------------------------------------
params, df, mini_df, mood_df, pain_df = dataHandler.setup_data_frames(params)
params["startTime"] = time.time()

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
# Pre-session mood VAS  (event 90)
# ---------------------------------------------------------------------------
serialHandler.report_event(ser, serialHandler.BIOPAC_EVENTS['PreVas_rating'])
pre_scores = VAS.run_mood_vas(window, io, params)
mood_df = dataHandler.insert_data_mood("pre", pre_scores, mood_df)

# ---------------------------------------------------------------------------
# NPU Instructions  (identical to original NPU assignment)
# ---------------------------------------------------------------------------
if not params["skipInstructions"]:
    df, mini_df = npuInstructions.show_instructions(params, window, image, io, df, mini_df, ser)

# ---------------------------------------------------------------------------
# Fixation cross before P-block  (event 95)
# ---------------------------------------------------------------------------
serialHandler.report_event(ser, serialHandler.BIOPAC_EVENTS['Fixation_cross'])
fixation_img = visual.ImageStim(
    win=window, image="./img/plus.jpeg", units="norm", size=(2, 2))
fixation_img.draw()
window.mouseVisible = False
window.flip()
time.sleep(float(params["fixationDuration"]))

# ---------------------------------------------------------------------------
# P-condition block  (NPU predictable threat, 120 s)
# ---------------------------------------------------------------------------
sound_path = helpers.randomize_sounds()[0]
fear_level, df, mini_df = blockP.run_p_block(
    window=window, image=image, params=params, io=io,
    df=df, mini_df=mini_df, block_num=1,
    ser=ser, fear_level=5, sound=sound_path)

blank = visual.ImageStim(win=window, image="./img/blank.jpeg", units="norm", size=(2, 2))
blank.draw()
window.update()
core.wait(2.0)

# ---------------------------------------------------------------------------
# TIM Instructions  (identical to original TIM assignment)
# ---------------------------------------------------------------------------
if not params["skipInstructions"]:
    timInstructions.instructions(window, params, io)

# ---------------------------------------------------------------------------
# TIM block  (single block, ~235-240 s)
# ---------------------------------------------------------------------------
pain_df, event_onset_df = timBlock.run_tim_block(
    window=window, params=params, io=io,
    pain_df=pain_df, mood_df=mood_df, block_number=1)

blank.draw()
window.update()
core.wait(2.0)

# ---------------------------------------------------------------------------
# Post-session mood VAS  (event 92)
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

dataHandler.export_data(params, fullDF=df, miniDF=mini_df, Mood=mood_df, Pain=pain_df)
dataHandler.save_fmri_event_onset(params, event_onset_df, 1)

print("===========================================\nFORT task complete.\n===========================================")
window.close()
core.quit()
