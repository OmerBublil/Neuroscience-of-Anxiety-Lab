"""
P-condition block for FORT assignment.
Extracted from NPU/blocksInfra.py — only the Predictable (P) condition is implemented.

Behavior: cue is presented → threat (shock/sound) ALWAYS occurs after the cue (predictable threat).
"""
import time

import pandas as pd
from psychopy import visual, core
from psychopy.iohub.client.keyboard import Keyboard
from psychopy.visual import ratingscale

import helpers
import dataHandler
import serialHandler

BLOCK_LENGTH = 120
CUE_LENGTH = 12
STARTLES_PER_BLOCK = 6

SCENARIO_PREFIX_P = 100       # NPU convention: P condition index base
STARTLE_EVENT_INDEX = helpers.STARTLE_EVENT_INDEX
SHOCK_EVENT_INDEX = helpers.SHOCK_EVENT_INDEX
CONDITION_START_INDEX = 10
CUE_START_INDEX = 20
CUE_END_INDEX = 30

SCALE_LABEL_HEB = "רמת חרדה"
SCALE_LABEL_ENG = "Anxiety Level"

IMG_PATH = "./img/blocks/"
IMG_SUFFIX = ".jpeg"


def run_p_block(window: visual.Window, image: visual.ImageStim, params: dict, io,
                df: pd.DataFrame, mini_df: pd.DataFrame, block_num: int = 1,
                ser=None, fear_level: float = 5, sound=None):
    """
    Run a single Predictable (P) condition block (120 seconds).
    A cue is displayed at randomized times; a threat always follows each cue onset.

    Returns: fear_level, df, mini_df
    """
    window.mouseVisible = False
    print("Starting FORT P-condition block")

    cue_times = helpers.randomize_cue_times()
    if not params["skipStartle"]:
        startle_times = helpers.randomize_startles(cue_times, BLOCK_LENGTH, CUE_LENGTH, STARTLES_PER_BLOCK)
    else:
        startle_times = []

    dict_for_df = dataHandler.create_dict_for_df(params, Step="Game", Block=block_num, Scenario="Predictable")
    dict_for_df["ScenarioIndex"] = SCENARIO_PREFIX_P + CONDITION_START_INDEX
    dict_for_df["CurrentTime"] = round(time.time() - dict_for_df["StartTime"], 2)
    condition_start = time.time()
    dict_for_df["TimeInCondition"] = round(time.time() - condition_start, 2)
    mini_df = pd.concat([mini_df, pd.DataFrame.from_records([dict_for_df])])

    if params["recordPhysio"]:
        serialHandler.report_event(ser, dict_for_df["ScenarioIndex"])

    # Strip the condition-start offset; keep only the P-condition base
    dict_for_df["ScenarioIndex"] -= CONDITION_START_INDEX

    # Randomize predictable shock time (always within a cue window)
    shock_time, startle_times = helpers.randomize_shock(cue_times, startle_times, params, BLOCK_LENGTH, CUE_LENGTH)
    shock_time = shock_time + time.time()

    cue_times, startle_times = helpers.prepare_cues_and_startles(cue_times, startle_times)

    timing_index = 0
    start_time = time.time()

    while time.time() < start_time + BLOCK_LENGTH:
        image.image = f"{IMG_PATH}P_{params['language'][0]}{IMG_SUFFIX}"
        image.setSize((2, 2))
        image.draw()
        window.update()
        window.mouseVisible = False

        fear_level, df, mini_df = _launch_wait_sequence(
            params=params, window=window, image=image,
            end_time=cue_times[timing_index] if timing_index < 3 else start_time + BLOCK_LENGTH,
            startles=startle_times, io=io, shock_time=shock_time, fear_level=fear_level,
            dict_for_df=dict_for_df, df=df, mini_df=mini_df, ser=ser,
            condition_start=condition_start, sound=sound)

        if timing_index == 3:
            pass
        elif cue_times[timing_index] <= time.time() <= cue_times[timing_index] + 1:
            print("Entering cue")
            current_cue_time = time.time()
            image.image = f"{IMG_PATH}P_{params['language'][0]}_Cue{IMG_SUFFIX}"
            image.setSize((2, 2))

            fear_level, df, mini_df = _launch_wait_sequence(
                params=params, window=window, image=image,
                end_time=current_cue_time + CUE_LENGTH,
                startles=startle_times, io=io, shock_time=shock_time, fear_level=fear_level,
                cue=True, dict_for_df=dict_for_df, df=df, mini_df=mini_df, ser=ser,
                condition_start=condition_start, sound=sound)
            timing_index += 1
            print("Leaving cue")

    dataHandler.save_backup(params=params, fullDF=df, miniDF=mini_df)
    return fear_level, df, mini_df


