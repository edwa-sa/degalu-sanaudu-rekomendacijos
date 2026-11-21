"""Sukuria atskirus SINTETINIUS demonstracijos įrašus, nekeičia modelio."""
from pathlib import Path
import json,sys,zipfile
import numpy as np
import pandas as pd
import joblib
from system import ROOT,analyse

def build():
    folder=ROOT/'demonstraciniai_duomenys';folder.mkdir(exist_ok=True)
    errors=folder/'klaidu_pavyzdziai';errors.mkdir(exist_ok=True)
    t=np.arange(300); phase=t%60
    smooth=45+5*np.sin(t/30)
    acceleration=np.where(phase<=8,20+9*phase,92-(phase-8)*72/51)
    braking=np.where(phase<43,20+60*phase/43,np.where(phase<50,80,np.maximum(20,80-12*(phase-49))))
    idle=np.interp(t,[0,70,90,200,220,299],[40,40,0,0,40,40])
    mixed=acceleration.copy();mixed[:60]=0;mixed[120:240]=braking[120:240]
    scenarios=[
        ('01_tolygus_vaziavimas.csv',smooth,None,{'stebejimas'},'Tolygus važiavimas be ryškių pasirinktų įvykių.'),
        ('02_staigus_greitejimas.csv',acceleration,None,{'greitejimas'},'Kartojami staigaus greitėjimo epizodai; lėtėjama palaipsniui.'),
        ('03_staigus_stabdymas.csv',braking,None,{'stabdymas'},'Greitėjama palaipsniui, periodiškai staigiai lėtėjama.'),
        ('04_auksti_sukiai.csv',smooth,3500,{'sukiai'},'Tolygus greitis, bet aukšti sūkiai esant nedidelei apkrovai.'),
        ('05_ilgas_stovejimas.csv',idle,None,{'stovejimas'},'Ilgesnis stovėjimas su veikiančiu varikliu; perėjimai tolygūs.'),
        ('06_misrus_vaziavimas.csv',mixed,3500,{'greitejimas','stabdymas','sukiai','stovejimas'},'Keli skirtingi įvykiai viename įraše.'),
        ('07_be_degalu_srauto.csv',smooth,None,{'stebejimas'},'Tinkami signalai, bet degalų srautas nepateiktas: sąnaudos nerodomos.'),
        ('08_trumpos_jutikliu_spragos.csv',acceleration,None,{'greitejimas'},'Dvi trumpos vidinės spragos: programa jas užpildo.'),
    ]
    model=joblib.load(ROOT/'results/style_model.joblib'); results=[]; records=[]
    for name,speed,fixed_rpm,expected,description in scenarios:
        a=np.diff(speed,prepend=speed[0])/3.6
        rpm=np.where(speed<1,800,1600+speed*6+np.maximum(a,0)*180)
        if fixed_rpm: rpm=np.where(speed<1,800,fixed_rpm)
        load=np.clip(25+14*np.maximum(a,0),15,90)
        fuel=.65+.04*speed+.7*np.maximum(a,0)+.0002*np.maximum(rpm-2000,0)
        frame=pd.DataFrame({'time_s':t,'speed_kmh':speed,'rpm':rpm,'load_pct':load,'fuel_lph':fuel})
        if name.startswith('07'):frame=frame.drop(columns='fuel_lph')
        if name.startswith('08'):
            frame.loc[40:41,'speed_kmh']=np.nan;frame.loc[140,'rpm']=np.nan
        frame.to_csv(folder/name,index=False,float_format='%.6f')
        # Tikrinamas būtent išsaugotas ir iš naujo nuskaitytas failas.
        result=analyse(pd.read_csv(folder/name),model)
        codes={r['code'] for r in result['recommendations']}
        assert codes==expected,(name,codes,expected)
        if name.startswith('07'):assert result['l100'] is None
        result.update(file=name,description=description,synthetic=True)
        results.append(result)
        records.append({'failas':name,'trukme_s':299,'eiluciu':300,'modelio_klase':result['style'],'patarimu_kodai':'; '.join(sorted(codes)),'sanaudos_l100':result['l100'],'aprasymas':description})
    bad=pd.read_csv(folder/'01_tolygus_vaziavimas.csv');bad.loc[80:90,'speed_kmh']=np.nan
    bad.to_csv(errors/'09_per_ilga_spraga.csv',index=False)
    bad=pd.read_csv(folder/'01_tolygus_vaziavimas.csv');bad.loc[20,'time_s']=bad.loc[19,'time_s']
    bad.to_csv(errors/'10_pasikartojantis_laikas.csv',index=False)
    error_results=[]
    for path in errors.glob('*.csv'):
        try:analyse(pd.read_csv(path),model);raise AssertionError('Turėjo atmesti '+path.name)
        except ValueError as e:error_results.append({'file':str(path.relative_to(folder)),'expected_error':str(e)})
    pd.DataFrame(records).to_csv(folder/'rezultatu_santrauka.csv',index=False,encoding='utf-8-sig')
    (folder/'patikrinti_rezultatai.json').write_text(json.dumps({'synthetic':True,'valid_examples':results,'invalid_examples':error_results},ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['DEMONSTRACINIAI DUOMENYS','',
        'VISI šie failai yra specialiai sukurti sintetiniai pavyzdžiai. Tai ne realūs OBD matavimai.',
        'Jie skirti veikimo ir rekomendacijų taisyklių demonstracijai, ne modelio tikslumui ar sutaupymui vertinti.',
        'Degalų srautas iliustracinis. Skirtingų pavyzdžių l/100 km nėra kontroliuojamo sutaupymo bandymas.',
        'Modelis nepakeistas ir iš naujo nemokytas. Stiliaus klasė ir rekomendacijų taisyklės vertinamos atskirai.',
        '', 'KAIP RODYTI','',
        '1. Paleiskite programą per PALEISTI.cmd.',
        '2. Spauskite Pasirinkti CSV ir rinkitės po vieną šio aplanko failą.',
        '3. Spauskite Analizuoti. Į programą nekelkite rezultatų santraukos CSV ar JSON.',
        '4. Pradėkite nuo 01, tada rodykite 02, 05 ir 06. Pabaigai galima 07 ir vieną klaidos pavyzdį.',
        '', 'KOKIO REZULTATO TIKĖTIS','']
    for row in records:
        lines.extend([row['failas'],row['aprasymas'],f"Modelio klasė: {row['modelio_klase']} (0 – tolygesnis, 1 – intensyvesnis profilis).",'Rekomendacijos: '+row['patarimu_kodai']+'.',''])
    lines.extend(['KLAIDŲ PAVYZDŽIAI','Aplanke klaidu_pavyzdziai yra tyčia netinkami failai. Parodykite, kad programa pateikia klaidą, o ne netikrą analizę.',''])
    for row in error_results:lines.extend([row['file'],row['expected_error'],''])
    lines.extend(['PASTABA APIE KLASĘ','Modelis apmokytas ankstesnio generatoriaus duomenimis. Šie specialūs scenarijai yra kitokie, todėl netikėta klasė gali parodyti modelio ribotumą. Patarimų taisyklės tikrina konkrečius signalų įvykius, todėl bendroji klasė nebūtinai sutaps su kiekvienu atskiru patarimu.','Visi šiame apraše nurodyti rezultatai patikrinti su pateiktu išsaugotu modeliu.'])
    (folder/'PRISTATYMO_INSTRUKCIJA.txt').write_text('\n'.join(lines),encoding='utf-8-sig')
    archive=ROOT.parent/'Demonstraciniai_OBD_duomenys.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in folder.rglob('*'):
            if path.is_file():z.write(path,Path(folder.name)/path.relative_to(folder))
    print(pd.DataFrame(records)[['failas','modelio_klase','patarimu_kodai']].to_string(index=False))
    print('Patikrinti 8 tinkami ir 2 tyčia klaidingi failai. Archyvas:',archive)
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');build()
