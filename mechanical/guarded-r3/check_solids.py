"""Check nominal shutter travel and plug engagement with intersecting CAD solids."""
from pathlib import Path
import json
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from build import fixed,carriage,envelope,box,O

def bounds(shape):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(shape,b,False,False)
 return (*b.CornerMin().Coord(),*b.CornerMax().Coord())

def overlap(a,b):
 A=bounds(a);B=bounds(b)
 if any(min(A[i+3],B[i+3])-max(A[i],B[i])<=1.e-7 for i in range(3)):return 0
 props=GProp_GProps();BRepGProp.VolumeProperties_s(BRepAlgoAPI_Common(a,b).Shape(),props)
 return max(0,props.Mass())

def shell(x,y,z):
 # Conservative rectangular shell model along insertion direction. Sidewalls intersect the
 # full-height blade irrespective of roll about the insertion axis of a mated 0/180° plug.
 from build import cut
 return cut(box(x-4.11,y,z-1.15,8.22,3.5,2.3),box(x-3.86,y-.1,z-.90,7.72,3.7,1.80))

if __name__=='__main__':
 static=fixed()
 findings=[]
 for travel in (0.,.7,5.,13.1,17.3,21.,24.7,30.,36.,40.):
  mobile=carriage(travel);assembly=envelope(travel)
  for item,solid,_ in mobile:
   for stat,other,_ in static+[(n,s,c)for n,s,c in assembly if n.startswith(('J40','Local board','D4NS'))]:
    volume=overlap(solid,other)
    if volume>1.e-5:findings.append((travel,item,stat,round(volume,4)))
 # Test each permissible corner, both nominally equivalent 180-degree orientations and the limit
 # where a held plug must have already blocked the returning gate.
 held=24.7; plug_checks=0
 for dx in (-.6,.6):
  for dz in (-.65,.65):
   for axial in (-.36,.36):
    sh=shell(92+dx,23.1+axial,27.28+dz)
    blade=carriage(held)[0][1]
    assert overlap(blade,sh)>.01 and overlap(carriage(40)[0][1],sh)==0
    plug_checks+=1
 # AL1 has a unique release window. A bolt extended into the fixed keeper
 # must physically meet the moving plate at every sampled open position.
 bolt=envelope(0)[0][1]
 strike_at=lambda t:next(s for name,s,_ in carriage(t) if 'single-window' in name)
 assert overlap(bolt,strike_at(0))<1.e-6
 obstructed=[t for t in (1.,5.,13.1,17.3,24.7,35.,40.) if overlap(bolt,strike_at(t))>.01]
 assert len(obstructed)==7
 report={'AL1_bolt_clear_at_closed':True,'AL1_release_obstructed_at_strokes_mm':obstructed,
         'stroke_samples':10,'fixed_to_carriage_solid_interferences_mm3':findings,
         'minimum_shell_plug_corners':plug_checks,'plug_contacts_blade_at_or_before_return_travel_mm':held,
         'both_usb_rolls_same_section':True,'hardware_tested':False}
 (O/'solid-check.json').write_text(json.dumps(report,indent=2)+'\n');print(findings)
 raise SystemExit(bool(findings))
