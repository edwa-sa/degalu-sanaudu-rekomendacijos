"""Paruošia tik šio projekto vietinę .venv ir paleidžia programą."""
from pathlib import Path
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parent

def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    if sys.version_info[:2]!=(3,12):
        raise RuntimeError('Šiam paketui reikia Python 3.12.')
    interpreter=ROOT/'.venv'/'Scripts'/'python.exe'
    if not interpreter.exists():
        print('Kuriama vietinė projekto aplinka .venv...',flush=True)
        subprocess.run([sys.executable,'-m','venv',str(ROOT/'.venv')],check=True,cwd=ROOT)
    env=os.environ.copy();env['PYTHONUTF8']='1'
    # Tikrinamos visos nurodytos versijos; dalinis diegimas nelaikomas sėkme.
    probe="import importlib.metadata as m; from pathlib import Path; rows=Path('requirements.txt').read_text().splitlines(); assert all(m.version(n)==v for n,v in (r.split('==') for r in rows if r.strip()))"
    ready=subprocess.run([str(interpreter),'-c',probe],cwd=ROOT,env=env,capture_output=True).returncode==0
    if not ready:
        print('Diegiamos projekto bibliotekos. Pirmą kartą reikia interneto; tai gali užtrukti kelias minutes.',flush=True)
        subprocess.run([str(interpreter),'-m','pip','install','-r',str(ROOT/'requirements.txt')],cwd=ROOT,env=env,check=True)
    print('Paleidžiama programa. Šį langą palikite atidarytą.',flush=True)
    subprocess.run([str(interpreter),str(ROOT/'app.py')],cwd=ROOT,env=env,check=True)

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('\nPALEIDIMO KLAIDA:',e,flush=True)
        print('Nukopijuokite klaidos tekstą iš šio lango. Jei klaida minima aukščiau, nukopijuokite ir ją.',flush=True)
        sys.exit(1)
