#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
import os
import time
import cPickle as pickle
import re
import yaml
from lxml import etree

# IMPORT_FOLDER_NAME = "DeployFromAnsible"
PARENT_IMPORT_FOLDER_NAME = "Technology & Physical"
IMPORT_FOLDER_NAME = "DeployFromAnsible"

class Archimator(object):
    """
    Archimator
    """
    def __init__(self):
        self.archi_namespaces = {
            'archimate': "http://www.archimatetool.com/archimate",
            'xsi':       "http://www.w3.org/2001/XMLSchema-instance"
        }    
        self.stats = {}
        self.current = None
        self.state = {}
        self.run_db_name = 'archimate.pickle'
        self.load_state()

        self.package_modules = set(['yum', 'apt'])
        self.file_modules = set(['template', 'file'])
    
        self.settings = None

        proto_settings = None        

        import pkg_resources
        proto_yml_str = pkg_resources.resource_string('ansible2archimate', 'template/archimator.yml')
        proto_yml = yaml.load(proto_yml_str)
        
        with open("archimator.yml", 'r') as stream:
            self.settings = yaml.load(stream)
            
        self.settings.update(proto_yml)    

        self.softs = set()
        self.path2soft = {}
        
        for soft_type in ['system-soft', 'application-soft']:
            for soft in self.settings[soft_type]:
                soft_id = soft + '-' + soft_type
                if not soft_id in self.softs:
                    self.softs.add(soft_id)
                    regexps = set(self.settings[soft_type][soft])
                    regexps |= set([soft])
                    for regexp in regexps:
                        re_ = re.compile(regexp)
                        self.path2soft[re_] = soft_id

        self.ignore = {}
        for soft_type in self.settings['ignore']:
            if soft_type not in self.ignore:
                self.ignore[soft_type] = []

            for path in self.settings['ignore'][soft_type]:
                re_ = re.compile(path)
                self.ignore[soft_type].append(re_)


        self.softwares  = {}
        self.host2soft  = {}
        
        for host in self.state:
            if host not in self.host2soft:
                self.host2soft[host] = set()

            for resource_type in self.state[host]:
                for name in self.state[host][resource_type]:
                    name = name.replace(r'//', r'/')
                    if name.startswith(r'htop'):
                        pass
                    ignored = False
                    if resource_type  in self.ignore:
                        for re_ in self.ignore[resource_type]:
                            if re_.match(name):
                                ignored = True
                                break
                            
                    if not ignored:
                        software = name.replace(r'/', '-') + '-undefined'
                        for re_, soft in self.path2soft.items():
                            if re_.match(name):
                                software = soft
    
                        if software not in self.softwares:
                            self.softwares[software] = name
    
                        if software not in self.host2soft[host]:
                            self.host2soft[host].add(software)
                            
                        if software.endswith('-undefined'):
                            print software
                            for re_, soft in self.path2soft.items():
                                print re_.pattern
                                if re_.pattern.startswith('/home/tms/www'):
                                    pass
                                if re_.match(name):
                                    software = soft

            pass

        yaml.dump(self.host2soft, sys.stdout, default_flow_style=False)
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
        # self.save_state()    
        pass

    # def save_state(self):
    #     '''
    #     Load state in a pickle file
    #     '''
    #     #pylint: disable=E1101
    #     pickle.Pickler(open(self.run_db_name, "w")).dump(self.state)
    #     pass

    def process(self, archimater):
        # Open original file
        et = etree.parse(archimater)
        et.write(archimater+'.xml', encoding="utf-8", xml_declaration=True, method="xml")

        parent_ansible_folder = None
        for parent_ansible_folder  in et.getroot().iterfind('./folder[@name="%s"]' % PARENT_IMPORT_FOLDER_NAME): 
            break
    
        ansible_folder = None
        for ansible_folder in parent_ansible_folder.iterfind('./folder[@name="%s"]' % IMPORT_FOLDER_NAME): 
            break
        
        if ansible_folder is None:
            import_folder_name = IMPORT_FOLDER_NAME
            xmlstr = '<folder name="%(import_folder_name)s" id="deploy-from-ansible" type="technology"/>' % vars()
            ansible_folder = etree.fromstring(xmlstr)
            parent_ansible_folder.append(ansible_folder)

        ansible_relation_folder = None
        for ansible_relation_folder in ansible_folder.iterfind('./folder[@name="Relations"]'): #[@name="Technology2"]
            break

        if ansible_relation_folder is None:
            xmlstr = '<folder name="Relations" id="deploy-from-ansible-relations" type="technology"/>' % vars()
            ansible_relation_folder = etree.fromstring(xmlstr)
            ansible_folder.append(ansible_relation_folder)


        for soft in self.softwares:
            name = soft
            xpath_ = "./element[@id='%s']" % soft
            element = None
            for element in ansible_folder.iterfind(xpath_):
                break
            if element is None:
                xsi_type = "archimate:Artifact"
                if soft.endswith('application-soft'):
                    xsi_type = "archimate:ApplicationComponent"
                    name = soft[:-len('application-soft')-1]
                if soft.endswith('system-soft'):
                    xsi_type = "archimate:SystemSoftware"
                    name = soft[:-len('system-soft')-1]
                xmlstr = '''<?xml version="1.0"?>
<element id="%(soft)s" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="%(name)s" xsi:type="%(xsi_type)s" />
''' % vars()
                element = etree.fromstring(xmlstr)
                ansible_folder.append(element)

        for host in self.host2soft:
            name = host 
            xpath_ = "./element[@id='%s']" % soft
            element = None
            for element in ansible_folder.iterfind(xpath_):
                break
            if len(element) == 0:
                xsi_type = "archimate:Node"
                host_id = host + "-ansible-host"
                xmlstr = '''<?xml version="1.0"?>
<element id="%(host_id)s" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="%(name)s" xsi:type="%(xsi_type)s" />
''' % vars()
                element = etree.fromstring(xmlstr)
                ansible_folder.append(element)

            for soft in self.host2soft[host]:
                xpath_ = '/archimate:model/folder[@name="DeployFromAnsible"]/folder[@name="Relations"]/element[(@source="%(host_id)s") and (@target="%(soft)s")]' % vars()
                # xpath_ = './element[@source="%(host_id)s" and @target="%(soft)s"]' % vars()
                res = et.xpath(xpath_, namespaces=self.archi_namespaces)
                if not res:
                    xsi_type = "archimate:AssignmentRelationship"
                    host_id = host + "-ansible-host"
                    relid = host + "---" + soft + "-ansible-relation"
                    xmlstr = '''<?xml version="1.0"?>
    <element id="%(relid)s" source="%(host_id)s" target="%(soft)s" xsi:type="%(xsi_type)s" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" />
    ''' % vars()
                    element = etree.fromstring(xmlstr)
                    ansible_relation_folder.append(element)

        et.write(archimater, encoding="utf-8", xml_declaration=True, method="xml")

        pass


    
def ansible2archimate():
    archimate_model = None
    if len(sys.argv) > 1:
        print "You have to specify destination model and project directory"
        archimate_model = sys.argv[1]

    ansible_dir = None    
    if len(sys.argv) > 2:
        ansible_dir = sys.argv[2]
        
    if ansible_dir:
        os.chdir(ansible_dir)

        

    AM = Archimator()
# ='/home/stas/Dropbox/archi/test.archimate'        
    AM.process(archimate_model)

# project_dir, model_filename


if __name__ == '__main__':
    ansible2archimate()        

