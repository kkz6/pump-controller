"""Linear RC model of probe frontend. Does not model semiconductor/surge behavior.
Requires numpy; outputs calculated (not measured) margins.
"""
import numpy as np
from pathlib import Path

def simulate(rwet, cable=3e-9, coupling=3e-9, inter=0.5e-9, block=1e-6, supply=3.3, dt=25e-6, common_block=None, sample_offset=0):
    n=3+4*len(rwet)
    G=np.zeros((n,n)); C=np.zeros((n,n)); b=np.zeros(n)
    def stamp(M,a,z,v):
        M[a,a]+=v
        if z is not None:
            M[z,z]+=v; M[a,z]-=v; M[z,a]-=v
    stamp(G,0,None,1/2200); b[0]=1/2200
    stamp(C,0,1,common_block if common_block is not None else 2*block); stamp(G,1,2,1/9980)
    stamp(C,2,None,cable)
    sense=[]
    for j,r in enumerate(rwet):
        e,f,s,p=3+4*j,4+4*j,5+4*j,6+4*j
        stamp(G,2,e,1/r); stamp(G,e,f,1/20000)
        stamp(C,f,s,block); stamp(G,s,None,1/47000)
        stamp(G,s,p,1/22000); stamp(C,p,None,1e-9)
        stamp(G,p,None,1/1e6) # conservative: model mux bias loading on every channel
        stamp(C,e,None,cable); stamp(C,2,e,coupling)
        for k in range(j): stamp(C,e,3+4*k,inter)
        sense.append(p)
    # 1 teraohm numerical gmin only; not physical BOM resistors.
    G+=np.eye(n)*1e-12
    M=np.linalg.inv(G+C/dt); T=M@(C/dt); B=M@b
    v=np.zeros(n); amp=supply*43/(27+43)/2
    half=round(.020/dt); period=2*half
    records=[]
    for t in range(25*period):
        drive=amp if (t//half)%2==0 else -amp
        v=T@v+B*drive
        if t>=24*period: records.append(v.copy())
    records=np.array(records)
    result=[]
    for j,idx in enumerate(sense):
        # ADC conversion interval representative of 860 SPS +-10% timing.
        starts=[.0071,.0091,.0111,.0131,.0151]
        start=round((starts[j]+sample_offset)/dt); end=round((starts[j]+sample_offset+.0013)/dt)
        a=records[start:end,idx].mean(); z=records[start+half:end+half,idx].mean()
        result.append((a-z)/2)
    return result, float(records[:,sense].min()),float(records[:,sense].max())

if __name__=='__main__':
    cases=[('4 wet 100k, nominal cable',[1e5]*4,{}),
           ('4 wet 100k, severe cable',[1e5]*4,{'cable':10e-9,'coupling':10e-9,'inter':2e-9}),
           ('4 dry 1M, nominal cable',[1e6]*4,{}),
           ('4 dry open, severe cable',[1e12]*4,{'cable':10e-9,'coupling':10e-9,'inter':2e-9}),
           ('one dry 1M, three wet short',[1e6,1e-3,1e-3,1e-3],{}),
           ('4 wet short',[1e-3]*4,{}),
           ('4 wet 100k, block C -30%, VDD -5%',[1e5]*4,{'block':700e-9,'supply':3.135}),
           ('top 100k, lower three short',[1e-3,1e-3,1e-3,1e5],{}),('top 100k, lower short, C-30% VDD-5%',[1e-3,1e-3,1e-3,1e5],{'block':700e-9,'supply':3.135}),('inlet wet 100k',[1e5],{'sample_offset':.008}),('inlet dry 1M',[1e6],{'sample_offset':.008})]
    lines=['CALCULATED LINEAR RC MODEL; NOT HARDWARE VALIDATION','25 Hz; 25 us backward-Euler; 1.0 s settling; bipolar ADC windows.']
    for name,rs,kw in cases:
        vals,mn,mx=simulate(rs,**kw)
        lines.append(f'{name}: half-amplitude V='+','.join(f'{x:.4f}' for x in vals)+f'; AC node span {mn:.4f}..{mx:.4f} V about 1.65 V')
    out='\n'.join(lines)+'\n'
    print(out)
    Path(__file__).with_name('probe-calculation.txt').write_text(out)
