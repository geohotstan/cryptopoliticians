from utils import HOR_DATA_FP, SENATE_DATA_FP, remove_directory
from members import fetch_members, setup_members
from holdings import scrape_house_of_representatives, scrape_senate

CONGRESS = 118 # most recent congress
year = 2022

try:
    # fetch members for most recent congress
    members = fetch_members(CONGRESS)

    # create data folders and basic json structure
    # -> /data/House of Representatives/
    # -> /data/Senate/
    setup_members(members)

    # House of Representatives
    # -> /data/House of Representatives/{members}
    scrape_house_of_representatives(year)

    # Senate
    # -> /data/Senate/{members}
    scrape_senate(year)
except (KeyboardInterrupt, Exception) as e:
    # remove everything in directory
    remove_directory(HOR_DATA_FP)
    remove_directory(SENATE_DATA_FP)
    raise e