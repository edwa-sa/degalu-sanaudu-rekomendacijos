"""Generuoja SINTETINIUS duomenis ir atlieka atkuriamus eksperimentus."""
import json,sys,platform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib, sklearn
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import GroupShuffleSplit,StratifiedGroupKFold,cross_val_score,learning_curve
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,ConfusionMatrixDisplay
from sklearn.inspection import permutation_importance
from system import ROOT,FEATURES,NAMES,clean_trip,features,analyse

def generate():
    rng=np.random.default_rng(42); frames=[]; labels=[]
    # 60 nepriklausomų sintetinių vairuotojų, po 10 įrašų po 180 s.
    for driver in range(60):
        style=driver%2
        tendency=float(rng.uniform(.55,.95) if style else rng.uniform(.05,.45))
        for route in range(10):
            tid=driver*10+route; local=np.random.default_rng(42000+tid)
            intensity=float(np.clip(tendency+local.normal(0,.16),0,1))
            v=0.; rows=[]; target=0.; idle=0
            for t in range(180):
                if t%18==0: target=float(local.choice([0,25,40,50,65,80],p=[.16,.12,.20,.22,.20,.10]))
                if t%45==0: idle=int(local.integers(3,11))
                aim=0 if idle>0 else target
                if idle>0: idle-=1
                cap=.9+2.4*intensity
                acc=float(np.clip((aim-v)/3.6*.65+local.normal(0,.12+.5*intensity),-1.4-2*intensity,cap))
                v=float(np.clip(v+3.6*acc,0,105))
                load=float(np.clip(18+.28*v+15*max(acc,0)+local.normal(0,3),5,100))
                rpm=float(np.clip(780+v*(15+15*intensity)+400*max(acc,0)+local.normal(0,70),700,6500))
                if v<1: rpm=float(800+local.normal(0,25))
                # Tik iliustracinė srauto formulė, nekalibruota konkrečiam varikliui.
                fuel=float(max(.3,.65+.035*v+.65*max(acc,0)+.00015*max(rpm-2000,0)))
                rows.append([driver,tid,t,v,rpm,load,fuel])
            f=pd.DataFrame(rows,columns=['driver_id','trip_id','time_s','speed_kmh','rpm','load_pct','fuel_lph'])
            # Dvi vienos sekundės spragos kiekviename įraše (tik viduje).
            for col in ['speed_kmh','rpm']:
                idx=int(local.integers(5,175)); f.loc[idx,col]=np.nan
            frames.append(f); labels.append({'driver_id':driver,'trip_id':tid,'style':style})
    return pd.concat(frames,ignore_index=True),pd.DataFrame(labels)