def _launch_wait_sequence(params, window, image, end_time, startles, io, dict_for_df, df, mini_df,
                           shock_time=0, fear_level=5, cue=False, ser=None, condition_start=0.0, sound=None):
    if cue:
        dict_for_df["CueStart"] = round(time.time() - condition_start, 2)
        dict_for_df["ScenarioIndex"] += CUE_START_INDEX
    else:
        dict_for_df["ScenarioIndex"] += CUE_END_INDEX

    if params["recordPhysio"]:
        serialHandler.report_event(ser, dict_for_df["ScenarioIndex"])

    dict_for_df["Cue"] = 1 if cue else 0
    dict_for_df["CurrentTime"] = round(time.time() - dict_for_df["StartTime"], 2)
    dict_for_df["TimeInCondition"] = round(time.time() - condition_start, 2)
    mini_df = pd.concat([mini_df, pd.DataFrame.from_records([dict_for_df])])
    df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])

    startles_filtered = [s for s in startles if time.time() <= s <= end_time]
    print(f"startles_filtered: {startles_filtered}")

    if shock_time != 0 and time.time() <= shock_time <= end_time:
        print("starting wait with shock")
        fear_level, df, mini_df = _wait_in_condition(
            params=params, window=window, image=image, startle_times=startles_filtered,
            end_time=end_time, shock_time=shock_time, io=io, fear_level=fear_level,
            dict_for_df=dict_for_df, df=df, mini_df=mini_df, ser=ser,
            condition_start=condition_start, sound=sound)
    else:
        print("starting wait without shock")
        fear_level, df, mini_df = _wait_in_condition(
            params=params, window=window, image=image, startle_times=startles_filtered,
            end_time=end_time, io=io, fear_level=fear_level,
            dict_for_df=dict_for_df, df=df, mini_df=mini_df, ser=ser,
            condition_start=condition_start, sound=sound)

    if cue:
        dict_for_df["CueEnd"] = round(time.time() - condition_start, 2)
        dict_for_df["CurrentTime"] = round(time.time() - dict_for_df["StartTime"], 2)
        dict_for_df["TimeInCondition"] = round(time.time() - condition_start, 2)
        mini_df = pd.concat([mini_df, pd.DataFrame.from_records([dict_for_df])])
        dict_for_df.pop("CueEnd")
        dict_for_df.pop("CueStart")
        dict_for_df["ScenarioIndex"] -= CUE_START_INDEX
    else:
        dict_for_df["ScenarioIndex"] -= CUE_END_INDEX

    return fear_level, df, mini_df


def _wait_in_condition(window, image, startle_times, end_time, io, params, dict_for_df, df, mini_df,
                        fear_level=5, shock_time=0, ser=None, condition_start=0.0, sound=None):
    keyboard = io.devices.keyboard
    scale = ratingscale.RatingScale(
        win=window, scale=None, labels=["0", "10"], low=0, high=10,
        markerStart=fear_level, showAccept=False, markerColor="Gray",
        textColor="Black", lineColor="Black",
        pos=(0, -window.size[1] / 2 + 150))

    scale_label = visual.TextStim(
        win=window,
        text=SCALE_LABEL_ENG if params["language"] == "English" else SCALE_LABEL_HEB,
        pos=(0, -window.size[1] / 2 + 250), color="Black",
        languageStyle="LTR" if params["language"] == "English" else "RTL", height=40)

    while time.time() <= end_time:
        image.draw()
        scale.draw()
        scale_label.draw()
        window.flip()
        window.mouseVisible = False

        dict_for_df["CurrentTime"] = round(time.time() - dict_for_df["StartTime"], 2)
        dict_for_df["FearRating"] = scale.getRating()
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])

        dict_for_df["TimeInCondition"] = round(time.time() - condition_start, 2)
        if startle_times and startle_times[0] <= time.time() <= startle_times[0] + 0.5:
            df, mini_df = helpers.play_startle(dict_for_df, df, mini_df, ser)
            startle_times.remove(startle_times[0])
        if shock_time and shock_time <= time.time() <= shock_time + 0.3:
            df, mini_df = _initiate_shock(window, params, dict_for_df, df, mini_df, ser, sound)

        for event in keyboard.getKeys(etype=Keyboard.KEY_PRESS):
            if event.key == "escape":
                dataHandler.export_data(params, fullDF=df, miniDF=mini_df)
                window.close()
                core.quit()

    print(f"Scale Rating: {scale.getRating()}")
    return scale.getRating(), df, mini_df


def _initiate_shock(window, params, dict_for_df, df, mini_df, ser=None, sound=None):
    dict_for_df["CurrentTime"] = round(time.time() - dict_for_df["StartTime"], 2)
    dict_for_df["Shock"] = 1
    dict_for_df["ScenarioIndex"] += SHOCK_EVENT_INDEX
    mini_df = pd.concat([mini_df, pd.DataFrame.from_records([dict_for_df])])

    if ser is not None:
        serialHandler.report_event(ser, dict_for_df["ScenarioIndex"])

    if params["shockType"] == "Shock":
        pass  # Physical shock device hook (not implemented)
    else:
        df = helpers.play_shock_sound(dict_for_df, df, sound)

    dict_for_df.pop("Shock")
    dict_for_df["ScenarioIndex"] -= SHOCK_EVENT_INDEX
    return df, mini_df
