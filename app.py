"""Grafinė demonstracija: python app.py; tekstinė: python app.py --cli failas.csv"""
import sys,json
import pandas as pd
import joblib
from system import ROOT,analyse

def analyse_file(path):
    frame=pd.read_csv(path)
    if 'trip_id' in frame and frame.trip_id.nunique()!=1: raise ValueError('Pasirinkite vienos kelionės CSV failą.')
    return analyse(frame,joblib.load(ROOT/'results/style_model.joblib'))

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--cli':
        sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(analyse_file(sys.argv[2] if len(sys.argv)>2 else ROOT/'data/demo_trip.csv'),ensure_ascii=False,indent=2)); return
    from hud import launch
    launch()
if __name__=='__main__': main()
