"""Four-page English project summary; leaves the active experiment untouched."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import shutil

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak
import build_guide as original

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'Stepwise_Confidence_4_Page_Summary.pdf'
state=json.loads((ROOT/'results/fresh_all_tasks/worker_state.json').read_text())
summary=json.loads((ROOT/'results/fresh_all_tasks/baseline_preview/summary.json').read_text())
checked=datetime.fromisoformat(state['checked_utc']).astimezone(ZoneInfo('America/Phoenix'))
stamp=checked.strftime('%B %d, %Y, %I:%M %p Arizona time')
progress=state['target_progress'];done=progress['completed_query_targets'];total=progress['total_eligible_queries']
W,H=A4;BODY=W-96
INK=colors.HexColor('#17313F');TEAL=colors.HexColor('#007277');PALE=colors.HexColor('#ECF5F5')
STYLE={
 'title':ParagraphStyle('four_title',fontName='GuideBold',fontSize=23,leading=28,textColor=INK,spaceAfter=10),
 'sub':ParagraphStyle('four_sub',fontName='GuideBold',fontSize=13.2,leading=17,textColor=TEAL,spaceBefore=9,spaceAfter=6,keepWithNext=True),
 'body':ParagraphStyle('four_body',fontName='Guide',fontSize=11.7,leading=16.1,textColor=INK,spaceAfter=8),
 'small':ParagraphStyle('four_small',fontName='Guide',fontSize=10,leading=13.3,textColor=INK,spaceAfter=7),
 'cell':ParagraphStyle('four_cell',fontName='Guide',fontSize=10.7,leading=14,textColor=INK),
 'head':ParagraphStyle('four_head',fontName='GuideBold',fontSize=10.7,leading=14,textColor=colors.white),
 'code':ParagraphStyle('four_code',fontName='GuideMono',fontSize=9.6,leading=13,textColor=INK,wordWrap='CJK',spaceAfter=8),
}

def p(s,kind='body'):return Paragraph(original.marked(s),STYLE[kind])
def table(rows,ratios):
    t=Table([[p(c,'head' if i==0 else 'cell') for c in row] for i,row in enumerate(rows)],
            colWidths=[BODY*r/sum(ratios) for r in ratios],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),
                          ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
                          ('VALIGN',(0,0),(-1,-1),'TOP'),
                          ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
                          ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return t

def note(s):
    t=Table([[p(s)]],colWidths=[BODY])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),
                          ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
                          ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
    return t

story=[]
def page(title):
    if story:story.append(PageBreak())
    story.append(p(title,'title'))
def text(s):story.append(p(s))
def sub(s):story.append(p(s,'sub'))
def bullet(s):text('• '+s)

page('1. The problem and our dataset')
text('**Goal:** identify suspicious individual actions inside an airline assistant’s execution, instead of receiving only a final task pass/fail result.')
text('An assistant can use the right tool but choose the wrong passenger, reservation, flight or payment. We want a confidence score for each analysed tool call or agent message so an engineer knows where to investigate.')
sub('What we generated — complete')
story.append(table([
 ['Item','Current project'],
 ['Dataset','tau2-bench Airline: simulated customers and sandboxed airline state.'],
 ['Scale','50 tasks × 20 runs = 1,000 distinct graded trajectories.'],
 ['Outcomes','680 passes / 320 failures; 68% task pass rate.'],
 ['Generating model','ASU-hosted Qwen3.8-27B for both assistant and user simulator.'],
 ['Temperatures','Assistant 1.0; user 0.0. No forced 50:50 outcome balance.'],
 ['One saved trajectory','Conversation, tool calls, observations and benchmark reward.'],
 ],[1.05,3.4]))
sub('Why repeat each task?')
text('Different executions reveal alternative successful patterns and mistakes. Successful runs become reference examples. Temperature 1.0 encourages variation but does not guarantee mixed outcomes: 12 tasks passed every run and one failed every run.')
sub('The workflow')
text('**Collect → audit → build graphs → split by task group → choose successful references → compute MCS targets → train GCNs → score held-out runs → compare with baselines.**')
text('A graph represents results as nodes and operations/dependencies as edges. The current experiment infers these links from observed events; it does not access the model’s hidden reasoning.')
story.append(note('We are adapting the paper’s method to tool-using agents. The original paper evaluates math/QA and uses larger training/evaluation sets. This is not an exact reproduction of its published benchmark results.'))

page('2. NIBS, MCS, GIBS and C4')
sub('NIBS: compare steps directly — no training')
text('Paper semantic NIBS compares a query step with steps in successful runs using BERT cosine similarity. **Max** takes the best match in each reference; **Mean** averages all step similarities in each reference. Both then average across references.')
text('The older **tool_sim** baseline compares tool names and argument values. It is an agent baseline, not the paper’s semantic NIBS. A similar-looking action is not automatically correct.')
sub('MCS: create graph-based training targets')
text('**Maximum Common Subgraph (MCS)** searches for a large compatible matching structure between a query graph and a successful reference graph. DeBERTa-MNLI scores operation/result similarity; node and edge thresholds are 0.7. Our search is approximate.')
text('For paper GIBS, a step is supported when its result node appears in the match. Average the indicators across references. Example: a step matched in four of five references gets a target of **0.8**. That means reference agreement, not “80% proven correct.”')
sub('GIBS: learn to predict those targets')
text('Frozen BERT turns text into features. A **two-layer Graph Convolutional Network (GCN)** and prediction layers learn a score for each agent step. The paper’s Equation 6 combines mask entropy with cross-entropy to the MCS targets.')
text('Only the small GCN/prediction layers are trained. **Qwen, BERT and DeBERTa are not fine-tuned.** After training, the GCN scores a query graph without MCS, successful references, gold actions or final reward at inference.')
sub('C4: our stricter target-generation variant')
bullet('Reject listed critical tool-field conflicts; require matching event kinds.')
bullet('Use symmetric truncation and allow multiple compatible matched components.')
bullet('Support a step only when **every incoming dependency edge** matches.')
story.append(note('C4 uses the same GCN but different targets. Current graphs do not automatically connect every prior conversation turn, and C4 teacher checks are not hard rules enforced by the predictor. C4 improvement still needs measurement.'))

page('3. Counts, training and evaluation')
story.append(table([
 ['Count','What it means'],
 ['1,000','All generated trajectories; all will receive held-out learned predictions.'],
 ['860','Queries eligible for MCS training/validation targets.'],
 ['911','Queries with enough references for the common NIBS comparison.'],
 ],[.7,3.7]))
sub('Why only 860 MCS targets?')
text('Our prototype requires **at least 3 other successful training references** for the same task, capped at 5. Seven tasks lack enough after validation is reserved: 7, 14, 20, 21, 29, 32 and 44. Therefore **1,000 − (7 × 20) = 860**. The excluded 140 remain in the dataset and still receive learned predictions.')
text('NIBS uses a larger successful evaluation-reference bank, so 911 queries qualify. The minimum-three rule and five-reference cap are our prototype choices. The paper does **not** require a 50:50 pass/fail ratio or a 3–17-pass task filter.')
sub('How training and testing stay separate')
text('Four held-out task-group folds contain **260, 260, 240 and 240** trajectories. A model scoring a task group does not fit or select checkpoints on that group. Training/validation MCS targets use training-partition references only.')
text('Train three seeds (7, 17, 27) for both GIBS and C4: **2 methods × 4 folds × 3 seeds = 24 checkpoints**. Use hidden size 128, dropout 0.1, Adam learning rate 0.001, and validation-loss early stopping.')
sub('How we judge the scores')
bullet('**AUROC:** do incorrect steps rank below correct steps?')
bullet('**Precision–recall / AP:** how well are rare errors retrieved?')
bullet('**First-error Top-1/Top-3:** does a low-score step identify the first labelled error?')
bullet('**ACC@80% and ECE:** selective accuracy and calibration; still need implementation.')
story.append(note('MCS targets supervise training; independent correctness labels evaluate usefulness. Current rule labels cover only some steps and share field assumptions with the matcher. Unverified steps are not assumed correct. Human/reference review remains necessary.'))

page('4. Results, progress and next steps')
text('**Snapshot: '+stamp+'.** The worker reports MCS target generation at **'+str(done)+' / '+str(total)+' ('+f'{100*done/total:.1f}'+'%)** for the two-method pipeline. Fresh GCN fitting and the learned comparison follow target completion. This PDF is not a live progress display.')
sub('Completed baseline results')
rows=[['Method','Tool AUROC','First-error Top-1']]
for key,label in [('paper_nibs_cos_max','Paper NIBS Max'),('paper_nibs_cos_mean','Paper NIBS Mean'),('tool_sim_nibs','tool_sim'),('random_expected','Random expectation'),('last_step_first','Last-step-first')]:
    a=summary['baselines'][key]['tool_calls']['aggregate']
    rows.append([label,f'{a["macro_auroc"]:.3f}',f'{100*a["localization"]["top1"]:.1f}%'])
story.append(table(rows,[1.6,1,1.25]))
story.append(Spacer(1,6))
text('These are automatic-label results on the reference-eligible population. AUROC covers **26 tasks** with both step-label classes; localization covers **173 failed runs** with labelled errors. A high AUROC is not the agent’s pass rate or proof of calibrated confidence.')
sub('What is done')
text('All 1,000 trajectories are collected and graph-compatible. NIBS baselines are complete. The dataset and completed baseline outputs are pushed to **1000Trajectories-Pardha**, commit **a283543**. Fresh GIBS/C4 outputs were not in that data-only push.')
sub('What to do next')
bullet('Let MCS finish; the monitor then retrieves targets and starts local GCN fitting/evaluation.')
bullet('Review successful-reference flags and independently label steps. Milestone 1 proposes reviewing 20–30 failed runs; this is still pending for the fresh collection.')
bullet('Complete the missing metrics; compare methods on identical eligible cases and report all-query coverage and N/A values.')
bullet('Review the expanded results with the stakeholder and prepare a demo showing a useful detection and a limitation. The fresh Phase 2 comparison is not complete yet.')
sub('Main files')
story.append(p('results/free_asu/main-qwen38-27b-serial-none/results.json\nresults/fresh_all_tasks/worker_state.json\nresults/fresh_all_tasks/baseline_preview/REPORT.md','code'))
story.append(p('Sources: supplied paper 2605.19228v2, §§4.2–4.4 and Appendices C.2/D.3; your Milestone 1; current code, frozen plan, baseline summary and worker state.','small'))

def decorate(c,doc):
    c.saveState();c.setFillColor(TEAL);c.rect(0,H-7,W,7,fill=1,stroke=0)
    c.setFont('GuideBold',9);c.setFillColor(INK);c.drawString(48,H-29,'STEPWISE CONFIDENCE  |  FOUR-PAGE PROJECT SUMMARY')
    c.setStrokeColor(colors.HexColor('#CCDDE1'));c.line(48,35,W-48,35)
    c.setFont('Guide',9);c.drawString(48,22,'CSE598 Team 11 • October 29, 2026');c.drawRightString(W-48,22,f'{doc.page} / 4')
    c.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=49,bottomMargin=47,
                      title='Stepwise Confidence: Four-Page Project Summary',author='CSE598 Team 11',pageCompression=1)
doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
print(OUT)
