# Python

The python service processes and creates all of the open-discourse data
- Add module directory to sys path: sys.path.insert(0,'path/open-discourse/python/src')
- export PYTHONPATH=${PYTHONPATH}:path/open-discourse/python/src
export PYTHONPATH=${PYTHONPATH}:/Users/justynaklejdysz/Documents/Projekty/open-discourse-custom/open-discourse/python/src

- After activating the virtual environment
null- . .venv/bin/activate
load the requirements file, pip install psycopg2-binary instead psycopg (error), only necessary for sql engine.
python -m pip install -r requirements.txt

## Folders

- The `data` folder contains all of the cached data
- The `logs` folder contains the logs which are generated in the `build.sh` script
- The `src` folder contains all of the python scripts. More infornmation on these can be found in the [README in src](./src/README.md)

## Commands

- To setup the python environment, please run `sh setup.sh`
- To build the open-discourse data, please run `sh build.sh`

## Notes

- Staatsminister in Auswaertigem Amt treated as Guest
