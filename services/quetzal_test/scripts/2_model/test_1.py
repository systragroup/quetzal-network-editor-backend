# %%
import sys
import json

default = {'scenario': 'base', 'training_folder': '../..'}  # Default execution parameters
manual, argv = (True, default) if 'ipykernel' in sys.argv[0] else (False, dict(default, **json.loads(sys.argv[1])))

# %%
from quetzal.model import stepmodel
import os

# from quetzal.io import excel
on_lambda = bool(os.environ.get('AWS_EXECUTION_ENV'))
num_cores = os.cpu_count()

# %%
print('on_lambda:', on_lambda)
print('num cores:', num_cores)

# %%
scenario = argv['scenario']
training_folder = argv['training_folder']

# if local. add the path to the scenario scenarios/<scenario>/
local_scen_path = '' if on_lambda else os.path.join('scenarios/', scenario)

input_folder = os.path.join(training_folder, 'inputs/')
scenario_folder = os.path.join(training_folder, local_scen_path, 'inputs/')
model_folder = os.path.join(training_folder, local_scen_path, 'model/')
output_folder = os.path.join(training_folder, local_scen_path, 'outputs/')

if not os.path.exists(output_folder):
	os.makedirs(output_folder)

# %%
if 'params' in argv.keys():
	print(argv['params'])

# %%
print('ok')

# %%
