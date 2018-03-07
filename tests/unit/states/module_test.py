# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Nicole Thomas (nicole@saltstack.com)`
'''

# Import Python Libs
from __future__ import absolute_import
from inspect import ArgSpec

# Import Salt Libs
from salt.states import module

# Import Salt Testing Libs
from salttesting import skipIf, TestCase
from salttesting.helpers import ensure_in_syspath
from salttesting.mock import (
    NO_MOCK,
    NO_MOCK_REASON,
    MagicMock,
    patch
)

ensure_in_syspath('../../')

CMD = 'foo.bar'
MOCK = MagicMock()
module.__salt__ = {CMD: MOCK}
module.__opts__ = {'test': False}

STATE_APPLY_RET = {
    'module_|-test2_|-state.apply_|-run': {
        'comment': 'Module function state.apply executed',
        'name': 'state.apply',
        'start_time': '16:11:48.818932',
        'result': False,
        'duration': 179.439,
        '__run_num__': 0,
        'changes': {
            'ret': {
                'module_|-test3_|-state.apply_|-run': {
                    'comment': 'Module function state.apply executed',
                    'name': 'state.apply',
                    'start_time': '16:11:48.904796',
                    'result': True,
                    'duration': 89.522,
                    '__run_num__': 0,
                    'changes': {
                        'ret': {
                            'module_|-test4_|-cmd.run_|-run': {
                                'comment': 'Module function cmd.run executed',
                                'name': 'cmd.run',
                                'start_time': '16:11:48.988574',
                                'result': True,
                                'duration': 4.543,
                                '__run_num__': 0,
                                'changes': {
                                    'ret': 'Wed Mar  7 16:11:48 CET 2018'
                                },
                                '__id__': 'test4'
                            }
                        }
                    },
                    '__id__': 'test3'
                },
                'module_|-test3_fail_|-test3_fail_|-run': {
                    'comment': 'Module function test3_fail is not available',
                    'name': 'test3_fail',
                    'start_time': '16:11:48.994607',
                    'result': False,
                    'duration': 0.466,
                    '__run_num__': 1,
                    'changes': {},
                    '__id__': 'test3_fail'
                }
            }
        },
        '__id__': 'test2'
    }
}


@skipIf(NO_MOCK, NO_MOCK_REASON)
class ModuleStateTest(TestCase):
    '''
    Tests module state (salt/states/module.py)
    '''

    aspec = ArgSpec(args=['hello', 'world'],
                    varargs=None,
                    keywords=None,
                    defaults=False)
    bspec = ArgSpec(args=[],
                    varargs='names',
                    keywords='kwargs',
                    defaults=None)

    def test_module_run_module_not_available(self):
        '''
        Tests the return of module.run state when the module function
        name isn't available
        '''
        with patch.dict(module.__salt__, {}):
            cmd = 'hello.world'
            ret = module.run(cmd)
            comment = 'Module function {0} is not available'.format(cmd)
            self.assertEqual(ret['comment'], comment)
            self.assertFalse(ret['result'])

    def test_module_run_test_true(self):
        '''
        Tests the return of module.run state when test=True is passed in
        '''
        with patch.dict(module.__opts__, {'test': True}):
            ret = module.run(CMD)
            comment = 'Module function {0} is set to execute'.format(CMD)
            self.assertEqual(ret['comment'], comment)

    def test_run_state_apply_result_false(self):
        '''
        Tests the 'result' of module.run that calls state.apply execution module
        :return:
        '''
        with patch.dict(module.__salt__, {"state.apply": MagicMock(return_value=STATE_APPLY_RET)}):
            ret = module.run(**{"name": "state.apply", 'mods': 'test2'})
            if ret['result']:
                self.fail('module.run did not report false result: {0}'.format(ret))

    @patch('salt.utils.args.get_function_argspec', MagicMock(return_value=aspec))
    def test_module_run_missing_arg(self):
        '''
        Tests the return of module.run state when arguments are missing
        '''
        ret = module.run(CMD)
        comment = 'The following arguments are missing: world hello'
        self.assertEqual(ret['comment'], comment)

    @patch('salt.utils.args.get_function_argspec', MagicMock(return_value=bspec))
    def test_module_run_hidden_varargs(self):
        '''
        Tests the return of module.run state when hidden varargs are used with
        wrong type.
        '''
        ret = module.run(CMD, m_names = 'anyname')
        comment = "'names' must be a list."
        self.assertEqual(ret['comment'], comment)


if __name__ == '__main__':
    from integration import run_tests
    run_tests(ModuleStateTest, needs_daemon=False)
