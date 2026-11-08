"""Prepare source-aware train/validation/test data without claiming exhaustive annotations."""
import argparse,json,hashlib,shutil
from pathlib import Path
from collections import Counter
import cv2,yaml


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();src=Path(a.source);out=Path(a.output).resolve()
    if out.exists():raise ValueError('Output already exists')
    records=json.loads((src/'records.json').read_text());audit=[];hashes={};counts={s:Counter() for s in ['train','val','test']}
    for i,r in enumerate(records):
        path=src/('traffic' if r['source']=='traffic' else 'rdd')/r['original_image']
        data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
        if sha in hashes:raise ValueError(f'Duplicate image bytes: {path}, {hashes[sha]}')
        hashes[sha]=str(path)
        image=cv2.imread(str(path));h,w=image.shape[:2]
        boxes=[]
        if r['source']=='traffic':
            mapping={0:2,1:1,2:0,3:0}
            for line in (src/'traffic'/r['original_label']).read_text().splitlines():
                c,x,y,bw,bh=map(float,line.split());boxes.append([mapping[int(c)],x,y,bw,bh])
        else:
            for box,c in zip(r['objects']['bbox'],r['objects']['categories']):
                if c==3:
                    x,y,bw,bh=box
                    x1=max(0,x);y1=max(0,y);x2=min(w,x+bw);y2=min(h,y+bh)
                    if x2>x1 and y2>y1:boxes.append([3,(x1+x2)/2/w,(y1+y2)/2/h,(x2-x1)/w,(y2-y1)/h])
        stem=f"{r['source']}_{i:05}"
        for kind in ['images','labels']:(out/kind/r['split']).mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,out/'images'/r['split']/(stem+'.jpg'))
        (out/'labels'/r['split']/(stem+'.txt')).write_text('\n'.join(' '.join(map(str,b)) for b in boxes))
        counts[r['split']].update(int(b[0]) for b in boxes)
        audit.append({**r,'prepared_image':f"images/{r['split']}/{stem}.jpg",'sha256':sha,'label_sha256':hashlib.sha256((out/'labels'/r['split']/(stem+'.txt')).read_bytes()).hexdigest()})
    config={'path':str(out),'train':'images/train','val':'images/val','test':'images/test','names':{0:'vehicle',1:'two_wheeler',2:'pedestrian',3:'pothole'}}
    (out/'data.yaml').write_text(yaml.safe_dump(config))
    (out/'audit.json').write_text(json.dumps({'annotation_policy':'partial; use class-masked loss and source-aware evaluation','counts':{s:dict(c) for s,c in counts.items()},'images':audit},indent=2))
    print(json.dumps({'images':dict(Counter(r['split'] for r in records)),'boxes':{s:dict(c) for s,c in counts.items()}},indent=2))


if __name__=='__main__':main()
