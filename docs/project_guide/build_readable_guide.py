"""Reflow the complete guide as a larger-print reading edition.

Uses the same frozen facts as the original guide, with a new plain-English
introduction, 14-point body text, a live table of contents, and a separate
three-page task appendix. Does not interact with the running experiment.
"""
from pathlib import Path
from html import escape
import json
import shutil

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    Table, TableStyle, CondPageBreak, KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents

import build_guide as source

HERE=Path(__file__).resolve().parent
OUT=HERE/'Stepwise_Confidence_Easy_Read.pdf'
W,H=A4
LEFT=50
CW=W-2*LEFT
INK=colors.HexColor('#152935')
ACCENT=colors.HexColor('#00676B')
GRAY=colors.HexColor('#425563')
PALE=colors.HexColor('#EDF5F5')
LINE=colors.HexColor('#CFDDE2')

STYLES={
    'body':ParagraphStyle('read_body',fontName='Guide',fontSize=14,leading=21,
                          textColor=INK,spaceAfter=11,allowWidows=0,allowOrphans=0),
    'lead':ParagraphStyle('read_lead',fontName='Guide',fontSize=15,leading=22.5,
                          textColor=INK,spaceAfter=15),
    'title':ParagraphStyle('read_title',fontName='GuideBold',fontSize=27,leading=33,
                           textColor=INK,spaceAfter=18,keepWithNext=True),
    'section':ParagraphStyle('read_section',fontName='GuideBold',fontSize=22,leading=28,
                             textColor=INK,spaceBefore=19,spaceAfter=12,keepWithNext=True),
    'sub':ParagraphStyle('read_sub',fontName='GuideBold',fontSize=16,leading=21,
                         textColor=ACCENT,spaceBefore=12,spaceAfter=8,keepWithNext=True),
    'small':ParagraphStyle('read_small',fontName='Guide',fontSize=12,leading=17,
                           textColor=GRAY,spaceAfter=11),
    'code':ParagraphStyle('read_code',fontName='GuideMono',fontSize=12,leading=17,
                          textColor=INK,wordWrap='CJK',spaceAfter=13,
                          borderPadding=9,borderColor=LINE,borderWidth=.6,
                          backColor=colors.HexColor('#F4F7F8')),
    'note':ParagraphStyle('read_note',fontName='Guide',fontSize=14,leading=21,
                          textColor=INK,spaceBefore=8,spaceAfter=17,
                          borderPadding=10,borderColor=LINE,borderWidth=.7,
                          backColor=PALE),
    'cell':ParagraphStyle('read_cell',fontName='Guide',fontSize=12.5,leading=17,
                          textColor=INK),
    'head':ParagraphStyle('read_head',fontName='GuideBold',fontSize=12.5,leading=17,
                          textColor=colors.white),
    'toc':ParagraphStyle('read_toc',fontName='Guide',fontSize=12.5,leading=19,
                         textColor=INK,spaceAfter=7,leftIndent=0,rightIndent=27),
}


def p(text,style='body'):
    return Paragraph(source.marked(text),STYLES[style])


class GuideDoc(BaseDocTemplate):
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='read_section':
            title=flowable.getPlainText()
            key='section-'+str(self.seq.nextf('sections'))
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title,key,0,False)
            self.notify('TOCEntry',(0,title,self.page,key))


def decorate(canvas,doc):
    canvas.saveState()
    canvas.setFillColor(ACCENT);canvas.rect(0,H-7,W,7,fill=1,stroke=0)
    canvas.setFont('GuideBold',10);canvas.setFillColor(GRAY)
    canvas.drawString(LEFT,H-30,'STEPWISE CONFIDENCE  |  EASY-READ EDITION')
    canvas.setStrokeColor(LINE);canvas.line(LEFT,36,W-LEFT,36)
    canvas.setFont('Guide',9.5)
    canvas.drawString(LEFT,22,'Team 11 • October 29, 2026 • Dated project snapshot')
    canvas.drawRightString(W-LEFT,22,str(doc.page))
    canvas.restoreState()


def title(text):
    return p(text,'section')


