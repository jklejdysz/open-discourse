# Python

The python service processes and creates all of the open-discourse data
- Add module directory to sys path: sys.path.insert(0,'path/open-discourse/python/src')
- export PYTHONPATH=${PYTHONPATH}:path/open-discourse/python/src
export PYTHONPATH=${PYTHONPATH}:/Users/justynaklejdysz/Documents/Projekty/open-discourse-custom/open-discourse/python/src

- After activating the virtual environment
null- . .venv/bin/activate
load the requirements file, pip install psycopg2-binary instead psycopg (error), only necessary for sql engine.
python -m pip install -r requirements.txt

## JK changes:

- fixed missing party assignments (09_amendments/missing_faction_id)
- removed speeches where long piece is repeated (09_amendments/duplicate_speeches)
01_preprocessing/06_extract_mps_from_mp_base_data:
- added more personal information on politicians from MPS data
01_preprocessing/*_split_xml* files:
- added extracting information about table of contents and saving it to a file.
- electoral term 1 and 2: Corrected the pattern matching beginning of the spoken content


## Folders

- The `data` folder contains all of the cached data
- The `logs` folder contains the logs which are generated in the `build.sh` script
- The `src` folder contains all of the python scripts. More infornmation on these can be found in the [README in src](./src/README.md)

## Commands

- To setup the python environment, please run `sh setup.sh`
- To build the open-discourse data, please run `sh build.sh`

## Notes

- Staatsminister in Auswaertigem Amt treated as Guest
