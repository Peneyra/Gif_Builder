import yaml
from pathlib import Path

def upd_con(template_name,config,key,value):
    # input: string - name of the template being updated
    # input: dict - current state of the config variable
    # input: string - name of the kye to be updated
    # input: string - value associated with the string
    # output: save the dict as a yaml
    # output: dict - all of the configuration file as a dictionary
    out = config
    file_path = Path('./templates/' + template_name + '/' + template_name + '.yaml')
    if not Path(file_path).exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        out['name'] = template_name
        out['scale'] = []
        out['crop_l'] = 0
        out['crop_r'] = 0
        out['crop_t'] = 0
        out['crop_b'] = 0
        out['scale_loc_vert'] = 0
        out['scale_loc_horz'] = 0
    out[key] = value
    with open(file_path,'w') as file: yaml.safe_dump(out,file)
    return out
def get_con(template_name):
    # input: string - name of the template
    # output: dict - configuration file as a dict
    out = {}
    file_path = './templates/' + template_name + '/' + template_name + '.yaml'
    if Path(file_path).exists():
        with open(file_path, 'r') as file: out = yaml.safe_load(file)
    else: print('no configuration file found here:' + file_path)
    return out