def append_text(story,text,kind='body'):
    # Short reading paragraphs; preserve every sentence of the original facts.
    if kind=='body' and len(text.split())>70:
        import re
        sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z])',text)
        current=[]
        for sentence in sentences:
            current.append(sentence)
            if len(' '.join(current).split())>=45:
                story.append(p(' '.join(current)));current=[]
        if current:story.append(p(' '.join(current)))
    else:story.append(p(text,kind))


def numeric_table(rows,widths=None):
    widths=widths or [CW/len(rows[0])]*len(rows[0])
    cells=[[p(cell,'head' if i==0 else 'cell') for cell in row] for i,row in enumerate(rows)]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),INK),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
    ]))
    return t


def readable_table(story,rows,ratios=None):
    # Numeric comparisons remain tables; explanatory comparisons become full-width prose.
    first=rows[0][0]
    if first=='Completed method':
        concise=[['Method','AUROC','Top-1']]+rows[1:]
        story.extend([numeric_table(concise,[CW*.51,CW*.245,CW*.245]),Spacer(1,13)])
        return
    if first=='Reference':
        concise=[['Reference','Similarities','Max','Mean']]+rows[1:]
        story.extend([numeric_table(concise,[CW*.21,CW*.37,CW*.21,CW*.21]),Spacer(1,13)])
        return
    if first=='Held-out fold':
        concise=[['Fold','Test runs']]+[[row[0],row[1]] for row in rows[1:]]
        story.extend([numeric_table(concise,[CW*.55,CW*.45]),Spacer(1,13)])
        story.append(p('In each fold, the other task groups provide training and validation data.'))
        return
    for row in rows[1:]:
        story.append(CondPageBreak(95))
        story.append(p(str(row[0]),'sub'))
        if len(row)==2:
            append_text(story,str(row[1]))
        else:
            for label,value in zip(rows[0][1:],row[1:]):
                append_text(story,'**'+str(label)+':** '+str(value))


def pipeline(story):
    steps=[('Generate and check the runs','Save complete executions and separate infrastructure errors.'),
           ('Turn runs into graphs','Represent the actions, results and inferred dependencies.'),
           ('Choose successful references','Use successful runs from the correct data partition.'),
           ('Compute MCS targets','Measure structural agreement with successful examples.'),
           ('Train the small GCN','Teach it to predict the per-step target scores.'),
           ('Evaluate on held-out tasks','Compare with baselines using separate correctness labels.')]
    for i,(a,b) in enumerate(steps,1):
        story.append(KeepTogether([p(f'{i}. {a}','sub'),p(b)]))


def graph(story):
    story.append(p('A simple example','sub'))
    story.append(p('User request / initial state','note'))
    story.append(p('↓  get_reservation_details(...)','body'))
    story.append(p('Reservation details returned by the tool','note'))
    story.append(p('↓  cancel_reservation(...)','body'))
    story.append(p('Cancellation result returned by the tool','note'))
    story.append(p('The result boxes are nodes. The operations connecting them are edges.','body'))


def render_blocks(story,blocks):
    for block in blocks:
        kind=block[0]
        if kind in {'p','lead','small','sub','code','note'}:
            append_text(story,block[1],{'p':'body'}.get(kind,kind))
        elif kind=='bullets':
            for text in block[1]:
                story.append(p('• '+text))
        elif kind=='table':readable_table(story,block[1],block[2])
        elif kind=='pipeline':pipeline(story)
        elif kind=='graph':graph(story)
        elif kind=='link':
            story.append(Paragraph('<link href="'+escape(block[2],quote=True)+'" color="#00676B"><u>'+escape(block[1])+'</u></link>',STYLES['small']))


