from typing import Union
from dataclasses import dataclass
from bs4 import BeautifulSoup
from pathlib import Path
from pdf2image import convert_from_bytes
import json
import requests

BASE_DATA_FP = Path(__file__).resolve().parent / 'data'

# =============================================
# ========= House of Representatives ==========
# =============================================
# https://disclosures-clerk.house.gov/

HOR_DATA_FP = BASE_DATA_FP / 'house_of_representatives'

def load_HoR_FD_XML(year: int) -> list[dict]:
    xml_fp = HOR_DATA_FP / f'{year}FD/{year}FD.xml'
    assert xml_fp.exists(), f'need to download from https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip extracted and copied to data/'

    with open(xml_fp, 'r') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'xml')

    fds = [{child.name: child.text.strip() if child.text else None for child in member.find_all()} \
           for member in soup.find_all('Member')]

    # NOTE: 'FilingType': 'O' refers to Annual Report
    fds = [fd for fd in fds if fd['FilingType'] == 'O']

    return fds


def save_HoR_FD_PDF(year: int, fds: list[dict]):
    fp = HOR_DATA_FP / f'reports/{year}'
    fp.mkdir(parents=True, exist_ok=True)

    for fd in fds:
        # unpack
        last_name = fd['Last']
        first_name = fd['First']
        doc_id = fd['DocID']
        year = fd['Year']
        filing_date = fd['FilingDate'].replace('/', '-')

        # create folder for member and create a folder to store images
        member_fp = fp / f"{last_name}_{first_name}"
        member_fp.mkdir(parents=True, exist_ok=True)
        images_fp = member_fp / "imgs"
        images_fp.mkdir(parents=True, exist_ok=True)

        # download pdf and save it in folder
        pdf_url = f'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}/{doc_id}.pdf'

        response = requests.get(pdf_url)
        if response.status_code != 200:
            raise requests.HTTPError(f"Failed to download {pdf_url}")

        images = convert_from_bytes(response.content)
        for i, image in enumerate(images):
            image_fp = images_fp / f"{filing_date}_{i}.jpg"
            image.save(image_fp, 'JPEG')
        print(f"Finished saving {i} images from {last_name}, {first_name} to {images_fp}")


def scrape_house_of_representatives(year: int):
    fds = load_HoR_FD_XML(year=year)

    # save to data/house_of_representatives/{year}
    save_HoR_FD_PDF(year=year, fds=fds)


# ===========================
# ========= Senate ==========
# ===========================
# https://efdsearch.senate.gov/search/

ROOT = 'https://efdsearch.senate.gov'
LANDING_PAGE_URL = f'{ROOT}/search/home/'
SEARCH_PAGE_URL = f'{ROOT}/search/'
REPORTS_URL = f'{ROOT}/search/report/data/'
PDF_PREFIX = '/search/view/paper/'
SENATE_DATA_FP = BASE_DATA_FP / 'senate'

BATCH_SIZE = 100

@dataclass
class SenateMember:
    first_name: str
    last_name: str
    html: str
    date: str
    is_scanned: bool


def _csrf(client: requests.Session) -> str:
    """ Set the session ID and return the CSRF token for this session. """
    landing_page_response = client.get(LANDING_PAGE_URL)
    assert landing_page_response.url == LANDING_PAGE_URL, 'Failed to fetch filings landing page'

    landing_page = BeautifulSoup(landing_page_response.text, 'lxml')
    form_csrf = landing_page.find(
        attrs={'name': 'csrfmiddlewaretoken'}
    )['value']
    form_payload = {
        'csrfmiddlewaretoken': form_csrf,
        'prohibition_agreement': '1'
    }
    client.post(LANDING_PAGE_URL,
                data=form_payload,
                headers={'Referer': LANDING_PAGE_URL})

    if 'csrftoken' in client.cookies:
        csrftoken = client.cookies['csrftoken']
    else:
        csrftoken = client.cookies['csrf']
    return csrftoken


def reports_api(client: requests.Session, offset: int, token: str, year: int) -> list[list[str]]:
    """ Query the periodic transaction reports API. """
    login_data = {
        'start': str(offset),
        'length': str(BATCH_SIZE),
        'report_types': '[7]', # Annual reports
        'filer_types': '[]', # 1 for Senator (not candidate)
        'submitted_start_date': f'01/01/{year} 00:00:00',
        'submitted_end_date': f'01/01/{year+1} 00:00:00',
        'candidate_state': '',
        'senator_state': '',
        'office_id': '',
        'first_name': '',
        'last_name': '',
        'csrfmiddlewaretoken': token
    }
    response = client.post(REPORTS_URL,
                           data=login_data,
                           headers={'Referer': SEARCH_PAGE_URL})
    return response.json()['data']


