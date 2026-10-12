"""Synthetic IW5GEO1 fixture and isolated iOS simulator render probe. No game data."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import time


def fixture():
    vertices=[(100,0,0),(-100,0,0),(0,100,0),(0,-100,0),(0,0,100),(0,0,-100)]
    indices=[4,0,2,4,2,1,4,1,3,4,3,0,5,2,0,5,1,2,5,3,1,5,0,3]
    data=bytearray(struct.pack('<8s6I',b'IW5GEO1\0',1,6,24,1,44,16))
    for i,xyz in enumerate(vertices):
        v=bytearray(44);struct.pack_into('<3f',v,0,*xyz)
        v[16:20]=bytes((60+i*25,200-i*20,100+i*20,255))
        v[36:40]=bytes((127,127,254,0));data.extend(v)
    data.extend(struct.pack('<24H',*indices))
    data.extend(struct.pack('<IIHHI',0,0,6,8,0))
    return bytes(data)


def valid_report(report):
    return isinstance(report,dict) and report.get('status')=='completed' and type(report.get('index_count')) is int and report['index_count']==24


def probe(app,output):
    output.mkdir(parents=True,exist_ok=True)
    record={'steps':[],'render_verified':False,'physical_device_verified':False}
    def save(): (output/'probe.json').write_text(json.dumps(record,indent=2)+'\n')
    def command(*args,check=True,timeout=90):
        try:
            p=subprocess.run(['xcrun','simctl',*map(str,args)],capture_output=True,text=True,timeout=timeout)
        except subprocess.TimeoutExpired:
            record['steps'].append({'args':list(map(str,args)),'timeout_seconds':timeout});save()
            if check:raise
            return ''
        record['steps'].append({'args':list(map(str,args)),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});save()
        if check and p.returncode: raise RuntimeError(p.stderr)
        return p.stdout.strip()
    inventory=json.loads(command('list','devices','available','--json'))
    choices=[(runtime,d) for runtime,ds in inventory['devices'].items() if '.iOS-' in runtime for d in ds if d.get('isAvailable') and d['name'].startswith('iPhone') and d.get('deviceTypeIdentifier')]
    if not choices: raise RuntimeError('No available iPhone simulator runtime')
    runtime,template=sorted(choices,key=lambda pair:pair[0])[-1]
    device=command('create','IW5 geometry smoke',template['deviceTypeIdentifier'],runtime)
    record.update(device=device,runtime=runtime)
    booted=False
    try:
        command('boot',device);booted=True
        command('bootstatus',device,'-b',timeout=240)
        command('install',device,app)
        container=Path(command('get_app_container',device,'org.kisakcod.iospreview','data'))
        report=container/'Documents/iw5-render-smoke.json'
        # The container belongs to this newly created simulator and app.
        if report.exists(): raise RuntimeError('Fresh simulator unexpectedly contains a stale render report')
        command('launch',device,'org.kisakcod.iospreview')
        deadline=time.monotonic()+90
        while time.monotonic()<deadline and not report.exists(): time.sleep(1)
        if not report.exists(): raise RuntimeError('No completed Metal draw report within 90 seconds')
        result=json.loads(report.read_text());record['render_report']=result;save()
        if not valid_report(result): raise RuntimeError('Metal command failed or wrong geometry was loaded')
        record['render_verified']=True;save()
        time.sleep(2)
    finally:
        try:
            if booted:
                command('io',device,'screenshot',output/'simulator.png',check=record['render_verified'])
                command('spawn',device,'log','show','--last','3m','--style','compact','--predicate','process == "KisakCOD-iOS"',check=False)
        finally:
            if booted:command('shutdown',device,check=False)
            command('delete',device,check=False)
            save()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixture',type=Path)
    p.add_argument('--app',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.fixture:
        a.fixture.parent.mkdir(parents=True,exist_ok=True);a.fixture.write_bytes(fixture())
    if a.app:
        if not a.output:p.error('--app requires --output')
        probe(a.app.resolve(),a.output.resolve())
    elif not a.fixture:p.error('specify --fixture or --app')


if __name__=='__main__':main()
