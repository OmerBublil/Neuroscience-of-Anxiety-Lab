"""
Data handling for FORT assignment.

Three DataFrames:
  fullDF / miniDF  — NPU-style continuous and event-level data (P-condition block)
  mood_df          — TIM-style pre/post session mood ratings
  pain_df          — TIM-style trial pain ratings (TIM block)
  event_onset_df   — TIM-style fMRI BIDS onset file (TIM block)
"""
import os
import datetime
import pandas as pd
from time import strftime, localtime
import time

# ---------------------------------------------------------------------------
# NPU-style headers (fullDF / miniDF)
# ---------------------------------------------------------------------------
HEADERS = [
    'ExperimentName',
    'Subject',
    'Session',
    'StartTime',
    'CurrentTime',
    'Step',
    'Block',
    'Scenario',
    'TimeInCondition',
    'Cue',
    'Startle',
    'Shock',
    'FearRating',
    'CueStart',
    'CueEnd',
    'ScenarioIndex',
    'ShockType',
    'VAS_score',
    'VAS_type',
    'VAS_RT',
]

# ---------------------------------------------------------------------------
# TIM-style headers
# ---------------------------------------------------------------------------
HEADERS_MOOD = ['Round', 'Label', 'Score']

HEADERS_PAIN = ['Block', 'Trial', 'TempNumber', 'Color', 'Pain']

HEADERS_FMRI_ONSET = ['onset', 'duration', 'condition', 'amplitude']


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def setup_data_frames(params: dict):
    params['headers'] = HEADERS
    df       = pd.DataFrame(columns=HEADERS)
    mini_df  = pd.DataFrame(columns=HEADERS)
    mood_df  = pd.DataFrame(columns=HEADERS_MOOD)
    pain_df  = pd.DataFrame(columns=HEADERS_PAIN)
    return params, df, mini_df, mood_df, pain_df


def setup_fmri_onset_file():
    return pd.DataFrame(columns=HEADERS_FMRI_ONSET)


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def create_dict_for_df(params: dict, **kwargs):
    """NPU-style event row."""
    d = {h: None for h in params['headers']}
    d['ExperimentName'] = 'FORT'
    d['Subject']        = params['Subject']
    d['StartTime']      = params['startTime']
    d['Session']        = params['session']
    d['ShockType']      = params['shockType']
    for k, v in kwargs.items():
        if k in d:
            d[k] = v
    return d


def insert_data_mood(round_label: str, scores: dict, mood_df: pd.DataFrame):
    """TIM-style mood row."""
    for label, score in scores.items():
        row = {'Round': round_label, 'Label': label, 'Score': score}
        mood_df = pd.concat([mood_df, pd.DataFrame.from_records([row])])
    return mood_df


def insert_data_pain(block, trial, temp_number, color, pain, pain_df: pd.DataFrame):
    """TIM-style pain row — identical to TIM/dataHandler.insert_data_pain."""
    row = {h: None for h in HEADERS_PAIN}
    row['Block']      = block
    row['Trial']      = trial
    row['TempNumber'] = temp_number
    row['Color']      = color
    row['Pain']       = pain
    return pd.concat([pain_df, pd.DataFrame.from_records([row])])


def insert_data_fmri_events(params: dict, duration: float, event: int,
                             heat_level: int, event_onset: pd.DataFrame):
    """TIM-style fMRI onset row — identical to TIM/dataHandler.insert_data_fmri_events."""
    row = {h: None for h in HEADERS_FMRI_ONSET}
    row['onset']     = round(time.time() - params['fmriStartTime'], 2)
    row['duration']  = round(duration, 2)
    row['condition'] = event
    row['amplitude'] = heat_level
    return pd.concat([event_onset, pd.DataFrame.from_records([row])])


# ---------------------------------------------------------------------------
# Export / backup
# ---------------------------------------------------------------------------

def _folder(params: dict) -> str:
    folder = './data'
    if params['Subject']:
        folder = f'./data/{params["Subject"]}'
        if not os.path.exists(folder):
            os.mkdir(folder)
    return folder


def export_data(params: dict, **kwargs):
    folder    = _folder(params)
    timestamp = strftime("%Y-%m-%d %H-%M", localtime(params['startTime']))
    for key, value in kwargs.items():
        if isinstance(value, pd.DataFrame):
            try:
                df = value.drop_duplicates(keep='first')
                df.to_csv(f'{folder}/FORT {params["Subject"]} Session {params["session"]} - {key} - {timestamp}.csv')
            except Exception:
                print(f"Could not export {key}.")
            else:
                backup = f'{folder}/FORT {params["Subject"]} Session {params["session"]} - {key} - {timestamp}.backup.csv'
                if os.path.exists(backup):
                    os.remove(backup)


def save_backup(params: dict, **kwargs):
    folder    = _folder(params)
    timestamp = strftime("%Y-%m-%d %H-%M", localtime(params['startTime']))
    for key, value in kwargs.items():
        if isinstance(value, pd.DataFrame):
            df = value.drop_duplicates(keep='first')
            df.to_csv(f'{folder}/FORT {params["Subject"]} Session {params["session"]} - {key} - {timestamp}.backup.csv')


def save_fmri_event_onset(params: dict, event_onset_df: pd.DataFrame, block):
    """TIM-style fMRI onset TSV — identical to TIM/dataHandler.save_fmri_event_onset."""
    if event_onset_df is None:
        return
    folder = _folder(params)
    event_onset_df.to_csv(
        f'{folder}/FORT_event_onset_subject_{params["Subject"]}_block_{block}.tsv', sep='\t')
