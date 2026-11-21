"""OBD pobūdžio CSV analizė. Tik skaitymas; ECU ir CAN rašymo nėra."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SIGNALS=['speed_kmh','rpm','load_pct','fuel_lph']
FEATURES=['mean_speed','speed_std','mean_abs_acc','acc_p95','brake_share','fast_acc_share','rpm_mean','high_rpm_share','idle_share','load_mean']
NAMES=['Vidutinis greitis','Greičio sklaida','Vidutinis |pagreitis|','Pagreičio 95 procentilis','Staigaus lėtėjimo dalis','Staigaus greitėjimo dalis','Vidutiniai sūkiai','Aukštų sūkių dalis','Stovėjimo su varikliu dalis','Vidutinė apkrova']

def clean_trip(frame):
    need=['time_s','speed_kmh','rpm','load_pct']
    if not set(need).issubset(frame.columns): raise ValueError('Trūksta laukų: '+', '.join(need))
    f=frame.copy().sort_values('time_s')
    for c in need+(['fuel_lph'] if 'fuel_lph' in f else []): f[c]=pd.to_numeric(f[c],errors='coerce')
    if f.time_s.isna().any() or f.time_s.duplicated().any(): raise ValueError('Netinkamos arba pasikartojančios laiko žymos.')
    if len(f)<60: raise ValueError('Reikia bent 60 sekundžių duomenų.')
    if not np.allclose(np.diff(f.time_s),1): raise ValueError('Prototipui reikia vienos sekundės žingsnio.')
    bounds={'speed_kmh':(0,180),'rpm':(0,7000),'load_pct':(0,100),'fuel_lph':(0,60)}
    for c,(lo,hi) in bounds.items():
        if c not in f: continue
        f.loc[~f[c].between(lo,hi),c]=np.nan
        if f[c].isna().mean()>.05: raise ValueError(f'Per daug trūkstamų reikšmių: {c}')
        # Pildomos tik vidinės spragos, ne ilgesnės kaip 2 s.
        missing=f[c].isna(); runs=missing.groupby((missing!=missing.shift()).cumsum()).transform('sum')
        if (missing & (runs>2)).any(): raise ValueError(f'Ilgesnė nei 2 s spraga: {c}')
        f[c]=f[c].interpolate(limit=2,limit_area='inside')
        if f[c].isna().any(): raise ValueError('Nepildomos spragos įrašo pradžioje ar pabaigoje.')
    f['acc_ms2']=f.speed_kmh.diff().fillna(0)/3.6
    return f

def features(f):
    a=f.acc_ms2
    return dict(mean_speed=f.speed_kmh.mean(),speed_std=f.speed_kmh.std(ddof=0),mean_abs_acc=a.abs().mean(),acc_p95=a.quantile(.95),brake_share=(a<-2.5).mean(),fast_acc_share=(a>2).mean(),rpm_mean=f.rpm.mean(),high_rpm_share=((f.rpm>3000)&(f.load_pct<45)&(f.speed_kmh>10)).mean(),idle_share=((f.speed_kmh<1)&(f.rpm>500)).mean(),load_mean=f.load_pct.mean())

def advice(f,style):
    x=features(f); tips=[]
    # Ribos yra demonstracinės ir turi būti kalibruojamos realiems automobiliams.
    if x['fast_acc_share']>.03: tips.append(('greitejimas','Dažnai staigiai greitėjama. Kai sąlygos leidžia, greitėkite tolygiau.'))
    if x['brake_share']>.02: tips.append(('stabdymas','Pastebėtas dažnas staigus lėtėjimas. Stebėkite eismą iš anksto ir palaikykite saugų atstumą.'))
    if x['high_rpm_share']>.08: tips.append(('sukiai','Dažnai išlaikomi aukšti sūkiai esant nedidelei apkrovai. Įvertinkite pavaros pasirinkimą pagal automobilio instrukciją; nevažiuokite per žemais sūkiais.'))
    if x['idle_share']>.1: tips.append(('stovejimas','Nemaža įrašo dalis praleista stovint su veikiančiu varikliu. Venkite nereikalingo stovėjimo, kai saugu ir leidžia automobilio instrukcija.'))
    if not tips: tips.append(('stebejimas','Ryškių pasirinktų požymių nerasta. Tęskite stebėjimą ir laikykitės techninės priežiūros rekomendacijų.'))
    # ML klasė keičia santrauką, konkretūs patarimai remiasi matomais rodikliais.
    summary='Įraše atpažinta daugiau intensyvaus vairavimo požymių.' if style==1 else 'Įrašas labiau panašus į tolygaus vairavimo pavyzdžius.'
    return summary,tips

def analyse(frame,model):
    f=clean_trip(frame); x=features(f)
    style=int(model.predict(pd.DataFrame([x])[FEATURES])[0])
    summary,tips=advice(f,style)
    distance=float(np.trapezoid(f.speed_kmh.to_numpy(),dx=1)/3600)
    fuel=float(np.trapezoid(f.fuel_lph.to_numpy(),dx=1)/3600) if 'fuel_lph' in f else None
    return {'style':style,'summary':summary,'distance_km':distance,'fuel_l':fuel,'l100':100*fuel/distance if fuel is not None and distance>.1 else None,'features':x,'recommendations':[{'code':k,'text':v} for k,v in tips]}
