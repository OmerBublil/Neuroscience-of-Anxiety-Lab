"""
VAS module for FORT assignment.
run_mood_vas(): TIM-style 5-question mood scale shown before/after the session.

Hebrew RTL handling follows NPU/VAS.py convention:
  - RatingScale labels:  labels[i][::-1]  (string-reversed, same as both NPU and TIM)
  - Question TextStim:   languageStyle='RTL', text NOT reversed  (NPU convention)
  - acceptText / acceptPreText strings are reversed where Hebrew
"""
import time

import pandas as pd
from psychopy import visual, core
from psychopy.iohub.client.keyboard import Keyboard
from psychopy.visual import ratingscale

# TIM-style mood VAS questions and answer labels
LABELS = ["Anxiety", "Tiredness", "Worry", "Mood", "PainSensitivity"]

QUESTIONS_HEBREW = [
    "עד כמה אתם מרגישים חרדה או לחץ כרגע?",
    "עד כמה אתם עייפים?",
    "עד כמה אתם מודאגים מהחלק הבא?",
    "איך מצב הרוח שלכם כרגע?",
    "עד כמה אתם רגישים לכאב?",
]
QUESTIONS_ENGLISH = [
    "How stressed or anxious are you feeling?",
    "How tired are you?",
    "How worried are you for the next part?",
    "How's your mood right now?",
    "How sensitive are you to pain?",
]

ANSWERS_HEBREW = [
    ["כלל לא", "הרבה מאוד"],
    ["כלל לא", "הרבה מאוד"],
    ["כלל לא", "הרבה מאוד"],
    ["רע מאוד", "טוב מאוד"],
    ["כלל לא", "הרבה מאוד"],
]
ANSWERS_ENGLISH = [
    ["Not at all", "A lot"],
    ["Not at all", "A lot"],
    ["Not at all", "A lot"],
    ["Very bad", "Very good"],
    ["Not at all", "A lot"],
]


def run_mood_vas(window: visual.Window, io, params: dict) -> dict:
    """
    Display TIM-style 5-question mood VAS.
    Returns a dict mapping LABELS -> score (0-10).

    Hebrew RTL:
      - Scale edge labels are [::-1] reversed (matches NPU + TIM)
      - Question text uses languageStyle='RTL' without reversal (matches NPU/VAS.py)
      - Accept button text reversed for Hebrew (matches TIM/VAS.py)
    """
    keyboard = io.devices.keyboard
    is_hebrew = params["language"] == "Hebrew"
    questions = QUESTIONS_HEBREW if is_hebrew else QUESTIONS_ENGLISH
    answers = ANSWERS_HEBREW if is_hebrew else ANSWERS_ENGLISH
    scores = {}

    for i, question in enumerate(questions):
        lbl_left, lbl_right = answers[i]

        # Labels reversed for Hebrew (both NPU and TIM do this)
        scale_labels = [lbl_left[::-1], lbl_right[::-1]] if is_hebrew else [lbl_left, lbl_right]

        # Accept button text reversed for Hebrew (matches TIM/VAS.py)
        accept_text     = "לחצו לנעילה"[::-1] if is_hebrew else "Press to Lock"
        accept_pre_text = "לחצו לנעילה"[::-1] if is_hebrew else "Press to Lock"

        scale = ratingscale.RatingScale(
            window,
            labels=scale_labels,
            scale=None, choices=None, low=0, high=10, precision=0.5,
            tickHeight=0, size=2, markerStart=5, noMouse=True,
            leftKeys=['left', 'b'], rightKeys=['right', 'd'],
            textSize=0.6,
            acceptText=accept_text,
            showValue=False, showAccept=True,
            acceptPreText=accept_pre_text, acceptSize=1.5,
            markerColor="Maroon", acceptKeys=["space", 'c'],
            textColor="Black", lineColor="Black", disappear=False)

        # Question text: languageStyle='RTL' without string reversal (NPU/VAS.py convention)
        question_stim = visual.TextStim(
            window,
            text=question,
            height=0.12, units='norm', pos=[0, 0.3], wrapWidth=2,
            languageStyle='RTL' if is_hebrew else 'LTR',
            font="Open Sans", color="Black")

        keyboard.getKeys()
        core.wait(0.05)

        while scale.noResponse:
            scale.draw()
            question_stim.draw()
            window.mouseVisible = False
            window.flip()
            for ev in keyboard.getKeys(etype=Keyboard.KEY_PRESS):
                if ev.key == "escape":
                    window.close()
                    core.quit()

        scores[LABELS[i]] = scale.getRating()

    return scores
