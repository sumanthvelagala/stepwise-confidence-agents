"""No model calls: endpoint restrictions, no-provider environment and orchestration."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from collection.run_tau2 import clean_environment, command, local_url, summarize, task_definitions
from collection import asu
from collection.audit import audit


class CollectionTests(unittest.TestCase):
    def test_reward_success_with_missing_action_is_flagged_without_relabeling(self):
        result=audit({'tasks':[{'id':'13','evaluation_criteria':{'actions':[{'name':'transfer_to_human_agents'}]}}],
                      'simulations':[{'id':'example','task_id':'13','reward_info':{'reward':1},'messages':[]}]})
        self.assertEqual(result['totals']['success'],1)
        self.assertEqual(result['totals']['reward_success_missing_expected_tool_names'],1)
        self.assertEqual(result['runs'][0]['official_reward'],1)

    def test_graph_failures_are_reported_without_dropping_the_trajectory(self):
        sim={'id':'example','task_id':'0','reward_info':{'reward':0},'messages':[
            {'role':'assistant','tool_calls':[{'id':'a','name':'get_user_details','arguments':{}},
                                              {'id':'b','name':'get_user_details','arguments':{}}]}]}
        result=audit({'simulations':[sim]})
        self.assertEqual(result['totals']['failure'],1)
        self.assertEqual(result['totals']['unbuildable_graphs'],1)
        self.assertEqual(result['unique_runs'],1)
        self.assertFalse(result['runs'][0]['graph_compatible'])

    def test_asu_key_file_is_read_without_using_other_provider_keys(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path=Path(directory)/'.env.asu'
            path.write_text('ASU_API_KEY=\n')
            with self.assertRaises(ValueError):
                asu.load_key(path)
            path.write_text('# local secret\nASU_API_KEY="test-only"\n')
            self.assertEqual(asu.load_key(path),'test-only')

    def test_asu_catalog_requires_explicit_active_tool_model_and_enough_context(self):
        entry={'id':'example','model_type':'chat','supports_function_calling':True,'context_window':32768}
        self.assertIsNone(asu.model_identity([entry],'example',32768)['weight_digest'])
        for model, changes, context in [('auto',{},32768),('example',{'supports_function_calling':False},32768),
                                         ('example',{'status':'retired'},32768),('example',{},65536)]:
            with self.assertRaises(ValueError):
                asu.model_identity([{**entry,**changes}],model,context)

    def test_asu_command_has_no_key_and_cannot_use_paid_endpoint(self):
        a=argparse.Namespace(tau2_dir=Path('/tmp/tau2'), backend='asu',base_url=asu.BASE_URL,
                             context=32768,max_tokens=2048,model='example',trials=1,
                             concurrency=1,simulation_timeout=1200)
        cmd=command(a,['13'],Path('/tmp/collection'))
        args=json.loads(cmd[cmd.index('--agent-llm-args')+1])
        self.assertEqual(args['api_base'],asu.BASE_URL)
        self.assertEqual(args['extra_headers'],{'x-obleth-boons':'off'})
        self.assertIn('reasoning_effort',args['allowed_openai_params'])
        self.assertIn('parallel_tool_calls',args['allowed_openai_params'])
        self.assertIs(args['parallel_tool_calls'],False)
        self.assertNotIn('api_key',args)
        self.assertNotIn('num_ctx',args)
        a.base_url='https://api.openai.com/v1'
        with self.assertRaises(ValueError):
            command(a,['13'],Path('/tmp/collection'))

    def test_only_loopback_native_endpoint_is_accepted(self):
        self.assertEqual(local_url('http://127.0.0.1:11434/'), 'http://127.0.0.1:11434')
        for url in ['https://api.openai.com', 'http://localhost@remote.test', 'http://127.0.0.1/api',
                    'http://127.0.0.1?api_key=x', 'http://user:password@localhost:11434']:
            with self.assertRaises(ValueError):
                local_url(url)

    def test_provider_keys_removed_and_dotenv_disabled(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY':'fake', 'GROQ_API_KEY':'fake',
                                     'GPU_API_BASE':'https://remote.test', 'SCA_TEST_SETTING':'keep'}):
            env=clean_environment()
        self.assertNotIn('OPENAI_API_KEY',env)
        self.assertNotIn('GROQ_API_KEY',env)
        self.assertNotIn('GPU_API_BASE',env)
        self.assertEqual(env['PYTHON_DOTENV_DISABLED'],'1')
        self.assertEqual(env['SCA_TEST_SETTING'],'keep')

    def test_role_settings_and_resume_are_explicit(self):
        a=argparse.Namespace(tau2_dir=Path('/tmp/tau2'), base_url='http://127.0.0.1:12345',
                             context=32768,max_tokens=2048,model='qwen3:8b',trials=20,
                             concurrency=1,simulation_timeout=1200)
        cmd=command(a,['0','49'],Path('/tmp/collection'))
        agent=json.loads(cmd[cmd.index('--agent-llm-args')+1])
        user=json.loads(cmd[cmd.index('--user-llm-args')+1])
        self.assertEqual(agent['temperature'],1)
        self.assertEqual(user['temperature'],0)
        self.assertEqual(agent['reasoning_effort'],'none')
        self.assertIn('--auto-resume',cmd)
        self.assertNotIn('--auto-review',cmd)
        self.assertNotIn('--review-model',cmd)

    def test_infrastructure_errors_are_not_agent_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'results.json'
            path.write_text(json.dumps({'simulations':[{'task_id':'0','reward_info':{'reward':1}},
                                                     {'task_id':'0','reward_info':{'reward':0}},
                                                     {'task_id':'1','reward_info':None}]}))
            result=summarize(path)
        self.assertEqual(result['outcomes'],{'success':1,'failure':1,'infrastructure_error':1})

    def test_tasks_that_require_an_llm_judge_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            folder=root/'data/tau2/domains/airline'; folder.mkdir(parents=True)
            policy=b'test policy'
            (folder/'policy.md').write_bytes(policy)
            (folder/'tasks.json').write_text(json.dumps([{'id':'1','evaluation_criteria':{'reward_basis':['DB','NL_ASSERTION']}}]))
            with patch('collection.run_tau2.subprocess.check_output',return_value='5bfa7e37b36656b37dc6d022156be6563c1007f3'), \
                 patch('collection.run_tau2.POLICY_SHA',hashlib.sha256(policy).hexdigest()[:12]):
                with self.assertRaises(ValueError):
                    task_definitions(root,None)


if __name__=='__main__':
    unittest.main()
