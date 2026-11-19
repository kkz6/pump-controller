from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[2];p=json.loads((R/'mechanical/rev-e/parameters.json').read_text());w=p['box']['width'];d=p['box']['depth'];pa=p['panel'];ox,oy=p['oled']['centre']
s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{d}mm" viewBox="0 0 {w} {d}">', '<rect x="0.25" y="0.25" width="169.5" height="149.5" rx="3" fill="white" stroke="#c3cbd0" stroke-width="0.2"/>','<text x="15" y="23" font-family="sans-serif" font-size="5" font-weight="bold" fill="#173f50">PUMP CONTROLLER</text>']
s.append(f'<rect x="{ox-13}" y="{d-oy-4}" width="26" height="8" rx="0.4" fill="#fff" stroke="#777" stroke-width="0.2"/>')
for b in pa['buttons']:
 x=pa['origin'][0]+b['xy'][0];y=d-(pa['origin'][1]+pa['size'][1]-b['xy'][1]);c='#bd312d' if b['name']=='STOP' else '#3c8054' if b['name']=='START' else '#465969'
 s.append(f'<circle cx="{x}" cy="{y}" r="3.25" fill="white" stroke="{c}" stroke-width="0.4"/><text x="{x}" y="{y+9}" text-anchor="middle" font-family="sans-serif" font-size="2.2" font-weight="bold" fill="{c}">{html.escape(b["name"])}</text>')
s.append('<text x="15" y="136" font-family="sans-serif" font-size="2.3" fill="#677d88">Rev E • 0.91in display • local controls</text>')
s.append('<path d="M15 143h20m-20 -1v2m20 -2v2" stroke="black" stroke-width="0.2"/><text x="25" y="141" font-family="sans-serif" font-size="2" text-anchor="middle">20 mm scale check</text></svg>')
(R/'output/enclosure-rev-e/front-label-template.svg').write_text('\n'.join(s))
