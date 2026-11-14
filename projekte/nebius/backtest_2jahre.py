#!/usr/bin/env python3
"""Backtest ueber 2 Jahre: Kursbewegung ueber Nacht gibt die Richtung fuer den Tag vor.

US-Version der L&S-Regel (rueckwirkend nur mit US-Daten moeglich):
  Variante A: Signal = Kurs 23:00 (Vortag) -> erster Vorboersenkurs ~10:00 deutscher Zeit,
              Einstieg zu diesem Kurs, Ausstieg 21:30.
  Variante B: Signal = 23:00 -> US-Eroeffnung 15:30, Einstieg 15:30, Ausstieg 21:30.
Plus = LONG, Minus = SHORT. Kosten 0,2 % je Trade abgezogen.
Erwartet daten/prepost_2y.json (Yahoo-Stundenkerzen inkl. Vor-/Nachboerse), siehe hole_daten().
"""
import os, sys, time, urllib.request
import json,datetime,statistics as st,random
from zoneinfo import ZoneInfo
NY=ZoneInfo('America/New_York'); DE=ZoneInfo('Europe/Berlin')
SYM = sys.argv[1:] or ['NBIS','CRWV','NVDA','AMD','TSLA','IREN','PLTR','MU']
D = None
def B(dd,d): return [(datetime.datetime.combine(datetime.date.fromisoformat(d),datetime.time(*map(int,h.split(':'))),NY),o,c) for h,o,c in dd[d]]
def at(bars,t):
    for s,o,c in bars:
        if s==t: return o
    p=[x for x in bars if x[0]<=t]; return p[-1][1] if p else None

def hole_daten(symbole, pfad="daten/prepost_2y.json"):
    out = {}
    p2 = int(datetime.datetime.now(datetime.UTC).timestamp()); p1 = p2 - 728 * 86400
    for s in symbole:
        url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{s}?period1={p1}&period2={p2}"
               "&interval=60m&includePrePost=true")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; day-trader-skill backtest)"})
        r = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
        q = r["indicators"]["quote"][0]; d = {}
        for t, o, c in zip(r["timestamp"], q["open"], q["close"]):
            if c is None or o is None:
                continue
            dt = datetime.datetime.fromtimestamp(t, NY)
            d.setdefault(dt.date().isoformat(), []).append((dt.strftime("%H:%M"), o, c))
        out[s] = d; time.sleep(0.5)
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    json.dump(out, open(pfad, "w"))
    return out

def trades(sym,variant):
    dd=D[sym]; days=sorted(dd); out=[]
    for d0,d1 in zip(days,days[1:]):
        b0,b1=B(dd,d0),B(dd,d1); D0,D1=datetime.date.fromisoformat(d0),datetime.date.fromisoformat(d1)
        ref=at(b0,datetime.datetime.combine(D0,datetime.time(23,0),DE).astimezone(NY))
        ex=at(b1,datetime.datetime.combine(D1,datetime.time(21,30),DE).astimezone(NY))
        if variant=='A':   # 10:00 DE Vorbörse
            pm=[x for x in b1 if x[0].hour<6]
            if not pm: continue
            ent=pm[0][1]
        else:              # US-Eröffnung 15:30 DE
            op=[x for x in b1 if x[0].hour==9 and x[0].minute==30]
            if not op: continue
            ent=op[0][1]
        if not ref or not ex: continue
        sig=(ent/ref-1)*100
        if sig==0: continue
        r=(ex/ent-1)*100
        out.append(dict(d=d1,sig=sig,raw=r,pnl=r if sig>0 else -r))
    return out
def summ(T,cost=0.2):
    if not T: return None
    v=[t['pnl']-cost for t in T]; e=1
    for x in v: e*=1+x/100
    return dict(n=len(v),avg=st.mean(v),win=sum(x>0 for x in v)/len(v)*100,chain=100*(e-1),long=st.mean([t['raw']-cost for t in T]))
def pval(T,n=3000):
    random.seed(7); m=st.mean(t['pnl'] for t in T)
    return sum(st.mean(t['raw']*random.choice((1,-1)) for t in T)>=m for _ in range(n))/n*100
if __name__=='__main__':
    D = hole_daten(SYM)
    for var,lab in (('A','Signal 23:00→10:00, Einstieg 10:00 (Vorbörse)'),('B','Signal 23:00→15:30, Einstieg 15:30 (US-Eröffnung)')):
        print('=====',lab)
        for s in D:
            T=trades(s,var)
            for thr in (0,1,2):
                TT=[t for t in T if abs(t['sig'])>=thr]
                r=summ(TT)
                if r: print(f"{s:5s} >= {thr}%: n={r['n']:3d} Schnitt {r['avg']:+.2f}% Gewinner {r['win']:.0f}% Kette {r['chain']:+7.1f}% | immer LONG {r['long']:+.2f}% | Zufall>= {pval(TT):.0f}%" if thr==0 else f"{s:5s} >= {thr}%: n={r['n']:3d} Schnitt {r['avg']:+.2f}% Gewinner {r['win']:.0f}%")
