"""Verify both source experiments, case claims and offline/HTTP browser behavior."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
import hashlib,json,math,statistics,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from demo_ui.build_comparison import read_run,evidence
from gibs.fresh.reference_comparison import verify_baseline
DIST=ROOT/'dist'
EXPERIMENTS={'cap5':'fresh_all_tasks','cap17':'fresh_refs_3_17'}
D={cap:json.loads((DIST/f'data/{cap}/dashboard.json').read_text()) for cap in EXPERIMENTS}
C=json.loads((DIST/'data/comparison.json').read_text())

def check_data():
    output={}
    for cap,source_name in EXPERIMENTS.items():
        d=D[cap];index={r['id']:r for r in d['runs']};source=ROOT.parent/'results'/source_name
        assert len(index)==1000 and len(d['tasks'])==50
        assert sum(r['nibs_available'] for r in index.values())==911
        assert sum(r['teacher_available'] for r in index.values())==860 and len(d['histories'])==24
        assert hashlib.sha256((source/'summary.json').read_bytes()).hexdigest()==d['meta']['summary_sha256']
        assert json.loads((source/'summary.json').read_text())==d['summary']
        predictions={m:{seed:json.loads((source/f'query_only_predictions/{m}_seed{seed}.json').read_text())['scores'] for seed in ['7','17','27']} for m in ['paper_gibs_pdf','c4_gibs']}
        total_steps=pairs=0
        for sid,item in index.items():
            run=read_run(cap,sid);steps=run['steps'];assert len(steps)==item['steps']
            assert [s['index'] for s in steps]==list(range(len(steps)));total_steps+=len(steps)
            for step in steps:
                for method in predictions:
                    assert set(step['scores'][method])=={'7','17','27'}
                    for seed,v in step['scores'][method].items():
                        assert math.isfinite(v) and 0<=v<=1
                        assert v==predictions[method][seed][sid][step['index']]
            for method,t in run['teachers'].items():
                assert 3<=len(t['references'])<=d['meta']['teacher_max_references']
                actual=json.loads((source/f'teachers/{method}/{sid}.json').read_text())
                assert t['events']==actual['events']==[s['event'] for s in steps]
                assert t['mask']==actual['mask'] and [r['id'] for r in t['references']]==actual['references']
                for ref in t['references']:
                    ri=index[ref['id']];assert ri['success'] and ri['task']==item['task'] and ref['id']!=sid
                    original=json.loads((source/f'pairs/{method}/{sid}_{ref["id"]}.json').read_text())
                    for key in ['mask','node_map','edge_map']:assert original[key]==ref[key]
                    pairs+=1
                for i,event in enumerate(t['events']):
                    assert abs(statistics.mean(ref['mask'][event] for ref in t['references'])-t['mask'][i])<1e-7
        assert total_steps==14145 and pairs=={'cap5':8456,'cap17':20102}[cap]
        output[cap]={'runs':1000,'tasks':50,'steps':total_steps,'genuine_pair_mappings_checked':pairs,'saved_prediction_and_teacher_identity':'pass','target_averaging':'pass'}
    assert len(C['examples'])==5 and len({e['run_id'] for e in C['examples']})==5
    for e in C['examples']:
        for cap in EXPERIMENTS:
            run=read_run(cap,e['run_id']);assert not run['run']['success'] and run['teachers']
            assert evidence(run)==e[cap]
    examples={e['id']:e for e in C['examples']}
    top=lambda key,cap,method:examples[key][cap]['methods'][method]['top1']
    assert top('gibs_success','cap17','paper_gibs_pdf')==1 and top('gibs_success','cap17','paper_nibs_cos_mean')==0
    assert top('nibs_beats_gibs','cap17','paper_nibs_cos_mean')==1 and top('nibs_beats_gibs','cap17','paper_gibs_pdf')==0
    assert top('more_refs_help','cap5','paper_gibs_pdf')==0 and top('more_refs_help','cap17','paper_gibs_pdf')==1
    assert top('c4_regresses','cap5','c4_gibs')==1 and top('c4_regresses','cap17','c4_gibs')==0
    assert all(top('gibs_failure',cap,'paper_gibs_pdf')==0 for cap in EXPERIMENTS)
    assert examples['gibs_failure']['cap17']['targets']['paper_gibs_pdf']['error_target']>=.8
    trial=ROOT.parent/'results/fresh_refs_3_17'
    verify_baseline(ROOT.parent/'results/fresh_all_tasks',json.loads((trial/'baseline_protection.json').read_text()))
    output.update(examples='Five genuine ranking claims verified',original_baseline_protection='pass')
    return output

def check_browser():
    screenshots=ROOT/'qa';screenshots.mkdir(exist_ok=True);errors=[]
    examples={e['id']:e for e in C['examples']}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror',lambda error:errors.append(str(error)))
        requests=[];page.on('request',lambda request:requests.append(request.url))
        page.goto((DIST/'index.html').as_uri());page.wait_for_selector('[data-comparison-method]')
        assert page.locator('[data-example]').count()==5
        text=page.locator('[data-comparison-method="paper_gibs_pdf"]').inner_text()
        assert all(v in text for v in ['0.700','0.723','+6.6 pp'])
        page.locator('#comparison-scope').select_option('all_agent_steps')
        assert '0.746' in page.locator('[data-comparison-method="paper_gibs_pdf"]').inner_text()
        page.locator('#comparison-scope').select_option('tool_calls')
        page.screenshot(path=str(screenshots/'comparison.png'),full_page=True)
        page.get_by_role('link',name='Results overview').click();page.wait_for_selector('.bar-row')
        assert '0.723' in page.locator('.bar-row').filter(has_text='Paper GIBS').inner_text()
        page.locator('#experiment').select_option('cap5')
        page.wait_for_function("document.querySelector('#source-stamp').textContent.startsWith('3–5')")
        assert '0.700' in page.locator('.bar-row').filter(has_text='Paper GIBS').inner_text()
        page.get_by_role('button',name='First-error Top-1',exact=True).click()
        assert '71.7%' in page.locator('.bar-row').filter(has_text='NIBS Mean').inner_text()
        page.locator('#experiment').select_option('cap17')
        page.wait_for_function("document.querySelector('#source-stamp').textContent.startsWith('3–17')")
        assert '72.3%' in page.locator('.bar-row').filter(has_text='NIBS Mean').inner_text()
        page.locator('#population').select_option('all')
        assert 'N/A' in page.locator('.bar-row').filter(has_text='NIBS Max').inner_text()
        page.locator('#population').select_option('common');page.get_by_role('button',name='AUROC',exact=True).click()
        page.locator('#seed').select_option('7')
        assert '0.730' in page.locator('.bar-row').filter(has_text='Paper GIBS').inner_text()
        page.locator('#seed').select_option('mean');page.locator('#label-only').check()
        assert page.locator('[data-task]').count()==26
        page.locator('#label-only').uncheck();assert page.locator('[data-task]').count()==50
        page.screenshot(path=str(screenshots/'overview-cap17.png'),full_page=True)
        for e in C['examples']:
            page.get_by_role('link',name='3–5 vs 3–17').click();page.wait_for_selector('[data-example]')
            page.locator(f'[data-example="{e["id"]}"]').click();page.wait_for_selector('.step-detail')
            assert e['title'] in page.locator('.example-note').inner_text()
            assert f'Step {e["cap17"]["error_step"]+1}' in page.locator('.step-detail h3').inner_text()
            assert 'First labelled tool error' in page.locator('.step-detail').inner_text()
            for method in ['paper_gibs_pdf','c4_gibs','paper_nibs_cos_mean']:
                text=page.locator(f'[data-step-method="{method}"]').inner_text()
                assert all(f'{e[cap]["methods"][method]["error_score"]:.3f}' in text for cap in EXPERIMENTS)
        page.locator('[data-case="more_refs_help"]').click();page.wait_for_selector('.step-detail')
        e=examples['more_refs_help'];data=read_run('cap17',e['run_id'])
        page.screenshot(path=str(screenshots/'example-scores.png'),full_page=True)
        page.get_by_role('button',name='Trajectory graph',exact=True).click();page.wait_for_selector('.graph-wrap svg')
        assert page.locator('.graph-wrap .graph-node').count()==len(data['graph']['nodes'])
        page.get_by_role('button',name='MCS & targets',exact=True).click();page.wait_for_selector('#teacher-ref')
        assert page.locator('#teacher-ref option').count()==10 and page.locator('.graph-wrap svg').count()==2
        assert '0 / 10' in page.locator('.target-comparison').inner_text()
        page.locator('#teacher-ref').select_option('9');page.wait_for_selector('.target-comparison')
        page.locator('#experiment').select_option('cap5')
        page.wait_for_function("document.querySelector('#teacher-ref')?.options.length===5")
        assert page.locator('#teacher-ref').input_value()=='0'
        assert page.locator('.target-tile').count()==len(data['steps'])
        page.locator('#experiment').select_option('cap17')
        page.wait_for_function("document.querySelector('#teacher-ref')?.options.length===10")
        page.locator('#teacher-method').select_option('c4_gibs');page.wait_for_selector('#teacher-ref')
        page.screenshot(path=str(screenshots/'mcs-cap-comparison.png'),full_page=True)
        page.locator('[data-case="gibs_failure"]').click();page.wait_for_selector('.step-detail')
        page.get_by_role('button',name='MCS & targets',exact=True).click();page.wait_for_selector('#teacher-ref')
        assert '10 / 10' in page.locator('.target-comparison').inner_text()
        page.locator('#teacher-method').select_option('c4_gibs')
        page.wait_for_function("document.querySelector('.target-comparison')?.textContent.includes('0 / 10')")
        page.locator('#run-task').select_option('7')
        page.wait_for_function("document.querySelector('#run-tab')?.textContent.includes('no MCS training target')")
        page.get_by_role('link',name='Why these results?').click();page.wait_for_selector('#history-chart svg')
        assert page.locator('.explain-card').count()==4
        page.locator('#experiment').select_option('cap5')
        page.wait_for_function("document.querySelector('#source-stamp').textContent.startsWith('3–5')")
        key='fold3_c4_gibs_seed27';page.locator('#history-key').select_option(key)
        assert f'{D["cap5"]["histories"][key]["epochs"]} epochs' in page.locator('#history-chart').inner_text()
        page.get_by_role('link',name='Method walkthrough').click();page.wait_for_selector('.toy-match')
        assert '[1.0, 0.8, 0.2]' in page.locator('#toy-vector').inner_text()
        page.locator('.toy-match[data-row="0"]').first.uncheck()
        assert '[0.8, 0.8, 0.2]' in page.locator('#toy-vector').inner_text()
        assert page.locator('#full-gibs-walkthrough h3').count()==15
        page.get_by_role('link',name='Results overview').click();page.wait_for_selector('.bar-row')
        assert page.locator('.toy-match').count()==0
        assert all(url.startswith('file:') for url in requests),'Offline demo made an external request'
        mobile=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        mobile.on('pageerror',lambda error:errors.append(str(error)))
        mobile.goto((DIST/'index.html').as_uri());mobile.wait_for_selector('[data-comparison-method]')
        assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),'Comparison overflows mobile'
        mobile.screenshot(path=str(screenshots/'mobile-comparison.png'),full_page=True)
        mobile.locator('[data-example="gibs_success"]').click();mobile.wait_for_selector('.step-detail')
        assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),'Explorer overflows mobile'
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(DIST)))
        worker=Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_selector('[data-comparison-method]')
            page.locator('[data-example="nibs_beats_gibs"]').click();page.wait_for_selector('.step-detail')
            assert 'NIBS catches what GIBS misses' in page.locator('.example-note').inner_text()
        finally:server.shutdown();server.server_close();worker.join()
        browser.close()
    assert not errors,errors
    return {'offline_mode':'pass','http_mode':'pass','desktop_and_mobile':'pass','both_experiments_and_five_examples':'pass','javascript_errors':errors,'screenshots':str(screenshots)}

if __name__=='__main__':
    report={'data':check_data(),'browser':check_browser()}
    (ROOT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
