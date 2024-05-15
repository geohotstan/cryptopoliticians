from members import Member
from bs4 import BeautifulSoup
from pathlib import Path
import requests

data_base_url = Path(__file__).resolve().parent / 'data'

# ========= House of Representatives ==========

# https://disclosures-clerk.house.gov/

# ---- FD Original and FD Amendment
# example doc_id: 10056961
# BASE_URL = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}/{doc_id}.pdf'
# BASE_FD_URL = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2024/10056961.pdf'

# ---- Periodic Transaction Report
# example doc_id: 20024317
# BASE_URL = https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf

# ---- Extension
# example doc_id: 8220063

# Basically only the doc_ids that start with 1 are relevant

def load_HoR_FD_XML(year: int) -> list[dict]:
    fd_fp = data_base_url / f'house_of_representatives/{year}FD/{year}FD.xml'
    assert fd_fp.exists(), 'need to download from https://disclosures-clerk.house.gov/'

    with open(fd_fp, 'r') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'xml')

    return [{child.name: child.text.strip() if child.text else None for child in member.find_all()} \
           for member in soup.find_all('Member')]

def save_HoR_FD_PDF(year: int, fds: list[dict]):
    fp = data_base_url / f'house_of_representatives/reports/{year}'

    for fd in fds:
        # unpack
        last_name = fd['Last']
        first_name = fd['First']
        doc_id = fd['DocID']
        year = fd['Year']
        filing_date = fd['FilingDate'].replace('/', '-')

        # create folder
        member_fp = fp / f"{last_name}_{first_name}"
        member_fp.mkdir(parents=True, exist_ok=True)

        # download pdf and save it
        file_name = f'{filing_date}_{doc_id}.pdf'
        pdf_fp = member_fp / file_name
        pdf_url = f'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}/{doc_id}.pdf'
        response = requests.get(pdf_url)
        if response.status_code == 200:
            with pdf_fp.open('wb') as pdf_file:
                pdf_file.write(response.content)
            print(f"Saved {file_name} to {fp}")
        else:
            print(f"Failed to download {pdf_url}")


# ========= Senate ==========

# https://efdsearch.senate.gov/search/



if __name__ == "__main__":
    year = 2022

    # ---- House of Representatives

    fds = load_HoR_FD_XML(year=year)
    # filter for DocID that starts with 1. See FD Original
    # NOTE: 'FilingType': 'C' refers to Candidate Report
    # NOTE: 'FilingType': 'O' refers to Annual Report
    # fds = [fd for fd in fds if fd['FilingType'] == 'C' and fd['DocID'][0] == '1']
    fds = [fd for fd in fds if fd['FilingType'] == 'O' and fd['DocID'][0] == '1']
    # fds = [fd for fd in fds if fd['FilingType'] == 'C' and fd['DocID'][0] == '1']

    save_HoR_FD_PDF(year=year, fds=fds)


    # ---- Senate