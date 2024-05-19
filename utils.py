import json
from pathlib import Path
import shutil

def remove_directory(path):
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        return True
    raise FileExistsError(f"directory {path} does not exist")

def update_holding_json(path_to_json:Path, holdings:dict):
    assert path_to_json.exists(), f"{path_to_json} does not exist"
    with open(path_to_json, "r") as file:
        data = json.load(file)

    data['holdings'] = data['holdings'] | holdings

    with open(path_to_json, "w") as file:
        json.dump(data, file, indent=4)

BASE_DATA_FP = Path(__file__).resolve().parent / 'data'
HOR_DATA_FP = BASE_DATA_FP / 'House of Representatives'
SENATE_DATA_FP = BASE_DATA_FP / 'Senate'

ASSET_HEADERS = ['Asset', 'Asset Type', 'Owner', 'Value', 'Income Type', 'Income']

STATE = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY'
}

