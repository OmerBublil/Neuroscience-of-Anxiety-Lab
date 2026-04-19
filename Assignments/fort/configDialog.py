"""
Configuration dialog for FORT assignment.
Combines NPU fields (shock type, startles, physio) with TIM fields (fixation duration).
Saves to FORTconfig.json for pre-filling on next run.
"""
import os
from psychopy import gui
import json

FIXATION_DURATION_DEFAULT = 8  # seconds (matches TIM's fixationBeforeBlock default)


def get_user_input(debug=False):
    """
    Gather initial configuration for the FORT task via a GUI dialog.
    Returns an answer array indexed as documented below.
    """
    loaded_data = {}
    config_exists = False
    if os.path.exists("./data/FORTconfig.json"):
        with open("./data/FORTconfig.json") as file:
            try:
                loaded_data = json.load(file)
                config_exists = True
            except json.decoder.JSONDecodeError:
                pass

    userInput = gui.Dlg(title="FORT Task Configuration")
    # [0] Subject
    userInput.addField('Subject Number:')
    # [1] Session
    userInput.addField('Session:', 1)
    # [2] Gender
    userInput.addField('Gender',
                       "Female" if not config_exists else loaded_data.get("gender", "Female"),
                       choices=["Male", "Female"])
    # [3] Language
    userInput.addField("Preferred Language",
                       "Hebrew" if not config_exists else loaded_data.get("language", "Hebrew"),
                       choices=["Hebrew", "English"])
    # [4] Shock type
    userInput.addField("Shock Type",
                       "Sound" if not config_exists else loaded_data.get("shockType", "Sound"),
                       choices=["Shock", "Sound"])
    # [5] Skip startles
    userInput.addField("Skip Startles",
                       False if not config_exists else loaded_data.get("skipStartle", False))
    # [6] Record physiology
    userInput.addField('Record Physiology',
                       False if not config_exists else loaded_data.get("recordPhysio", False))
    # [7] Skip instructions
    userInput.addField('Skip Instructions',
                       False if not config_exists else loaded_data.get("skipInstructions", False))
    # [8] Fixation duration (seconds) — shown before the P-condition block
    userInput.addField('Fixation Duration (sec)',
                       FIXATION_DURATION_DEFAULT if not config_exists
                       else loaded_data.get("fixationDuration", FIXATION_DURATION_DEFAULT))
    # [9] / [10] / [11] — debug-only fields
    if debug:
        userInput.addField('Full Screen',
                           True if not config_exists else loaded_data.get("fullScreen", True))
        userInput.addField('Save Data at Unexpected Quit', False)
        userInput.addField('Save Config as Default', False)

    return userInput.show()
