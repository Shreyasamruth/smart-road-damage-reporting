"""Fetch a bounded, licensed public baseline dataset. No credentials required.
RDD India has damage-only labels; Visaitech has traffic-only labels.
This script preserves that distinction and does NOT assert full four-class annotation.
"""
import argparse
import hashlib
import json
import random
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SOURCES = {
 'rdd': 'https://huggingface.co/datasets/dronefreak/RDD2022',
 'traffic': 'https://huggingface.co/datasets/visaitech/vehicle-mixed-traffic-detection',
}


def fetch(url, dest):
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and (dest.stat().st_size or dest.suffix == '.txt'):
        return dest
    error=None
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'road-scene-assignment/1.0'})
            with urllib.request.urlopen(request,timeout=30) as r:
                data=r.read()
            if not data and dest.suffix != '.txt': raise ValueError('Empty response')
            dest.write_bytes(data)
            return dest
        except Exception as e:
            error=e
            time.sleep(attempt+1)
    raise RuntimeError(f'{url}: {error}')


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='public_data');p.add_argument('--workers',type=int,default=12)
    a=p.parse_args();root=Path(a.output)
    root.mkdir(parents=True,exist_ok=True)
    jobs=[];records=[]
    for split in ['train','val']:
        path=fetch(f'https://huggingface.co/api/datasets/visaitech/vehicle-mixed-traffic-detection/tree/main/images/{split}?limit=1000',root/f'traffic_{split}_index.json')
        for entry in json.loads(path.read_text()):
            if not entry['path'].endswith('.jpg'):continue
            image=entry['path'];label=image.replace('images/','labels/').rsplit('.',1)[0]+'.txt'
            for relative in [image,label]:
                jobs.append((SOURCES['traffic']+'/resolve/main/'+urllib.parse.quote(relative),root/'traffic'/relative))
            group=Path(image).name.split('__')[0]
            target='test' if split=='val' else ('val' if group=='V005' else 'train')
            records.append({'source':'traffic','original_image':image,'original_label':label,'split':target,'group':group,'annotated_classes':[0,1,2]})
    # The mirror metadata is COCO xywh in original image pixels, and class 3 is pothole.
    candidates=[]
    for shard in [1,2,3]:
        rel=f'data/images/train/shard_{shard:03}/metadata.jsonl'
        path=fetch(SOURCES['rdd']+'/resolve/main/'+rel,root/f'rdd_metadata_{shard:03}.jsonl')
        for line in path.read_text().splitlines():
            r=json.loads(line)
            if not r['file_name'].startswith('India_'):continue
            index=int(Path(r['file_name']).stem.split('_')[-1])
            # Separate filename-number bands, with gaps. True drive IDs unavailable.
            split='train' if index<5000 else ('val' if 6000<=index<7000 else ('test' if index>=8000 else None))
            if split:
                candidates.append({**r,'split':split,'shard':shard})
    rng=random.Random(42)
    for split,n in [('train',180),('val',36),('test',40)]:
        pool=[r for r in candidates if r['split']==split]
        pos=[r for r in pool if 3 in r['objects']['categories']]
        neg=[r for r in pool if 3 not in r['objects']['categories']]
        rng.shuffle(pos);rng.shuffle(neg)
        selected=pos[:int(n*.8)]+neg[:n-len(pos[:int(n*.8)])]
        for r in selected:
            relative=f"data/images/train/shard_{r['shard']:03}/{r['file_name']}"
            jobs.append((SOURCES['rdd']+'/resolve/main/'+relative,root/'rdd'/r['file_name']))
            records.append({'source':'rdd','original_image':r['file_name'],'split':split,
                'group':f"filename_band_{int(Path(r['file_name']).stem.split('_')[-1])//1000}",
                'annotated_classes':[3],'objects':r['objects']})
    jobs += [(SOURCES['traffic']+'/resolve/main/videos/clip_040.mp4',root/'clip_040.mp4'),
             (SOURCES['traffic']+'/raw/main/README.md',root/'TRAFFIC_SOURCE.md'),
             (SOURCES['rdd']+'/raw/main/README.md',root/'RDD_SOURCE.md')]
    failures=[]
    def work(pair):
        try: fetch(*pair);return None
        except Exception as e:return str(e)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for i,error in enumerate(ex.map(work,jobs)):
            if error:failures.append(error)
            if i%25==0:print(f'{i}/{len(jobs)} completed; failures={len(failures)}',flush=True)
    (root/'records.json').write_text(json.dumps(records,indent=2))
    (root/'download_failures.json').write_text(json.dumps(failures,indent=2))
    if failures:raise RuntimeError(f'{len(failures)} downloads failed; rerun to retry missing files')
    print('All downloads complete',flush=True)


if __name__=='__main__':main()
