import os
import yaml


def create_dir(dir):
    # input: str - directory
    # output: none
    try:
        os.makedirs(dir)
        print('created ' + dir)
    except FileExistsError:
        print(dir + ' exists.')
    except:
        print('error creating ' + dir)

    return None


class File_Structure:
    # input: str - filepath
    # input: str - file extension
    def update(self, subject):
        cwd = os.getcwd()

        self.subject = subject
        self.template = cwd + "/templates/" + subject + "/" + subject + "_template.gif"
        self.config = cwd + "/templates/" + subject + "/" + subject + ".yaml"
        if self.ext == '.txt':
            self.out_fp = self.orig_folder + "/" + subject + ".gif"
        if self.ext == '.gif' or self.ext == '.jpg':
            self.out_fp = self.orig_folder + "/" + subject + ".txt"

    # all relevant files saved as strings
    def __init__(self, orig_fp, ext):
        subject = 'temp'
        orig_folder = '/'.join(orig_fp.split("/")[:-1]) + '/'
        cwd = os.getcwd()
    
        self.dtg = '010000ZJAN2025'
        self.ext = ext
        self.cwd = cwd
        self.orig_fp = orig_fp
        self.orig_file = orig_fp.split('/')[-1][:-4]
        self.orig_folder = orig_folder
        self.templates_folder = cwd + "/templates/"
        self.msg_template = cwd + '/templates/Message Template.txt'
        if ext == '.txt':
            self.out_fp = orig_folder + "/" + subject + ".gif"
        if ext == '.gif' or ext == '.jpg':
            self.out_fp = orig_folder + "/" + subject + ".txt"

        self.subject = subject
        self.template = cwd + "/templates/" + subject + "/" + subject + "_template.gif"
        self.config = cwd + "/templates/" + subject + "/" + subject + ".yaml"

        create_dir(cwd + '/templates')


def config_update(fp,config,key,value):
    # input: fp class - name of the template being updated
    # input: dict     - current state of the config variable
    # input: string   - name of the kye to be updated
    # input: string   - value associated with the string
    # output: dict    - all of the configuration file as a dictionary
    # output: save the dict as a yaml
    out = config
    required_keys = ['name','scale','cr','b']

    create_dir(fp.templates_folder + '/' + fp.subject)

    if not os.path.exists(fp.config):
        for key in required_keys:
            if not key in out.keys():
                if key == 'name': out[key] = fp.subject
            else:
                out[key] = []
    
    out[key] = value

    try: 
        with open(fp.config,'w') as file: 
            yaml.safe_dump(out,file)
        print('Updated config file for ' + fp.subject)
    except:
        print('Could not update config file. Check logs.')

    return out


def config_get(fp):
    # input: fp class - name of the template
    # output: dict - configuration file as a dict
    out = {}

    create_dir(fp.templates_folder + '/' + fp.subject)

    if not os.path.exists(fp.config):
        print('Could not update config file. Check logs.')

    else:
        with open(fp.config, 'r') as file: 
            out = yaml.safe_load(file)

    return out