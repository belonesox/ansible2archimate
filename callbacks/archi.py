import datetime
import os
import time
import cPickle as pickle
import ansible.executor.task_result

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    A plugin for timing tasks
    """
    def __init__(self):
        super(CallbackModule, self).__init__()
        self.stats = {}
        self.current = None
        self.state = {}
        self.run_db_name = 'archimate.pickle'
        self.load_state()

        self.package_modules = set(['yum', 'apt'])
        self.file_modules = set(['template', 'file'])
        pass


    def load_state(self):
        '''
        Load state from pickle file
        '''
        self.state = {}
        if os.path.exists(self.run_db_name):
            try:
                #pylint: disable=E1101
                self.state = pickle.load(open(self.run_db_name, 'r'))
            except EOFError:
                pass
        self.save_state()    
        pass

    def save_state(self):
        '''
        Load state in a pickle file
        '''
        #pylint: disable=E1101
        pickle.Pickler(open(self.run_db_name, "w")).dump(self.state)
        pass


    def on_any(self, *args, **kwargs):
        if not isinstance(args, tuple):
            return

        if not len(args) == 2:
            return

        if not len(args[0]) == 1:
            return

        if not isinstance(args[0][0], ansible.executor.task_result.TaskResult):
            return

        if '_result' not in dir(args[0][0]):
            return

        if '_host' not in dir(args[0][0]):
            return


        res = args[0][0]._result
        host = unicode(args[0][0]._host)

        if not host in self.state:
            self.state[host] = {}

        if 'invocation' not in res:
            return

        inv = res['invocation']
        if not 'module_args' in inv:
            return


        module = 'template'
        if 'module_name' in inv:
            module = inv['module_name']

        if not module in (self.package_modules | self.file_modules):
            return

        module_type = 'misc'

        if module in self.package_modules:
            value = set(inv['module_args']['name'])
            module_type = 'packages'

        if module in self.file_modules:
            value = set([inv['module_args']['path']])
            module_type = 'files'

        if module_type not in self.state[host]:
            self.state[host][module_type] = set()

        self.state[host][module_type] |= value
        pass


    # def runner_on_ok(self, host, res):
    #     if host not in self.state:
    #         self.state[host] = {}
    #
    #     if 'invocation' in res:
    #         pass
    #     pass


    def playbook_on_stats(self, stats):
        self.save_state()
        for host in self.state:
            for module in self.state[host]:
                for value in self.state[host][module]:
                    print host, module, value
        pass


