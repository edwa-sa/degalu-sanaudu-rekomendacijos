# Degalų sąnaudų optimizavimo rekomendacijų sistema

Programinis semestro projekto prototipas. Analizuoja vieno važiavimo CSV,
atpažįsta tolygesnį arba intensyvesnį profilį ir pateikia paaiškinamus patarimus.
ECU valdymo ir tiesioginio OBD adapterio kode nėra.

Atnaujintoje sąsajoje rodomi didesni rodikliai, greičio ir sūkių grafikas,
demonstracinių įrašų pasirinkimas ir JSON rezultato išsaugojimas.
Grafikas vaizduoja išsaugotą įrašą, ne tiesioginę automobilio telemetriją.
Sąsajos modulis: hud.py. Visas GitHub įkėlimo aprašymas: GITHUB_INSTRUKCIJA.txt.

## Svarbu apie duomenis

VISI pateikti važiavimo duomenys yra sintetiniai. 60 profilių, po 10 įrašų
po 180 s. Tai nėra realūs dalyviai ar automobilio matavimai. Klasės yra generatoriaus
profilių žymos; tikslumas nepatvirtintas realiame eisme. Degalų srauto formulė
iliustracinė, ne realaus variklio kalibracija. Sutaupymas neišmatuotas.

## Paleidimas

Windows: išskleiskite visą archyvą, atidarykite projekto aplanką ir dukart
spustelėkite **PALEISTI.cmd**. Ne app.py. Paleidiklis ieško Python 3.12,
sukuria tik šio aplanko .venv, įdiegia bibliotekas ir paleidžia programą.
Pirmą kartą reikia interneto. Klaidos langas lieka atidarytas.
Jei Python 3.12 nerastas, jį reikia įdiegti atskirai iš python.org su pip ir tkinter.

Rekomenduojama Python 3.12. Grafinis režimas reikalauja tkinter.

```text
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
python verify.py
python app.py
```

Linux / macOS aktyvavimas: `source .venv/bin/activate`.
Jei grafinė sąsaja neprieinama:

```text
python app.py --cli data/demo_trip.csv
```

Modelis ir rezultatai pateikti jau sugeneruoti. Norint tik demonstracijos,
po bibliotekų įdiegimo užtenka paleisti app.py. Mokymas naudoja sėklą 42.
Pirmam diegimui reikės interneto; vėliau analizė veikia vietoje.

## Importo schema

CSV antraštė: `time_s,speed_kmh,rpm,load_pct,fuel_lph`.
`fuel_lph` neprivalomas. Be jo sąnaudos neskaičiuojamos.
Viename faile turi būti vienas įrašas, bent 60 eilučių, 1 s laiko žingsnis.
Vienetai: s, km/h, aps./min., %, l/h. Papildomi ID laukai modeliui neteikiami.
Duomenis iš realaus registratoriaus reikia atskirai eksportuoti, suderinti
vienetus ir laiko žymas. PID palaikymas priklauso nuo automobilio.

Vidinės iki 2 s spragos interpoliuojamos. Ilgesnės, kraštinės spragos,
pasikartojantis laikas ar >5 % trūkstamų reikšmių atmetami.

## Metodika

Mokymas: 480 įrašų iš 48 sintetinių vairuotojų.
Testas: 120 įrašų iš kitų 12 vairuotojų. ID nenaudojami kaip požymiai.
CV: penki StratifiedGroupKFold skaidymai, grupuojama pagal vairuotoją.
Palyginami DummyClassifier, LogisticRegression ir RandomForestClassifier.
Modelis pasirenkamas tik pagal mokymo CV macro F1, ne pagal testą.
Pasirinkta logistinė regresija. Išsaugotas modelis mokytas tik su mokymo dalimi.

Konkrečius patarimus sudaro atskiros taisyklės. AI klasė keičia santrauką;
ji nėra gedimo diagnozė ar žmogaus pavojingumo įvertinimas.
Ribos demonstracinės, tikriems automobiliams nevaliduotos.

## Failai

- main.py – generatorius, mokymas, metrikos ir grafikai.
- system.py – kokybės patikra, požymiai ir rekomendacijos.
- app.py – grafinė arba tekstinė demonstracija.
- verify.py – funkcinės patikros.
- data/synthetic_obd.csv – sintetiniai signalai (108 000 eilučių).
- data/labels.csv – sintetinių profilių žymos.
- data/features.csv – 600 agreguotų įrašų.
- results/ – metrikos, skaidymas, prognozės, rekomendacijos ir modelis.

## Prieš akademinį pateikimą

Užpildyti tikrus titulinio lapo duomenis ir atsakomybių lentelę.
Įkelti kodą į savo GitHub saugyklą ir į ataskaitą įrašyti tikrą nuorodą.
Vieša saugykla nebuvo sukurta. Aptarti su dėstytoju, ar sintetinio
prototipo apimtis priimtina ir ar reikia fizinio OBD registratoriaus.
Autoriai turi suprasti ir patys patikrinti kodą bei laikytis kurso AI naudojimo tvarkos.

## Šaltiniai

- https://www.fueleconomy.gov/feg/driveHabits.jsp
- https://www.csselectronics.com/pages/obd2-pid-table-on-board-diagnostics-j1979
- https://scikit-learn.org/stable/modules/cross_validation.html
- https://scikit-learn.org/stable/modules/ensemble.html
- https://scikit-learn.org/stable/modules/model_evaluation.html

Rekomendacijų kryptis paremta bendrais ekonomiško vairavimo patarimais,
o skaitinės ribos ir generatoriaus parametrai yra šio demonstracinio projekto prielaidos.
