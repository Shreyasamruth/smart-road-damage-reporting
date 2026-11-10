"""Convert Pascal VOC boxes to initial YOLO labels; manually complete all four classes."""
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

MAP = {'car':0,'bus':0,'truck':0,'van':0,'autorickshaw':0,
       'motorcycle':1,'motorbike':1,'scooter':1,'bicycle':1,
       'person':2,'pedestrian':2,'D40':3,'pothole':3}


def convert(source, output):
    output = Path(output)
    if output.exists():
        raise ValueError('Choose a new output directory')
    files=sorted(Path(source).rglob('*.xml'))
    if not files:
        raise ValueError('No VOC XML found')
    skipped={}
    for path in files:
        root=ET.parse(path).getroot()
        width=float(root.findtext('size/width')); height=float(root.findtext('size/height'))
        if width <= 0 or height <= 0:
            raise ValueError(f'Invalid dimensions: {path}')
        lines=[]
        for obj in root.findall('object'):
            name=obj.findtext('name','').strip()
            if name not in MAP:
                skipped[name]=skipped.get(name,0)+1
                continue
            # VOC boxes are one-based inclusive; convert to zero-based continuous edges.
            x1=max(0,float(obj.findtext('bndbox/xmin'))-1)
            y1=max(0,float(obj.findtext('bndbox/ymin'))-1)
            x2=min(width,float(obj.findtext('bndbox/xmax')))
            y2=min(height,float(obj.findtext('bndbox/ymax')))
            if x2 <= x1 or y2 <= y1:
                raise ValueError(f'Invalid bounding box: {path}')
            lines.append(f'{MAP[name]} {(x1+x2)/2/width:.8f} {(y1+y2)/2/height:.8f} {(x2-x1)/width:.8f} {(y2-y1)/height:.8f}')
        target=output/path.relative_to(source).with_suffix('.txt')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text('\n'.join(lines),encoding='utf-8')
    print(f'Converted {len(files)} XML files. Unmapped classes: {skipped}')
    print('INITIAL LABELS ONLY: audit class mappings, rider policy and add missing traffic/pothole annotations.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--xml-dir',required=True); p.add_argument('--output',required=True)
    a=p.parse_args(); convert(a.xml_dir,a.output)
