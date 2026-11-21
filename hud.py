"""Vietinė važiavimo įrašo peržiūra. Jokių realaus laiko automobilio rodmenų."""
import json
from pathlib import Path
import pandas as pd
from system import ROOT,clean_trip

def plot_trip(frame,figure):
    f=clean_trip(frame);figure.clear()
    ax=figure.add_subplot(111);ax.set_facecolor('#142638');figure.set_facecolor('#142638')
    ax.plot(f.time_s-f.time_s.iloc[0],f.speed_kmh,color='#43DBC4',linewidth=1.7,label='Greitis')
    ax.set_xlabel('Įrašo laikas, s',color='#C9D6E2');ax.set_ylabel('Greitis, km/h',color='#43DBC4');ax.set_ylim(bottom=0)
    ax.tick_params(colors='#C9D6E2');ax.grid(alpha=.12,color='white')
    right=ax.twinx();right.plot(f.time_s-f.time_s.iloc[0],f.rpm,color='#F5BE65',alpha=.7,linewidth=1,label='Sūkiai');right.set_ylabel('Sūkiai, aps./min.',color='#F5BE65');right.tick_params(colors='#C9D6E2');right.set_ylim(bottom=0)
    for axes in [ax,right]:
        for spine in axes.spines.values():spine.set_color('#3A4D60')
    figure.tight_layout(pad=1.5)
    return f

