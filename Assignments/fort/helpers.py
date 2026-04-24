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
        core.wait(0.05)


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


# ---------------------------------------------------------------------------
# TIM timing helpers
# ---------------------------------------------------------------------------

PRE_BLOCK_FIXATION_TIME = 8


def create_timing_array(params):
    random.seed(time.time())
    while True:
        timings = []
        for i in range(params['nTrials']):
            timing_dict = {
                'preITI': random.uniform(params['preITIMin'], params['preITIMax']),
                'squareOnset': params['secondParadigmSquareOnset'],
                'squareBlankScreen': params['secondParadigmSquareBlankScreen'],
                'squareJitter': random.uniform(params['secondParadigmJitterMin'], params['secondParadigmJitterMax']),
                'painTime': 6,
                'preRatingITI': params['preRatingITI'],
                'painRating': params['painRateDuration'],
                'postITI': random.uniform(params['postITIMin'], params['postITIMax']),
            }
            timings.append(timing_dict)
        timings_sum = sum_timing_array(timings) + PRE_BLOCK_FIXATION_TIME
        print(f"Timing Sum = {timings_sum}\n==================================")
        if 235 <= timings_sum <= 240:
            return timings


def sum_timing_array(timings: list):
    time_sum = 0
    for timing_dict in timings:
        time_sum += sum(timing_dict.values())
    return time_sum


def tim_wait_for_time(window: visual.Window, params, mood_df, pain_df, start_time, display_time, keyboard, event_onset_df=None):
    while time.time() < start_time + display_time:
        for event in keyboard.getKeys():
            if event.key == "escape":
                tim_graceful_shutdown(window, params, mood_df, pain_df, event_onset_df)
        core.wait(0.05)


def tim_iti(window: visual.Window, params, keyboard, mood_df, pain_df, display_time, event_onset_df=None):
    square = visual.ImageStim(window, image="./img/blank.jpeg", units="norm", size=(2, 2))
    square.draw()
    window.mouseVisible = False
    window.flip()
    start_time = time.time()
    tim_wait_for_time(window, params, mood_df, pain_df, start_time, display_time, keyboard, event_onset_df)


def tim_fixation_before_block(window: visual.Window, params, mood_df, pain_df, keyboard, event_onset_df=None):
    image = visual.ImageStim(window, "./img/plus.jpeg", units="norm", size=(2, 2))
    image.draw()
    window.mouseVisible = False
    window.flip()
    tim_wait_for_time(window, params, mood_df, pain_df, time.time(), params['fixationBeforeBlock'], keyboard, event_onset_df)


def tim_wait_for_time_with_periodic_events(window, params, mood_df, pain_df, start_time, display_time, keyboard, prefix, sec, event_onset_df):
    T_TO_HEAT = {'T2': 1, 'T4': 2, 'T8': 3}
    while time.time() < start_time + display_time:
        if sec <= time.time() - start_time <= sec + 0.1:
            print(f"Sending event. Timediff: {time.time() - start_time}, sec: {sec}")
            event_onset_df = tim_add_event(params, f'{prefix}_{sec}', 2, T_TO_HEAT[prefix], event_onset_df)
            sec += 2
        for ev in keyboard.getKeys():
            if ev.key == "escape":
                tim_graceful_shutdown(window, params, mood_df, pain_df, event_onset_df)
        core.wait(0.02)
    return sec, event_onset_df


def show_waiting_for_next_block(window: visual.Window, params: dict):
    img = f"./img/wait_E.jpeg" if params['language'] == 'English' else f"./img/wait_{params['gender'][0]}.jpeg"
    image = visual.ImageStim(window, img, units="norm", size=(2, 2))
    image.draw()
    window.flip()


def show_waiting_for_ra_space(window: visual.Window, params: dict):
    img = f"./img/waitForSpace_E.jpeg" if params['language'] == 'English' else f"./img/waitForSpace_H.jpeg"
    image = visual.ImageStim(window, img, units="norm", size=(2, 2))
    image.draw()
    window.flip()


def tim_add_event(params: dict, event_name: str, event_time, heat_level, event_onset_file: pd.DataFrame):
    event = serialHandler.PARADIGM_2_BIOPAC_EVENTS[event_name]
    serialHandler.report_event(params['serialBiopac'], event)
    return dataHandler.insert_data_fmri_events(params, event_time, event, heat_level, event_onset_file)


def tim_graceful_shutdown(window, params, mood_df, pain_df, event_onset_df=None):
    dataHandler.export_data(params, Mood=mood_df, Pain=pain_df)
    dataHandler.save_fmri_event_onset(params, event_onset_df, "backup")
    print("Experiment Ended\n===========================================")
    window.close()
    core.quit()
    exit()


def tim_wait_for_space(window: visual.Window, params, mood_df, pain_df, io, event_onset_df=None):
    keyboard = io.devices.keyboard
    keyboard.getKeys()
    core.wait(0.1)
    while True:
        for event in keyboard.getKeys():
            if event.key in [" ", 'c']:
                return
            elif event.key == "escape":
                tim_graceful_shutdown(window, params, mood_df, pain_df, event_onset_df)
        core.wait(0.05)