def disclosure_api(client: requests.Session, member: SenateMember, href_link: str):
    full_url = ROOT + href_link
    response = client.get(full_url)

    webpage_soup = BeautifulSoup(response.text, 'html.parser')

    # if the disclosure is scanned, we just fetch the images
    if member.is_scanned:
        # TODO: get assets
        gif_urls = [img['src'] for img in webpage_soup.find_all('img', class_='filingImage')]
        responses = [client.get(url) for url in gif_urls]
        if any(response.status_code != 200 for response in responses):
            raise requests.HTTPError(f"{member=} raise HTTP error")
        return [response.content for response in responses]

    # otherwise, we'll parse the webpage for assets
    assets_section = webpage_soup.find('h3', string='Part 3. Assets').find_parent('section')
    table = assets_section.find('table', {'id': 'grid_items'})

    ret = []
    for row in table.tbody.find_all('tr'):
        cells = row.find_all('td')
        asset_data = {
        'Asset': cells[1].find('strong').text.strip(), # strong -> only get bolded Asset title (no asset description)
        'Asset Type': cells[2].get_text(separator=" ").strip(),
        'Owner': cells[3].text.strip(),
        'Value': cells[4].text.strip(),
        'Income Type': cells[5].text.strip(),
        'Income': cells[6].text.strip(),
        }
        ret.append(asset_data)

    return ret


def scrape_and_save_disclosure(client: requests.Session, year:int, reports:list[SenateMember]):
    fp = SENATE_DATA_FP / f'reports/{year}'
    fp.mkdir(parents=True, exist_ok=True)

    for disclosure in reports:
        disclosure_fp = fp / f"{disclosure.last_name}_{disclosure.first_name}"
        disclosure_fp.mkdir(parents=True, exist_ok=True)

        # Find the <a> tag and extract the href attribute
        link_soup = BeautifulSoup(disclosure.html, 'html.parser')
        a_tag = link_soup.find('a')
        href_link = a_tag['href']
        disclosure_name = a_tag.text

        member_diclosure: list[Union[bytes, dict]] = disclosure_api(client, disclosure, href_link)

        if disclosure.is_scanned:
            assert all(isinstance(f, bytes) for f in member_diclosure), \
            f"datatype is wrong for {disclosure.last_name} {disclosure.first_name} {disclosure.html}"

            # create a folder to store images
            images_fp = disclosure_fp / "imgs"
            images_fp.mkdir(parents=True, exist_ok=True)

            for i, f in enumerate(member_diclosure):
                file_fp = images_fp / f"{disclosure_name}_{disclosure.date}_{i}.gif"
                with open(file_fp, "wb") as file:
                    file.write(f)

            print(f"Finished saving {i} images from {disclosure.last_name}, {disclosure.first_name} to {images_fp}")
        else:
            assert all(isinstance(f, dict) for f in member_diclosure), \
            f"datatype is wrong for {disclosure.last_name} {disclosure.first_name} {disclosure.html}"

            file_fp = disclosure_fp / f"{disclosure_name}_{disclosure.date}.json"
            with open(file_fp, "w") as file:
                json.dump({f"{disclosure.last_name}_{disclosure.first_name}": member_diclosure}, file)

            print(f"Finished saving json from {disclosure.last_name}, {disclosure.first_name} to {file_fp}")



def scrape_senate(year: int):
    def _filter(reports: list[list[str]]) -> list[SenateMember]:
        return [SenateMember(
            first_name=report[0].title(),
            last_name=report[1].title(),
            html=report[3],
            date=report[4].replace("/", "-"),
            is_scanned= "for CY" not in report[3]
        ) for report in reports if "Senator" in report[2]]

    client = requests.Session()

    token = _csrf(client)
    idx = 0
    reports = reports_api(client, idx, token, year)
    all_reports: list[list[str]] = []
    while len(reports) != 0:
        all_reports.extend(reports)
        idx += BATCH_SIZE
        reports = reports_api(client, idx, token, year)

    all_reports = _filter(all_reports)

    scrape_and_save_disclosure(client, year, all_reports)




if __name__ == "__main__":
    # grab for year
    year = 2022

    # House of Representatives
    scrape_house_of_representatives(year)

    # Senate
    scrape_senate(year)
