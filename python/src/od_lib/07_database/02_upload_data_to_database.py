from sqlalchemy import create_engine
import od_lib.definitions.path_definitions as path_definitions
import pandas as pd
import os
import datetime

send_to_db = False

engine = create_engine("postgresql://postgres:postgres@localhost:5432/next")

# Load Final Data

CONTRIBUTIONS_EXTENDED = os.path.join(
    path_definitions.DATA_FINAL, "contributions_extended.pkl"
)
SPOKEN_CONTENT = os.path.join(path_definitions.DATA_FINAL, "speech_content.pkl")
FACTIONS = os.path.join(path_definitions.DATA_FINAL, "factions.pkl")
PEOPLE = os.path.join(path_definitions.DATA_FINAL, "politicians.csv")
CONTRIBUTIONS_SIMPLIFIED = os.path.join(
    path_definitions.CONTRIBUTIONS_SIMPLIFIED, "contributions_simplified.pkl"
)
CONTRIBUTIONS_SIMPLIFIED_WP19 = os.path.join(
    path_definitions.CONTRIBUTIONS_SIMPLIFIED,
    "electoral_term_19",
    "contributions_simplified.pkl",
)
CONTRIBUTIONS_SIMPLIFIED_WP20 = os.path.join(
    path_definitions.CONTRIBUTIONS_SIMPLIFIED,
    "electoral_term_20",
    "contributions_simplified.pkl",
)
ELECTORAL_TERMS = os.path.join(path_definitions.ELECTORAL_TERMS, "electoral_terms.csv")

# Load data
electoral_terms = pd.read_csv(ELECTORAL_TERMS)

politicians = pd.read_csv(PEOPLE)
politicians = politicians.drop_duplicates(subset=["ui"], keep="first")
politicians = politicians.drop(
    [
        "electoral_term",
        "faction_id",
        "institution_type",
        "institution_name",
        "institution_start_dt",
        "institution_end_dt",
        "constituency",
        "wkr_number",
        "wkr_land",
        "mandate_type"
    ],
    axis=1,
)

politicians.columns = [
    "id",
    "first_name",
    "last_name",
    "birth_place",
    "birth_country",
    "birth_date",
    "death_date",
    "gender",
    "profession",
    "religion",
    "family",
    "aristocracy",
    "academic_title",
]

series = {
    "id": -1,
    "first_name": "Not found",
    "last_name": "",
    "birth_place": None,
    "birth_country": None,
    "birth_date": None,
    "death_date": None,
    "gender": None,
    "profession": None,
    "religion": None,
    "family": None,
    "aristocracy": None,
    "academic_title": None,
}
# New pandas version: _append
politicians = politicians._append(pd.Series(series), ignore_index=True)

def convert_date_politicians(date):
    try:
        date = datetime.datetime.strptime(date, "%d.%m.%Y")
        date = date.strftime("%Y-%m-%d %H:%M:%S")
        return date
    except (ValueError, TypeError):
        return None


def convert_date_speeches(date):
    try:
        date = datetime.datetime.fromtimestamp(date)
        date = date.strftime("%Y-%m-%d %H:%M:%S")
        return date
    except (ValueError, TypeError) as e:
        print(e)
        return None


def check_politicians(row):
    speaker_id = row.politician_id

    politician_ids = politicians.id.tolist()
    if speaker_id not in politician_ids:
        speaker_id = -1
    return speaker_id


print("starting electoral_terms..")

if send_to_db:
    electoral_terms.to_sql(
        "electoral_terms", engine, if_exists="append", schema="open_discourse", index=False
    )

electoral_terms.to_csv(os.path.join(path_definitions.DATABASE, "electoral_terms.csv"), index = False)

print("starting politicians..")

politicians = politicians.where((pd.notnull(politicians)), None)

politicians.birth_date = politicians.birth_date.apply(convert_date_politicians)
politicians.death_date = politicians.death_date.apply(convert_date_politicians)

politicians.to_csv(os.path.join(path_definitions.DATABASE, "politicians.csv"), index = False)

if send_to_db:
    politicians.to_sql(
        "politicians", engine, if_exists="append", schema="open_discourse", index=False
    )


print("starting factions..")
factions = pd.read_pickle(FACTIONS)
factions = factions.sort_values('id')

# Step 1: Drop duplicates based on 'id' and 'abbreviation'
factions = factions.drop_duplicates(subset=['id', 'abbreviation'])

# Step 2: Keep only 'id' and 'abbreviation' columns
factions = factions[['id', 'abbreviation']]