def run():
    data=ROOT/'data'; out=ROOT/'results'; data.mkdir(exist_ok=True); out.mkdir(exist_ok=True)
    raw,labels=generate(); raw.to_csv(data/'synthetic_obd.csv',index=False); labels.to_csv(data/'labels.csv',index=False)
    rows=[]
    for tid,f in raw.groupby('trip_id'):
        clean=clean_trip(f); row=features(clean); row['trip_id']=tid; rows.append(row)
    ds=pd.DataFrame(rows).merge(labels,on='trip_id'); ds.to_csv(data/'features.csv',index=False)
    X=ds[FEATURES]; y=ds['style']; groups=ds.driver_id
    tr,te=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=42).split(X,y,groups))
    cv=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42)
    models={'Daugumos klasė':DummyClassifier(strategy='most_frequent'),'Logistinė regresija':make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=1000,random_state=42)),'Atsitiktinis miškas':RandomForestClassifier(n_estimators=200,max_depth=6,min_samples_leaf=4,class_weight='balanced',random_state=42,n_jobs=-1)}
    rows=[]; predictions={}
    for name,model in models.items():
        scores=cross_val_score(model,X.iloc[tr],y.iloc[tr],groups=groups.iloc[tr],cv=cv,scoring='f1_macro')
        model.fit(X.iloc[tr],y.iloc[tr]); pred=model.predict(X.iloc[te]); predictions[name]=pred
        rows.append({'model':name,'accuracy':accuracy_score(y.iloc[te],pred),'precision':precision_score(y.iloc[te],pred,zero_division=0),'recall':recall_score(y.iloc[te],pred,zero_division=0),'f1':f1_score(y.iloc[te],pred,zero_division=0),'macro_f1':f1_score(y.iloc[te],pred,average='macro',zero_division=0),'cv_macro_f1':scores.mean(),'cv_sd':scores.std()})
    metrics=pd.DataFrame(rows); metrics.to_csv(out/'metrics.csv',index=False)
    # Pasirenkama tik pagal CV, be testo rezultatų naudojimo parinkimui.
    chosen=metrics.iloc[1:].sort_values('cv_macro_f1',ascending=False,kind='stable').iloc[0].model
    model=models[chosen]; joblib.dump(model,out/'style_model.joblib')
    ds['split']='train'; ds.loc[te,'split']='test'; ds[['trip_id','driver_id','style','split']].to_csv(out/'split.csv',index=False)
    prediction=ds.iloc[te][['trip_id','driver_id','style']].copy(); prediction['predicted']=predictions[chosen]; prediction.to_csv(out/'test_predictions.csv',index=False)
    reports=[]
    for tid in prediction.trip_id:
        a=analyse(raw[raw.trip_id==tid],model); a['trip_id']=int(tid); reports.append(a)
    (out/'recommendations.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'raw_rows':len(raw),'trips':len(ds),'drivers':groups.nunique(),'train_trips':len(tr),'test_trips':len(te),'train_drivers':groups.iloc[tr].nunique(),'test_drivers':groups.iloc[te].nunique(),'missing_cells':int(raw.isna().sum().sum()),'classes':y.value_counts().sort_index().to_dict(),'test_classes':y.iloc[te].value_counts().sort_index().to_dict(),'chosen':chosen,'python':platform.python_version(),'sklearn':sklearn.__version__,'seed':42}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    plt.rcParams.update({'font.size':10,'figure.dpi':150})
    fig,ax=plt.subplots(1,2,figsize=(9,3.1))
    for cl,color in [(0,'#53758d'),(1,'#bc7958')]:
        subset=ds[ds['style']==cl]; ax[0].hist(subset.mean_abs_acc,bins=18,alpha=.6,color=color,label=['Tolygus','Intensyvus'][cl])
    ax[0].set(xlabel='Vidutinis |pagreitis|, m/s²',ylabel='Įrašų skaičius'); ax[0].legend(fontsize=8)
    for cl in [0,1]:
        f=clean_trip(raw[raw.trip_id==cl*10]); ax[1].plot(f.time_s,f.speed_kmh,label=['Tolygus','Intensyvus'][cl],linewidth=1)
    ax[1].set(xlabel='Laikas, s',ylabel='Greitis, km/h'); ax[1].legend(fontsize=8); fig.tight_layout(); fig.savefig(out/'data.png'); plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(9,3.2))
    for a,name in zip(ax,list(models)[1:]): ConfusionMatrixDisplay.from_predictions(y.iloc[te],predictions[name],labels=[0,1],display_labels=['Tolygus','Intensyvus'],ax=a,colorbar=False,cmap='Blues'); a.set_title(name); a.set_xlabel('Prognozuota klasė'); a.set_ylabel('Tikra sintetinė klasė')
    fig.tight_layout(); fig.savefig(out/'confusion.png'); plt.close(fig)
    imp=permutation_importance(model,X.iloc[te],y.iloc[te],scoring='f1_macro',n_repeats=15,random_state=42)
    order=np.argsort(imp.importances_mean); pd.DataFrame({'feature':FEATURES,'importance':imp.importances_mean,'sd':imp.importances_std}).to_csv(out/'importance.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,3.5)); ax.barh(np.array(NAMES)[order],imp.importances_mean[order],xerr=imp.importances_std[order],color='#53758d'); ax.set_xlabel('Macro F1 sumažėjimas sumaišius požymį'); fig.tight_layout(); fig.savefig(out/'importance.png'); plt.close(fig)
    splits=list(cv.split(X.iloc[tr],y.iloc[tr],groups.iloc[tr]))
    sizes,train_scores,val_scores=learning_curve(model,X.iloc[tr],y.iloc[tr],cv=splits,train_sizes=[.3,.5,.7,1],scoring='f1_macro',shuffle=True,random_state=42)
    fig,ax=plt.subplots(figsize=(8.5,3)); ax.plot(sizes,train_scores.mean(axis=1),'o-',label='Mokymas'); ax.plot(sizes,val_scores.mean(axis=1),'o-',label='Validavimas'); ax.set(xlabel='Mokymo įrašų skaičius',ylabel='Macro F1',ylim=(0,1.03)); ax.legend(); fig.tight_layout(); fig.savefig(out/'learning.png'); plt.close(fig)
    raw[raw.trip_id==int(prediction.trip_id.iloc[0])].to_csv(data/'demo_trip.csv',index=False)
    print(metrics.to_string(index=False)); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8'); run()
