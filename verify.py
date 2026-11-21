"""Patikrina duomenų atskyrimą, įvestis ir rekomendacijų logiką."""
import json,sys
import numpy as np
import pandas as pd
from system import ROOT,clean_trip,advice
from app import analyse_file

def run():
    checks={}; sp=pd.read_csv(ROOT/'results/split.csv')
    checks['Skirtingi vairuotojai mokymui ir testui']=not bool(set(sp[sp.split=='train'].driver_id)&set(sp[sp.split=='test'].driver_id))
    checks['Visos 600 kelionių panaudotos vieną kartą']=len(sp)==600 and sp.trip_id.nunique()==600
    a=analyse_file(ROOT/'data/demo_trip.csv'); checks['Išsaugotas modelis ir CSV analizė veikia']=a['style'] in [0,1] and len(a['recommendations'])>0 and np.isfinite(a['l100'])
    frame=pd.read_csv(ROOT/'data/demo_trip.csv'); f=clean_trip(frame)
    checks['Trumpi jutiklių tarpai užpildyti']=not f[['speed_kmh','rpm']].isna().any().any()
    from system import analyse
    import joblib
    checks['Be degalų srauto sąnaudos neišgalvojamos']=analyse(frame.drop(columns=['fuel_lph']),joblib.load(ROOT/'results/style_model.joblib'))['l100'] is None
    invalid=frame.copy(); invalid.loc[10:20,'speed_kmh']=np.nan
    try: clean_trip(invalid); checks['Ilga duomenų spraga atmetama']=False
    except ValueError: checks['Ilga duomenų spraga atmetama']=True
    invalid=frame.copy(); invalid.loc[2,'time_s']=invalid.loc[1,'time_s']
    try: clean_trip(invalid); checks['Pasikartojantis laikas atmetamas']=False
    except ValueError: checks['Pasikartojantis laikas atmetamas']=True
    invalid=frame.drop(columns=['rpm'])
    try: clean_trip(invalid); checks['Trūkstamas privalomas laukas atmetamas']=False
    except ValueError: checks['Trūkstamas privalomas laukas atmetamas']=True
    # Kontroliuojami įvykiai tikrina visas taisykles, nesiremdami modelio atsakymu.
    probe=f.copy(); probe['acc_ms2']=np.tile([3,-3,0],60); probe['rpm']=3500; probe['load_pct']=30; probe['speed_kmh']=40; probe.loc[probe.index[:30],'speed_kmh']=0
    codes={c for c,t in advice(probe,1)[1]}; checks['Suveikia keturios įvykių rekomendacijos']=codes=={'greitejimas','stabdymas','sukiai','stovejimas'}
    probe['acc_ms2']=0; probe['rpm']=1600; probe['speed_kmh']=40
    checks['Kai įvykių nėra pateikiamas stebėjimo patarimas']=advice(probe,0)[1][0][0]=='stebejimas'
    checks={k:bool(v) for k,v in checks.items()}; (ROOT/'results/verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(checks.values()),checks
    print(json.dumps(checks,ensure_ascii=False,indent=2))
if __name__=='__main__': sys.stdout.reconfigure(encoding='utf-8'); run()
