"""
NPU-style instruction screens for FORT.
Mirrors NPU/instructionsScreen.show_instructions() using fort's own modules.
Does NOT modify NPU. Uses the same slide images via fort/img/instructions (symlink to NPU/img/instructions).
"""
import time

import pandas as pd
import psychtoolbox as ptb
from psychopy import visual, core, sound
from psychopy.iohub.client.keyboard import Keyboard
from psychopy.visual import ratingscale

import dataHandler
import serialHandler

PATH = "./img/instructions/"
SUFFIX = ".jpeg"
SLIDES = 36
SHOCK_SLIDE = 6
STARTLE_SLIDE = 30
RATING_SLIDE = 29
CALIBRATION_SLIDE = 3


# ---------------------------------------------------------------------------
# Internal wait helpers (mirrors NPU/helpers.py — kept here to avoid polluting
# fort/helpers.py with NPU-specific signatures)
# ---------------------------------------------------------------------------

def _wait_for_space(window, io, params, df, dict_for_df):
    keyboard = io.devices.keyboard
    keyboard.getKeys()
    core.wait(0.05)
    while True:
        dict_for_df["CurrentTime"] = round(time.time() - params["startTime"], 2)
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])
        for ev in keyboard.getKeys(etype=Keyboard.KEY_PRESS):
            if ev.key == " ":
                return df
            if ev.key == "escape":
                dataHandler.export_data(params, fullDF=df)
                window.close()
                core.quit()
        core.wait(0.05)


def _wait_for_space_with_replay(window, io, params, df, dict_for_df):
    keyboard = io.devices.keyboard
    keyboard.getKeys()
    core.wait(0.05)
    while True:
        dict_for_df["CurrentTime"] = round(time.time() - params["startTime"], 2)
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])
        for ev in keyboard.getKeys():
            if ev.key in ('r', 'R'):
                return True, df
            elif ev.key == ' ':
                return False, df
            elif ev.key == "escape":
                dataHandler.export_data(params, fullDF=df)
                window.close()
                core.quit()
        core.wait(0.05)


def _wait_for_calibration(window, io, params, df, mini_df, dict_for_df, ser=None):
    keyboard = io.devices.keyboard
    start_time = time.time()
    dict_for_df["Step"] = "Calibration"
    dict_for_df["CurrentTime"] = round(time.time() - params["startTime"], 2)
    dict_for_df["ScenarioIndex"] = 99
    if params.get("recordPhysio") and ser:
        serialHandler.report_event(ser, dict_for_df["ScenarioIndex"])
    mini_df = pd.concat([mini_df, pd.DataFrame.from_records([dict_for_df])])
    dict_for_df.pop("ScenarioIndex")
    while time.time() < start_time + params["calibrationTime"]:
        dict_for_df["CurrentTime"] = round(time.time() - params["startTime"], 2)
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])
        for ev in keyboard.getKeys(etype=Keyboard.KEY_PRESS):
            if ev.key == "escape":
                dataHandler.export_data(params, fullDF=df, miniDF=mini_df)
                window.close()
                core.quit()
        core.wait(0.05)
    return df, mini_df


def _play_sound_and_wait(window, io, params, df, dict_for_df, sound_type):
    sound_path = "./sounds/shock_sound_1.mp3" if sound_type == "Scream" else "./sounds/startle_probe_low.wav"
    sound_obj = sound.Sound(sound_path)
    core.wait(3)
    sound_obj.play(when=ptb.GetSecs())
    end_time = time.time() + 2
    keyboard = io.devices.keyboard
    while time.time() < end_time:
        dict_for_df["CurrentTime"] = round(time.time() - params["startTime"], 2)
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])
        for ev in keyboard.getKeys(etype=Keyboard.KEY_PRESS):
            if ev.key == "escape":
                dataHandler.export_data(params, fullDF=df)
                window.close()
                core.quit()
        core.wait(0.05)
    while True:
        for ev in keyboard.getKeys(etype=Keyboard.KEY_PRESS):
            if ev.key == "escape":
                dataHandler.export_data(params, fullDF=df)
                window.close()
                core.quit()
            elif ev.key == " ":
                return df
        core.wait(0.05)


def _wait_for_space_with_rating_scale(window, img, io, params, df, dict_for_df):
    keyboard = io.devices.keyboard
    scale = ratingscale.RatingScale(
        win=window, scale=None, labels=["0", "10"], low=0, high=10, markerStart=5,
        showAccept=False, markerColor="Gray", acceptKeys=["space"],
        textColor="Black", lineColor="Black",
        pos=(0, -window.size[1] / 2 + 200))
    while scale.noResponse:
        dict_for_df["CurrentTime"] = round(time.time() - params["startTime"], 2)
        dict_for_df["FearRating"] = scale.getRating()
        df = pd.concat([df, pd.DataFrame.from_records([dict_for_df])])
        img.draw()
        scale.draw()
        window.flip()
    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def show_instructions(params: dict, window: visual.Window, img: visual.ImageStim,
                      io, df: pd.DataFrame, mini_df: pd.DataFrame, ser=None):
    """
    Show NPU instruction slides identically to NPU/instructionsScreen.show_instructions().
    Uses fort/img/instructions/ (symlink to NPU/img/instructions/).
    params must contain: gender, language, startTime, skipStartle,
                         skipCalibration, videosTiming, calibrationTime.
    """
    pref = f"{params['gender'][0]}{params['language'][0]}"
    dict_for_df = dataHandler.create_dict_for_df(params, Step="Instructions")
    window.mouseVisible = False

    videos_timing = params.get('videosTiming', 'After')
    skip_calibration = params.get('skipCalibration', False)

    replay = True
    plays_again = False
    while replay:
        slide_range = range(2, SLIDES) if videos_timing == "Before" else range(1, SLIDES)
        for i in slide_range:
            if (skip_calibration or videos_timing == "Before") and i in [2, 3, 4]:
                continue
            if params.get("skipStartle", False) and i == STARTLE_SLIDE:
                continue
            if plays_again and i in [2, 3, 4]:
                continue

            dict_for_df["CurrentTime"] = round(time.time() - params["startTime"], 2)
            img.image = f"{PATH}{i}{pref}{SUFFIX}"
            img.setSize((2, 2))
            img.draw()
            window.update()

            if i == CALIBRATION_SLIDE:
                df, mini_df = _wait_for_calibration(window, io, params, df, mini_df, dict_for_df, ser)
                dict_for_df["Step"] = "Instructions"
            elif i == SHOCK_SLIDE:
                df = _play_sound_and_wait(window, io, params, df, dict_for_df, "Scream")
            elif i == RATING_SLIDE:
                df = _wait_for_space_with_rating_scale(window, img, io, params, df, dict_for_df)
            elif i == STARTLE_SLIDE:
                df = _play_sound_and_wait(window, io, params, df, dict_for_df, "Startle")
            else:
                df = _wait_for_space(window, io, params, df, dict_for_df)

        # Last slide
        img.image = f"{PATH}{SLIDES}{pref}{SUFFIX}"
        img.setSize((2, 2))
        img.draw()
        window.update()
        replay, df = _wait_for_space_with_replay(window, io, params, df, dict_for_df)
        plays_again = replay

    return df, mini_df
