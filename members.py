import requests
from typing import Any
from dataclasses import dataclass, field

CONGRESS = 118
BASE_URL = f"https://api.congress.gov/v3"
API_KEY = "<enter-your-key>" # https://gpo.congress.gov/sign-up/

@dataclass
class Member:
    name: str
    party: str
    state: str
    chamber: str
    holdings: dict = field(default=dict)

def fetch_members(congress: int, params=None) -> list[dict]:
    url = BASE_URL + f'/member/congress/{congress}'
    if params is None: params = {'api_key': API_KEY, 'limit': 250}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise requests.HTTPError(f"Received status code {response.status_code} when fetching members")

    data = response.json()
    assert 'members' in data, "no members were returned"

    members = [member for member in data['members']]

    # Update the URL to the next page
    if next_url := data['pagination'].get('next'):
        # Parse out the params from the next_url
        next_url_split = next_url.split('?')
        url = next_url_split[0]
        params.update(dict(x.split('=') for x in next_url_split[1].split('&')))
        members += fetch_members(congress, params)

    return members

def parse_members(members: list[dict]) -> list[Member]:
    # filter for if any members resigned during their term
    members = [member for member in members if any('endYear' not in term for term in member['terms']['item'])]

    ret = []
    for member in members:
        member_obj = Member(
            name=member['name'],
            party=member['partyName'][0],
            state=member['state'].title(),
            chamber=member['terms']['item'][0]['chamber'],
        )
        ret.append(member_obj)
    return ret

def fetch():
    return parse_members(fetch_members(CONGRESS))


if __name__ == "__main__":
    # print(fetch_members(CONGRESS))
    for member in fetch():
        print(member)
