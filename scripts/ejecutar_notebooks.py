"""Ejecuta y guarda notebooks completos y vistas HTML de verificación."""
from pathlib import Path
import os
import sys
import json
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'qa/jupyter_runtime')
os.environ['IPYTHONDIR']=str(ROOT/'qa/ipython')
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
kernels=ROOT/'qa/kernels'
(kernels/'taller').mkdir(parents=True,exist_ok=True)
(ROOT/'qa/jupyter_runtime').mkdir(parents=True,exist_ok=True)
(kernels/'taller/kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
    'display_name':'Python (.venv taller)','language':'python'}),encoding='utf-8')
ksm=KernelSpecManager(kernel_dirs=[str(kernels)])
preview=ROOT/'qa/notebook_previews'; preview.mkdir(parents=True,exist_ok=True)
for path in sorted((ROOT/'notebooks').glob('*.ipynb')):
    print('Ejecutando',path.name,flush=True)
    nb=nbformat.read(path,as_version=4)
    km=KernelManager(kernel_name='taller',kernel_spec_manager=ksm)
    client=NotebookClient(nb,km=km,timeout=900,resources={'metadata':{'path':str(ROOT)}},allow_errors=False)
    client.execute()
    nbformat.validate(nb); nbformat.write(nb,path)
    html,_=HTMLExporter().from_notebook_node(nb)
    (preview/(path.stem+'.html')).write_text(html,encoding='utf-8')
    for i,cell in enumerate(nb.cells):
        for j,out in enumerate(cell.get('outputs',[])):
            if 'image/png' in out.get('data',{}):
                import base64
                (preview/f'{path.stem}_{i}_{j}.png').write_bytes(base64.b64decode(out.data['image/png']))
    print('Completado',path.name,flush=True)
