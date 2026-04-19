"""
Data handling for FORT assignment.
- fullDF / miniDF: NPU-style continuous and event-level data for the P-condition block.
- mood_df: TIM-style pre/post session mood ratings.
"""
import os
import datetime
import pandas as pd
from time import strftime, localtime

# NPU-style headers for the P-condition block data
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

# TIM-style headers for pre/post mood ratings
HEADERS_MOOD = [
    'Round',
    'Label',
    'Score',
]


def setup_data_frames(params: dict):
    params['headers'] = HEADERS
    df = pd.DataFrame(columns=HEADERS)
    mini_df = pd.DataFrame(columns=HEADERS)
    mood_df = pd.DataFrame(columns=HEADERS_MOOD)
    return params, df, mini_df, mood_df


def create_dict_for_df(params: dict, **kwargs):
    dict_layout = {header: None for header in params['headers']}
    dict_layout['ExperimentName'] = 'FORT'
    dict_layout['Subject'] = params['Subject']
    dict_layout['StartTime'] = params['startTime']
    dict_layout['Session'] = params['session']
    dict_layout['ShockType'] = params['shockType']
    for key, value in kwargs.items():
        if key in dict_layout:
            dict_layout[key] = value
    return dict_layout


def insert_data_mood(round_label: str, scores: dict, mood_df: pd.DataFrame):
    for label, score in scores.items():
        row = {h: None for h in HEADERS_MOOD}
        row['Round'] = round_label
        row['Label'] = label
        row['Score'] = score
        mood_df = pd.concat([mood_df, pd.DataFrame.from_records([row])])
    return mood_df


def _get_folder(params: dict) -> str:
    folder = './data'
    if params['Subject']:
        folder = f'./data/{params["Subject"]}'
        if not os.path.exists(folder):
            os.mkdir(folder)
    return folder


def export_data(params: dict, **kwargs):
    folder = _get_folder(params)
    timestamp = strftime("%Y-%m-%d %H-%M", localtime(params['startTime']))
    for key, value in kwargs.items():
        if isinstance(value, pd.DataFrame):
            try:
                df = value.drop_duplicates(keep='first')
                df.to_csv(f'{folder}/FORT {params["Subject"]} Session {params["session"]} - {key} - {timestamp}.csv')
            except Exception:
                print(f"Could not export {key}, keeping backup.")
            else:
                backup = f'{folder}/FORT {params["Subject"]} Session {params["session"]} - {key} - {timestamp}.backup.csv'
                if os.path.exists(backup):
                    os.remove(backup)


def save_backup(params: dict, **kwargs):
    folder = _get_folder(params)
    timestamp = strftime("%Y-%m-%d %H-%M", localtime(params['startTime']))
    for key, value in kwargs.items():
        if isinstance(value, pd.DataFrame):
            df = value.drop_duplicates(keep='first')
            df.to_csv(f'{folder}/FORT {params["Subject"]} Session {params["session"]} - {key} - {timestamp}.backup.csv')
