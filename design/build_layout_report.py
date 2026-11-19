"""Create a layout-status cover and annotate native PCB PDF proof pages."""
import io
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pypdf import PdfReader, PdfWriter
from build_report import para, table, heading, footer, INK, GRAY

P=Path(__file__).resolve().parents[1]
E=P/'hardware/exports'
D=json.loads((P/'hardware/checks/layout-summary.json').read_text())
V=json.loads((P/'hardware/checks/via-in-pad-audit.json').read_text())
rows=[['Layout check','Recorded result'],
      ['Outline / stack',f"{D['dimensions_mm'][0]} x {D['dimensions_mm'][1]} mm / {D['layers']} copper layers"],
      ['Fitted electrical components',str(D['component_count'])],
      ['Remaining unconnected items',str(D['remaining_unrouted'])],
      ['Native DRC errors / warnings',f"{D['native_drc_errors']} / {D['native_drc_warnings']}"],
      ['Board pad nets match circuit source','PASS' if D['board_netlist_matches_source'] else 'FAIL / see board-netlist-check.json'],
      ['R2 filled heat-spreading copper',f"{D['R2_filled_copper_mm2']} mm2; minimum {D['R2_required_copper_mm2']} mm2"],
      ['Live / isolated spacing corridor',f"{D['isolation_corridor_mm']} mm layout rule"],
      ['Via-in-pad assembly requirement',f"{V['unique_via_count']} vias / {V['overlap_count']} pad overlaps; filled and plated over, or reroute before fabrication"],
      ['Fabrication release','NOT RELEASED - engineering prototype']]
story=[para('PCB layout review','Title2'),para('The following pages show the native board at the recorded design state. Read connectivity and DRC counts together; a rendered board alone does not establish electrical completion.'),table(rows,[195,303]),heading('Scope of verification'),para('The checks cover CAD geometry and assigned connections. Component land patterns, contactor-coil suitability, mains insulation/protection coordination, surge/EMC, closed-starter temperature, probe behavior and firmware still need review or physical validation.'),heading('Physical envelope'),para('Board dimensions exclude connector plugs, cable bends, insulation covers, fasteners, antenna and the separate OLED module. Measure the intended starter before making enclosure holes. Preserve the separation between live conductors and isolated controls in the complete assembly.'),heading('Sources for this review'),para('hardware/checks/layout-summary.json\nhardware/checks/main-drc.json\nhardware/checks/board-netlist-check.json\nhardware/checks/schematic-verification.json\nhardware/checks/via-in-pad-audit.json\ndesign/fabrication-constraints.txt','Smallx')]
if D['remaining_unrouted'] or D['native_drc_errors'] or not D['board_netlist_matches_source']:
    story.insert(2,para('OPEN LAYOUT WORK: this board is not electrically complete or ready to manufacture. The native reports identify the remaining items.','H2x'))
SimpleDocTemplate(str(E/'layout-00-status.pdf'),pagesize=A4,leftMargin=17*mm,rightMargin=17*mm,topMargin=19*mm,bottomMargin=22*mm).build(story,onFirstPage=footer,onLaterPages=footer)

for side in ['front','back']:
    source=E/('pcb-'+side+'-raw.pdf')
    if not source.exists():continue
    reader=PdfReader(source);writer=PdfWriter()
    for page in reader.pages:
        w,h=float(page.mediabox.width),float(page.mediabox.height)
        stream=io.BytesIO();c=canvas.Canvas(stream,pagesize=(w,h))
        c.setFillColor(INK);c.setFont('Helvetica-Bold',12)
        c.drawString(15*mm,h-15*mm,'MAIN PCB / '+('FRONT' if side=='front' else 'BOTTOM - MIRRORED VIEW')+' / REV C PROTOTYPE')
        c.setFillColor(GRAY);c.setFont('Helvetica',8)
        c.drawString(15*mm,12*mm,f"90 x 70 mm | {D['remaining_unrouted']} unconnected items | DRC {D['native_drc_errors']} errors, {D['native_drc_warnings']} warnings | Not a fabrication release")
        c.save();stream.seek(0);page.merge_page(PdfReader(stream).pages[0]);writer.add_page(page)
    dest=E/('layout-01-front.pdf' if side=='front' else 'layout-02-back.pdf')
    with dest.open('wb') as f:writer.write(f)
print('Created layout status and available PCB proof pages')