# Step 3: Add a row with id = -1 and abbreviation = 'not found'
not_found_row = pd.DataFrame([{'id': -1, 'abbreviation': 'not found'}])
factions = pd.concat([factions, not_found_row], ignore_index=True)

# Earlier: factions were defined independently here again, mismatch in coding compared to 01_create_factions

factions.id = factions.id.astype(int)

factions.to_csv(os.path.join(path_definitions.DATABASE, "factions.csv"), index = False)

if send_to_db:
    factions.to_sql(
        "factions", engine, if_exists="append", schema="open_discourse", index=False
    )

print("starting speeches..")

speeches = pd.read_pickle(SPOKEN_CONTENT) # shape (950898, 12) #(976728, 12)
speeches.shape

speeches["date"] = speeches["date"].apply(convert_date_speeches)
speeches.shape
speeches = speeches.where((pd.notnull(speeches)), None)
speeches.position_long.replace([r"^\s*$"], [None], regex=True, inplace=True)
speeches.politician_id = speeches.apply(check_politicians, axis=1)
speeches.shape


# Unfortunately, the original code base provided by open discourse does not provide the data for:
#Electoral term 1 has a gap larger than 1 between sessions 18 and 20.
#Electoral term 1 has a gap larger than 1 between sessions 40 and 43.
#Electoral term 1 has a gap larger than 1 between sessions 182 and 184.
#Electoral term 1 has a gap larger than 1 between sessions 222 and 225.
#Electoral term 1 has a gap larger than 1 between sessions 279 and 282.
#Electoral term 2 has a gap larger than 1 between sessions 187 and 189.
# There was a bug in their code, which I discovered and fixed later.
# 1 & 2 electoral terms are not important to our project, but in order to keep id consistent
# I had to remove the sessions which were previously missing:

speeches['remove'] = ((speeches.electoral_term==1) & (speeches.session.isin([19, 41, 42, 183, 223, 224, 280, 281])))| ((speeches.electoral_term==2) & (speeches.session.isin([188])))
sum(speeches['remove'])
speeches.shape[0]
speeches = speeches[~speeches['remove']]

# Redefine id
speeches.loc[speeches.electoral_term<=18, "id"] = list(range(len(speeches[speeches.electoral_term<=18])))


def check_session_gaps(group):
    group = group.sort_values()
    gaps = group.diff()
    gap_pairs = [(group.iloc[i-1], group.iloc[i]) for i in range(1, len(group)) if gaps.iloc[i] > 1]
    return gap_pairs

gap_pairs_exist = speeches.groupby('electoral_term')['session'].apply(check_session_gaps)

# Print electoral terms with gaps in sessions larger than 1 and the pair of sessions
for term, gap_pairs in gap_pairs_exist.items():
    if gap_pairs:
        for pair in gap_pairs:
            print(f'Electoral term {term} has a gap larger than 1 between sessions {pair[0]} and {pair[1]}.')



speeches.to_csv(os.path.join(path_definitions.DATABASE, "speeches.csv"), index = False)

if send_to_db:
    speeches.to_sql(
        "speeches", engine, if_exists="append", schema="open_discourse", index=False
    )


print("starting contributions_extended..")

contributions_extended = pd.read_pickle(CONTRIBUTIONS_EXTENDED)

contributions_extended = contributions_extended.where(
    (pd.notnull(contributions_extended)), None
)

contributions_extended.to_csv(os.path.join(path_definitions.DATABASE, "contributions_extended.csv"), index = False)

if send_to_db:
    contributions_extended.to_sql(
        "contributions_extended",
        engine,
        if_exists="append",
        schema="open_discourse",
        index=False,
    )


print("starting contributions_simplified..")

contributions_simplified = pd.read_pickle(CONTRIBUTIONS_SIMPLIFIED)

contributions_simplified_electoral_term_19 = pd.read_pickle(
    CONTRIBUTIONS_SIMPLIFIED_WP19
)
contributions_simplified_electoral_term_20 = pd.read_pickle(
    CONTRIBUTIONS_SIMPLIFIED_WP20
)

contributions_simplified = pd.concat(
    [
        contributions_simplified,
        contributions_simplified_electoral_term_19,
        contributions_simplified_electoral_term_20,
    ],
    sort=False,
)

contributions_simplified = contributions_simplified.where(
    (pd.notnull(contributions_simplified)), None
)

contributions_simplified["id"] = range(len(contributions_simplified.content))

contributions_simplified.to_csv(os.path.join(path_definitions.DATABASE, "contributions_simplified.csv"), index = False)

if send_to_db:
    contributions_simplified.to_sql(
        "contributions_simplified",
        engine,
        if_exists="append",
        schema="open_discourse",
        index=False,
    )

print("finished")
