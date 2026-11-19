"""Check service-shutter geometry and deliberate dimensional faults, in millimetres."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
NOMINAL={
  'closed_left_x':66., 'bore_center_x':92., 'bore_width':16., 'stroke':40.,
  'blade_center_before_mouth':.95, 'blade_thickness':.60, 'blade_thickness_tolerance':.03,
  'alignment_to_actual_mouth':.18, 'axial_guide_play':.08, 'elastic_flatness':.10,
  'mated_exposed_shell_min':1.85, 'closed_at_switch_datum':55.75,'closed_error':.50,
  'closed_low':54.50,'closed_high':57.,'direct_open_travel':10.,
  'coupling_lost_motion_max':.60, 'travel_registration_error':.70,
  'shell_center_error':.60, 'guide_stroke_error':.50, 'blade_min_z':17., 'blade_max_z':37.,
  'usb_center_z':27.28,'bore_height':9.,'vertical_registration_error':.65,
  'al1_bolt_diameter_min':9.9,'al1_bolt_diameter_max':10.05,'al1_strike_bore_max':10.7,
  'al1_endplay_side_registration':.30,'al1_fixed_axis':52.,'al1_strike_left':0.,'al1_strike_right':114.
}

def validate(d):
    c=d['bore_center_x']; aperture_left=c-d['bore_width']/2; aperture_right=c+d['bore_width']/2
    clearance=(d['blade_thickness']+d['blade_thickness_tolerance'])/2+sum(d[k] for k in
        ('alignment_to_actual_mouth','axial_guide_play','elastic_flatness'))
    reach=d['blade_center_before_mouth']
    # Conservatively allow the full insertion window, plus mechanical lost motion.
    open_at=d['direct_open_travel']+d['coupling_lost_motion_max']+(d['closed_high']-d['closed_low'])
    crack=aperture_left-d['closed_left_x']-d['travel_registration_error']
    # Centreline alone gives a conservative lower bound for where the closing
    # blade has already struck the shell sidewall in either plug orientation.
    held=c-d['shell_center_error']-d['closed_left_x']-d['travel_registration_error']
    # Full cylinder projected through the one stationary-axis bolt keeper before key release.
    hasp=(d['al1_strike_bore_max']-d['al1_bolt_diameter_min'])/2+d['al1_endplay_side_registration']
    gaps={
      'key_release_before_any_access':crack-hasp,
      'full_diameter_bolt_on_solid_at_end_of_stroke':d['al1_fixed_axis']-d['al1_bolt_diameter_max']/2-d['al1_endplay_side_registration']-(d['al1_strike_left']+d['stroke']+d['guide_stroke_error']),
      'stand_off_from_receptacle':reach-clearance,
      'inside_exposed_shell_region':d['mated_exposed_shell_min']-reach-clearance,
      'direct_open_before_any_aperture_visible':crack-open_at,
      'plug_blocks_closure_before_possible_remake':held-open_at,
      'open_position_clearance_to_full_bore':d['closed_left_x']+d['stroke']-d['guide_stroke_error']-d['travel_registration_error']-aperture_right,
      'blade_covers_upper_bore':d['blade_max_z']-d['vertical_registration_error']-(d['usb_center_z']+d['bore_height']/2),
      'blade_covers_lower_bore':d['usb_center_z']-d['bore_height']/2-d['blade_min_z']-d['vertical_registration_error'],
      'closed_key_lower_window':d['closed_at_switch_datum']-d['closed_error']-d['closed_low'],
      'closed_key_upper_window':d['closed_high']-(d['closed_at_switch_datum']+d['closed_error'])
    }
    return {k:round(v,3) for k,v in gaps.items()},dict(direct_open_by=open_at,first_visible_at=crack,
        retained_plug_prevents_closure_below=held,AL1_bolt_engagement_only_up_to=hasp)

if __name__=='__main__':
    gaps,events=validate(NOMINAL)
    assert min(gaps.values())>0
    cases={'blocked_on_mated_plug':({'blade_center_before_mouth':2.1},'inside_exposed_shell_region'),
           'opens_too_early':({'closed_left_x':76.},'direct_open_before_any_aperture_visible'),
           'incorrect_key_position':({'closed_at_switch_datum':57.2},'closed_key_upper_window'),
           'short_striker_releases_key_with_gate_open':({'al1_strike_left':14.},'full_diameter_bolt_on_solid_at_end_of_stroke'),
           'insufficient_full_open_stroke':({'stroke':30.},'open_position_clearance_to_full_bore')}
    for name,(changes,key) in cases.items():
        result,_=validate({**NOMINAL,**changes})
        assert result[key]<0,name
    report={'dimensions_mm':NOMINAL,'worst_case_positive_margins_mm':gaps,'events_in_mm_from_RUN_stop':events,
            'negative_controls_detected':list(cases),'physical_drop_time_tested':False,'physical_gate_tested':False,
            'system_timing_guaranteed':False}
    (ROOT/'kinematic-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['worst_case_positive_margins_mm']))
