from utils import HOR_DATA_FP, SENATE_DATA_FP, remove_directory
from members import fetch_members, setup_members
from holdings import scrape_house_of_representatives, scrape_senate
from extract import disclosure_openai_VLM

CONGRESS = 118 # most recent congress
year = 2022

try:
    # clean up previous attempts
    if HOR_DATA_FP.exists():
        remove_directory(HOR_DATA_FP)
    if SENATE_DATA_FP.exists():
        remove_directory(SENATE_DATA_FP)

    # fetch members for most recent congress
    members = fetch_members(CONGRESS)

    # create data folders and basic json structure
    # -> /data/House of Representatives/
    # -> /data/Senate/
    setup_members(members)

    # House of Representatives
    # -> /data/House of Representatives/{members}
    unsure = scrape_house_of_representatives(year)
    if unsure:
        for name_1, name_2 in unsure:
            print(name_1, " <=> ", name_2)
        ans = input("Are any of these the same person? (yes or no) ")
        if ans == "yes":
            raise RuntimeError("please add both names into interchangable_names.json and rerun run.py")

    # Senate
    # -> /data/Senate/{members}
    unsure = scrape_senate(year)
    if unsure:
        for name_1, name_2 in unsure:
            print(name_1, " <=> ", name_2)
        ans = input("Are any of these the same person? (yes or no) ")
        if ans == "yes":
            raise RuntimeError("please add both names into interchangable_names.json and rerun run.py")

except (KeyboardInterrupt, Exception) as e:
    # remove everything in directory
    if HOR_DATA_FP.exists():
        remove_directory(HOR_DATA_FP)
    if SENATE_DATA_FP.exists():
        remove_directory(SENATE_DATA_FP)
    raise e