def build():
    story=[Spacer(1,38),p('Your project,\nstep by step','title'),
           p('A larger-print guide to step-level confidence for airline agents.','lead'),
           p('NIBS • MCS • GIBS • C4','sub'),
           Spacer(1,15),
           p('The problem we are solving','sub'),
           p('An airline assistant makes many decisions in one conversation. The benchmark tells us whether the whole task passed or failed. We want to help identify which individual actions deserve inspection.'),
           p('The main idea','sub'),
           p('Compare an execution with successful examples. Use those comparisons to create step-level targets. Then train a small graph model to predict those targets for a new execution.'),
           p('What this edition changes','sub'),
           p('Bigger text, shorter paragraphs, fewer dense tables, clickable contents, and a separate task-results appendix. The complete technical explanation is retained.'),
           p('Project snapshot: '+source.SNAP['created_arizona'],'small'),
           p('This is a guide to the current project, not a claim that unfinished experiments have completed.','note'),PageBreak(),
           title('Start here: the project in six steps')]
    plain=[('1. We collected 1,000 executions.',
            'There are 50 airline tasks. We ran each task 20 times. We saved the conversation, tool calls, tool results and final reward. This part is complete.'),
           ('2. We identified successful examples.',
            'A successful run gives us a reference pattern for the same task. A passing run can still contain mistakes, so suspicious references need review.'),
           ('3. NIBS compares steps directly.',
            'It asks: does this action look like actions in successful runs? It does not train a model. The baseline results are complete.'),
           ('4. MCS compares connected patterns.',
            'We turn executions into graphs. MCS looks for similar actions and results that connect in compatible ways. These matches become targets for training. This stage is still running in the snapshot.'),
           ('5. GIBS trains a small GCN.',
            'The GCN learns to predict those per-step targets from a graph. We are not training the Qwen language model. C4 uses the same predictor with stricter target-generation rules.'),
           ('6. We check whether the scores are useful.',
            'We score held-out executions and compare the methods against independent correctness judgements. Final task pass rates and agreement with successful runs do not, by themselves, prove step-level accuracy.')]
    for heading,body in plain:
        story.extend([CondPageBreak(120),p(heading,'sub'),p(body)])
    story.extend([p('The three numbers you will see','sub'),
                  p('**1,000:** all generated trajectories.\n**860:** eligible MCS training/validation queries.\n**911:** queries with enough references for the common NIBS comparison.'),
                  p('You do not need a forced 50:50 pass/fail split to follow the paper. The current collection has 680 passes and 320 failures.','note'),PageBreak(),
                  title('Contents')])
    toc=TableOfContents();toc.levelStyles=[STYLES['toc']];toc.dotsMinLevel=0
    story.extend([toc,PageBreak()])
    # The original cover/reading map are replaced. Every substantive section remains.
    for item in source.PAGES[2:-1]:
        story.extend([CondPageBreak(150),title(item['title']),p(item['subtitle'],'small')])
        render_blocks(story,item['blocks'])
        story.append(Spacer(1,13))
    # All 50 task outcomes in a separate, comfortably sized appendix.
    rows=source.SNAP['task_rows']
    for start in range(0,len(rows),17):
        chunk=rows[start:start+17]
        story.append(PageBreak())
        heading='Appendix: all 50 task outcomes' if start==0 else f'Appendix continued: tasks {chunk[0]["task_id"]}–{chunk[-1]["task_id"]}'
        story.extend([title(heading),p('Each task has 20 runs. These are fresh Qwen benchmark outcomes.','small')])
        data=[['Task','Pass','Fail','MCS eligible','NIBS eligible']]
        data.extend([[r['task_id'],r['passes'],r['failures'],r['mcs_eligible'],r['nibs_eligible']] for r in chunk])
        story.extend([numeric_table(data,[CW*.12,CW*.13,CW*.13,CW*.31,CW*.31]),Spacer(1,15),
                      p('“Eligible” means references are available under that method’s rules. It does not mean MCS computation or GCN training has completed.','small')])
        if start+17>=len(rows):
            story.extend([p('Collection totals','sub'),p('1,000 runs • 680 passes • 320 failures\n860 MCS-target-eligible queries • 911 NIBS-eligible queries')])
    doc=GuideDoc(str(OUT),pagesize=A4,leftMargin=LEFT,rightMargin=LEFT,
                 topMargin=55,bottomMargin=52,title='Your Project, Step by Step — Easy-Read Edition',
                 author='CSE598 Team 11',pageCompression=1)
    doc.addPageTemplates(PageTemplate(id='readable',frames=[Frame(LEFT,52,CW,H-107,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=decorate))
    doc.multiBuild(story)
    print(OUT)


if __name__=='__main__':build()
