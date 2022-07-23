import sys
import subprocess


if len(sys.argv) > 0:
    subprocess.run('cd src/util && python data.py', shell=True)

subprocess.run('cd src && streamlit run app.py', shell=True)
