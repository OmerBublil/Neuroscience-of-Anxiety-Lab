"""
Helper utilities for FORT assignment.
Adapted from NPU/helpers.py - includes timing randomization, startle/shock playback,
and wait functions needed for the P-condition block.
"""
import random
import time

import pandas as pd
from psychopy import visual, core, sound
from psychopy.iohub.client.keyboard import Keyboard
import psychtoolbox as ptb

import dataHandler
import serialHandler

# Constants mirrored from NPU blockP logic (kept here to avoid circular imports)
STARTLE_EVENT_INDEX = 1
SHOCK_EVENT_INDEX = 2
HABITUATION_EVENT = 80

SOUNDS = ["./sounds/shock_sound_1.mp3", "./sounds/shock_sound_2.mp3"]


# ---------------------------------------------------------------------------
# Wait helpers
# ---------------------------------------------------------------------------

def wait_for_space_no_df(window: visual.Window, io):
    keyboard = io.devices.keyboard
    keyboard.getKeys()
    core.wait(0.05)
    while True:
        for event in keyboard.getKeys(etype=Keyboard.KEY_PRESS):
            if event.key == " ":
                return
            if event.key == "escape":
                window.close()
                core.quit()


def wait_for_space(window: visual.Window, io, params: dict, df: pd.DataFrame, dict_for_df: dict):
    keyboard = io.devices.keyboard
    keyboard.getKeys()
    core.wait(0.05)
    while True:
        dict_for_df["CurrentTime"] = round(time.time() - params["startTime"], 2)
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])
        for event in keyboard.getKeys(etype=Keyboard.KEY_PRESS):
            if event.key == " ":
                return df
            if event.key == "escape":
                dataHandler.export_data(params, fullDF=df)
                window.close()
                core.quit()
        core.wait(0.05)


def wait_until_time_with_df(window: visual.Window, io, params: dict, df: pd.DataFrame, dict_for_df: dict, end_time):
    keyboard = io.devices.keyboard
    while time.time() < end_time:
        dict_for_df["CurrentTime"] = round(time.time() - params["startTime"], 2)
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])
        for event in keyboard.getKeys(etype=Keyboard.KEY_PRESS):
            if event.key == "escape":
                dataHandler.export_data(params, fullDF=df)
                window.close()
                core.quit()
        core.wait(0.01)
    return df


# ---------------------------------------------------------------------------
# Timing randomization (NPU logic, P-condition relevant)
# ---------------------------------------------------------------------------

def randomize_cue_times():
    random.seed()
    times = [random.randrange(8, 30), random.randrange(45, 70), random.randrange(85, 105)]
    times.sort()
    print(f"cue times - {times}")
    return times


def randomize_startles(cues: list, block_length=120, cue_length=12, startles_per_block=6):
    random.seed()
    seconds = list(range(2, block_length))
    startle_times = []
    for cue in cues:
        startle_times.append(round(random.uniform(cue + 2, cue + cue_length - 1), 2))
        for x in range(cue, cue + cue_length + 1):
            if x in seconds:
                seconds.remove(x)
    for i in range(startles_per_block - 3):
        chosen_sec = random.choice(seconds[int(i / 3 * len(seconds)): int((i + 1) / 3 * len(seconds))])
        startle_times.append(chosen_sec)
        seconds.remove(chosen_sec)
    startle_times.sort()
    print(f"startle times: {startle_times}")
    return startle_times


def randomize_shock(cues: list, startles: list, params: dict, block_length=120, cue_length=12):
    """
    Randomize predictable shock timing: shock falls within a cue window.
    Adapted from NPU helpers.randomize_shock (predictable=True branch only).
    """
    random.seed()
    cue_for_shock = round(random.choice([0, 1, 2]), 2)
    if params["skipStartle"]:
        shock_time = round(cues[cue_for_shock] + random.uniform(2, 10), 2)
    else:
        shock_time = round(cues[cue_for_shock] + random.uniform(6, 8), 2)
        # Adjust startle so it precedes shock by 1.5–3.5 s within the same cue
        cue_time = cues[cue_for_shock]
        new_startle = round(cue_time + random.uniform(1.5, 3.5), 2)
        for startle in list(startles):
            if cue_time < startle < cue_time + cue_length:
                startles.remove(startle)
                startles.append(new_startle)
                startles.sort()
    print(f"Shock is in {shock_time} seconds")
    print(f"Final startles: {startles}")
    return shock_time, startles


def prepare_cues_and_startles(cues: list, startles: list):
    start_time = time.time()
    cue_times = [cue + start_time for cue in cues]
    startle_times = [s + start_time for s in startles]
    return cue_times, startle_times


# ---------------------------------------------------------------------------
# Audio playback
# ---------------------------------------------------------------------------

def play_startle(dict_for_df: dict, df: pd.DataFrame, mini_df: pd.DataFrame, ser=None):
    dict_for_df["CurrentTime"] = round(time.time() - dict_for_df["StartTime"], 2)
    dict_for_df["Startle"] = 1
    dict_for_df["ScenarioIndex"] += STARTLE_EVENT_INDEX
    mini_df = pd.concat([mini_df, pd.DataFrame.from_records([dict_for_df])])
    if ser is not None:
        serialHandler.report_event(ser, dict_for_df["ScenarioIndex"])
    sound_obj = sound.Sound("./sounds/startle_probe_low.wav")
    now = ptb.GetSecs()
    now_for_while = time.time()
    sound_obj.play(when=now)
    while time.time() < now_for_while + 1:
        dict_for_df["CurrentTime"] = round(time.time() - dict_for_df["StartTime"], 2)
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])
        core.wait(0.05)
    dict_for_df.pop("Startle")
    dict_for_df["ScenarioIndex"] -= STARTLE_EVENT_INDEX
    return df, mini_df


def play_shock_sound(dict_for_df: dict, df: pd.DataFrame, sound_name=None):
    sound_path = sound_name if sound_name else "./sounds/shock_sound_1.mp3"
    sound_obj = sound.Sound(sound_path)
    now = ptb.GetSecs()
    sound_obj.play(when=now)
    now_for_while = time.time()
    while time.time() < now_for_while + 1.5:
        dict_for_df["CurrentTime"] = round(time.time() - dict_for_df["StartTime"], 2)
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])
        core.wait(0.05)
    return df


def randomize_sounds():
    numbers = [0, 1, 2, 3]
    random.shuffle(numbers)
    sounds_in_order = [SOUNDS[x % 2] for x in numbers]
    print(sounds_in_order)
    return sounds_in_order