def launch():
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from app import analyse_file
    bg='#0B1724';panel='#142638';fg='#EDF4FA';muted='#A9BDCE';accent='#43DBC4'
    win=tk.Tk();win.title('Degalų sąnaudų rekomendacijos | įrašo analizė');win.geometry('1220x820');win.minsize(980,700);win.configure(bg=bg)
    style=ttk.Style(win);style.theme_use('clam')
    style.configure('TButton',background='#21445A',foreground=fg,font=('Segoe UI',10),padding=(12,8));style.map('TButton',background=[('active','#2C5B74')])
    def label(parent,text,size=11,color=fg,**kw):return tk.Label(parent,text=text,font=('Segoe UI',size),bg=kw.pop('bg',bg),fg=color,**kw)
    header=tk.Frame(win,bg=bg);header.pack(fill='x',padx=24,pady=(18,10))
    label(header,'VAŽIAVIMO ANALIZĖ',22).pack(anchor='w')
    label(header,'Išsaugoto įrašo peržiūra ir paaiškinamos rekomendacijos',11,muted).pack(anchor='w',pady=4)
    controls=tk.Frame(win,bg=bg);controls.pack(fill='x',padx=24,pady=7)
    path=tk.StringVar(value=str(ROOT/'data/demo_trip.csv'));state={'result':None}
    entry=tk.Entry(controls,textvariable=path,font=('Segoe UI',10),bg=panel,fg=fg,insertbackground=fg,relief='flat');entry.pack(side='left',fill='x',expand=True,ipady=10,padx=(0,10))
    def browse():
        name=filedialog.askopenfilename(initialdir=ROOT/'demonstraciniai_duomenys',filetypes=[('Važiavimo CSV','*.csv')])
        if name:path.set(name);show()
    ttk.Button(controls,text='Pasirinkti CSV',command=browse).pack(side='left',padx=4)
    ttk.Button(controls,text='Analizuoti',command=lambda:show()).pack(side='left',padx=4)
    def export():
        if state['result'] is None:return
        name=filedialog.asksaveasfilename(defaultextension='.json',initialfile='analizes_rezultatas.json',filetypes=[('JSON','*.json')])
        if name:
            try:Path(name).write_text(json.dumps(state['result'],ensure_ascii=False,indent=2),encoding='utf-8');status.set('Rezultatas išsaugotas.')
            except OSError as e:messagebox.showerror('Nepavyko išsaugoti',str(e))
    ttk.Button(controls,text='Išsaugoti rezultatą',command=export).pack(side='left',padx=4)
    quick=tk.Frame(win,bg=bg);quick.pack(fill='x',padx=24,pady=6)
    label(quick,'Demonstracinis įrašas',10,muted).pack(side='left',padx=(0,10))
    demos={p.stem:p for p in sorted((ROOT/'demonstraciniai_duomenys').glob('0*.csv'))}
    choice=ttk.Combobox(quick,values=list(demos),state='readonly',width=44);choice.pack(side='left')
    def select(event=None):
        if choice.get() in demos:path.set(str(demos[choice.get()]));show()
    choice.bind('<<ComboboxSelected>>',select)
    metrics=tk.Frame(win,bg=bg);metrics.pack(fill='x',padx=24,pady=12);values={}
    for key,title in [('style','VAIRAVIMO PROFILIS'),('distance','ATSTUMAS'),('fuel','SĄNAUDOS PAGAL SRAUTĄ'),('events','REKOMENDACIJŲ TEMOS')]:
        box=tk.Frame(metrics,bg=panel);box.pack(side='left',fill='both',expand=True,padx=(0,8))
        label(box,title,9,muted,bg=panel).pack(anchor='w',padx=14,pady=(10,4));v=tk.StringVar(value='—');values[key]=v
        tk.Label(box,textvariable=v,font=('Segoe UI',19,'bold'),bg=panel,fg=accent).pack(anchor='w',padx=14,pady=(0,12))
    summary=tk.StringVar();tk.Label(win,textvariable=summary,font=('Segoe UI',11),bg=bg,fg=fg,anchor='w',wraplength=1100).pack(fill='x',padx=24,pady=(0,8))
    content=tk.PanedWindow(win,orient='horizontal',bg=bg,sashwidth=10,bd=0);content.pack(fill='both',expand=True,padx=24,pady=5)
    chart=tk.Frame(content,bg=panel);content.add(chart,minsize=480,stretch='always')
    label(chart,'PRADINIO ĮRAŠO SIGNALAI',10,muted,bg=panel).pack(anchor='w',padx=15,pady=10)
    fig=Figure(figsize=(7,3.5),dpi=95);canvas=FigureCanvasTkAgg(fig,master=chart);canvas.get_tk_widget().pack(fill='both',expand=True)
    tips=tk.Frame(content,bg=panel);content.add(tips,minsize=300,width=380)
    label(tips,'REKOMENDACIJOS',12,fg,bg=panel).pack(anchor='w',padx=16,pady=12)
    text=tk.Text(tips,wrap='word',bg=panel,fg=fg,font=('Segoe UI',11),relief='flat',padx=16,pady=10,state='disabled',width=34)
    scroll=ttk.Scrollbar(tips,command=text.yview);scroll.pack(side='right',fill='y');text.configure(yscrollcommand=scroll.set);text.pack(fill='both',expand=True)
    status=tk.StringVar(value='');tk.Label(win,textvariable=status,bg=bg,fg=muted,font=('Segoe UI',10),anchor='w',wraplength=1150).pack(fill='x',padx=24,pady=(8,3))
    label(win,'Mokomasis prototipas. Pavyzdiniai duomenys sintetiniai. Sutaupymas neišmatuotas. ECU nekeičiamas.',10,muted).pack(anchor='w',padx=24,pady=(0,14))
    def show():
        try:
            a=analyse_file(path.get());frame=pd.read_csv(path.get());plot_trip(frame,fig);canvas.draw()
            state['result']=a;values['style'].set('Intensyvesnis' if a['style'] else 'Tolygesnis');values['distance'].set(f"{a['distance_km']:.2f} km")
            values['fuel'].set(f"{a['l100']:.2f} l/100 km" if a['l100'] is not None else 'Nėra duomenų')
            topics=[r for r in a['recommendations'] if r['code']!='stebejimas'];values['events'].set(str(len(topics)))
            summary.set(a['summary']);text.configure(state='normal');text.delete('1.0','end')
            for i,r in enumerate(a['recommendations'],1):text.insert('end',f"{i}. {r['text']}\n\n")
            text.configure(state='disabled');status.set(f"Atidaryta: {Path(path.get()).name}. Klasių įvertis ir įvykių taisyklės yra atskiri rezultatai.")
        except Exception as e:
            state['result']=None;status.set('Analizė nepavyko. Ekrane gali likti ankstesnio įrašo rodiniai.');messagebox.showerror('Duomenų klaida',str(e))
    show();win.mainloop()
