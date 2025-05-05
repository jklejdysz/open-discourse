from bs4 import BeautifulSoup
import od_lib.definitions.path_definitions as path_definitions
import requests
import os
import regex
import time

# output directory
ELECTORAL_TERM_19_20_OUTPUT = path_definitions.ELECTORAL_TERM_19_20_STAGE_01

if not os.path.exists(ELECTORAL_TERM_19_20_OUTPUT):
    os.makedirs(ELECTORAL_TERM_19_20_OUTPUT)

election_periods = [
    {
        "election_period": 19,
        "url": "https://www.bundestag.de/ajax/filterlist/de/services/opendata/543410-543410?offset={}",  # noqa
    },
    {
        "election_period": 20,
        "url": "https://www.bundestag.de/ajax/filterlist/de/services/opendata/866354-866354?offset={}",  # noqa
    },
]


#election_periods = [election_periods[1]]
#election_period = election_periods

for election_period in election_periods:
    OUTPUT_PATH = os.path.join(
        ELECTORAL_TERM_19_20_OUTPUT,
        "electoral_term_{}".format(election_period["election_period"]),
    )

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    reached_end = False
    offset = 0

    while not reached_end:
        URL = election_period["url"].format(str(offset))
        page = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})

        soup = BeautifulSoup(page.text, "html.parser")
        reached_end = True

        # scrape for links
        for link in soup.find_all("a", attrs={"href": regex.compile("xml$")}):
            print(link)
            reached_end = False
            url = link.get("href") #"https://www.bundestag.de" + link.get("href")
            page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            pattern = r"\d{5}(?=-data\.xml)|\d{5}(?=\.xml)"
            session = regex.search(pattern, url).group(0)

            print(session)

            if not os.path.exists(os.path.join(OUTPUT_PATH, session + ".xml")):
                with open(os.path.join(OUTPUT_PATH, session + ".xml"), "w") as file:
                    file.write(
                        regex.sub(
                            "</sub>",
                            "",
                            regex.sub("<sub>", "", page.content.decode("utf-8")),
                        )
                    )

            time.sleep(0.1)
        offset += 10
