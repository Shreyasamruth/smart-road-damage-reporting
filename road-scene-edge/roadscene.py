"""Four-class YOLO26n training and static ONNX CPU deployment."""
import argparse
import csv
import hashlib
import json
import platform
import random
import shutil
import time
from pathlib import Path

import numpy as np

NAMES = ['vehicle', 'two_wheeler', 'pedestrian', 'pothole']


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def letterbox(image, size):
    import cv2
    h, w = image.shape[:2]
    ratio = min(size / h, size / w)
    nw, nh = round(w * ratio), round(h * ratio)
    left, top = (size - nw) // 2, (size - nh) // 2
    resized = cv2.resize(image, (nw, nh))
    canvas = np.full((size, size, 3), 114, np.uint8)
    canvas[top:top + nh, left:left + nw] = resized
    tensor = np.ascontiguousarray(canvas[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255
    return tensor, (ratio, left, top)


def decode(output, transform, shape, threshold):
    """YOLO26 end-to-end output: batch x max_det x [xyxy, score, class]."""
    if output.ndim != 3 or output.shape[0] != 1 or output.shape[2] != 6:
        raise ValueError(f'Expected end-to-end [1,N,6], got {output.shape}')
    rows = output[0]
    rows = rows[np.isfinite(rows).all(1) & (rows[:, 4] >= threshold)].copy()
    if len(rows) == 0:
        return rows
    if not np.all((rows[:, 5] >= 0) & (rows[:, 5] < 4) & (rows[:, 5] == np.floor(rows[:, 5]))):
        raise ValueError('Wrong class IDs: use the trained four-class model')
    ratio, left, top = transform
    rows[:, [0, 2]] = np.clip((rows[:, [0, 2]] - left) / ratio, 0, shape[1])
    rows[:, [1, 3]] = np.clip((rows[:, [1, 3]] - top) / ratio, 0, shape[0])
    return rows[(rows[:, 2] > rows[:, 0]) & (rows[:, 3] > rows[:, 1])]


class Detector:
    def __init__(self, model, threads=4):
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(model), sess_options=options, providers=['CPUExecutionProvider'])
        inp = self.session.get_inputs()[0]
        shape = inp.shape
        if len(shape) != 4 or shape[:2] != [1, 3] or not isinstance(shape[2], int) or shape[2] != shape[3]:
            raise ValueError(f'Expected static [1,3,S,S], got {shape}')
        if inp.type != 'tensor(float)':
            raise ValueError('Expected float32 input, including QDQ INT8 graph')
        self.name, self.size = inp.name, shape[2]

    def run(self, image, threshold=.25):
        tensor, transform = letterbox(image, self.size)
        start = time.perf_counter()
        output = self.session.run(None, {self.name: tensor})[0]
        elapsed = time.perf_counter() - start
        return decode(output, transform, image.shape, threshold), elapsed


def labels(path):
    result = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        values = list(map(float, line.split()))
        if len(values) != 5:
            raise ValueError(f'{path}: expected detection labels, not segmentation polygons')
        c, x, y, w, h = values
        if c != int(c) or not 0 <= c < 4 or not all(np.isfinite(values)) or not 0 < w <= 1 or not 0 < h <= 1:
            raise ValueError(f'{path}: invalid label {line}')
        if x-w/2 < -1e-6 or y-h/2 < -1e-6 or x+w/2 > 1+1e-6 or y+h/2 > 1+1e-6:
            raise ValueError(f'{path}: box outside image')
        result.append(values)
    return result


def prepare(args):
    """Manifest split by source sequence, with annotation-completeness attestation."""
    import cv2
    import yaml
    source = Path(args.manifest).resolve()
    rows = list(csv.DictReader(source.open(encoding='utf-8')))
    required = {'image','label','group','split','source','fully_annotated'}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f'Manifest requires {sorted(required)}')
    target = Path(args.output).resolve()
    if target.exists():
        raise ValueError('Output exists; choose a new dataset directory to avoid stale data')
    groups, hashes, checked = {}, set(), []
    counts = {s: [0]*4 for s in ['train','val','test']}
    for row in rows:
        split, group = row['split'], row['group']
        if split not in counts or not group or row['fully_annotated'].lower() != 'true':
            raise ValueError('Require train/val/test, a sequence group, and complete four-class annotations')
        if group in groups and groups[group] != split:
            raise ValueError(f'Sequence leakage: {group}')
        groups[group] = split
        image, label = source.parent / row['image'], source.parent / row['label']
        sha = digest(image)
        if sha in hashes:
            raise ValueError(f'Duplicate image bytes: {image}')
        hashes.add(sha)
        if cv2.imread(str(image)) is None:
            raise ValueError(f'Unreadable image {image}')
        boxes = labels(label)
        for box in boxes:
            counts[split][int(box[0])] += 1
        checked.append((row, image, label, sha))
    if any(0 in count for count in counts.values()):
        raise ValueError(f'Each split must contain all four classes: {counts}')
    audit = []
    for i, (row, image, label, sha) in enumerate(checked):
        stem = f'{i:07d}'
        for folder, original, extension in [('images', image, image.suffix.lower()), ('labels', label, '.txt')]:
            out = target / folder / row['split'] / (stem + extension)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, out)
        audit.append({**row, 'sha256': sha, 'prepared_image': f'images/{row["split"]}/{stem}{image.suffix.lower()}'})
    (target / 'data.yaml').write_text(yaml.safe_dump({'path': str(target), 'train':'images/train', 'val':'images/val', 'test':'images/test', 'names':dict(enumerate(NAMES))}))
    write_json(target / 'audit.json', {'counts': counts, 'images': audit})
    print(target / 'data.yaml')


def train(args):
    from ultralytics import YOLO
    result = YOLO(args.weights).train(data=args.data, epochs=args.epochs, imgsz=args.size,
        batch=args.batch, device=args.device, seed=42, deterministic=True, workers=args.workers,
        project='runs', name='roadscene', exist_ok=False, patience=20, close_mosaic=10)
    print(result)


def export(args):
    from ultralytics import YOLO
    import onnx
    model = YOLO(args.weights)
    if list(model.names.values()) != NAMES:
        raise ValueError('Checkpoint must have exactly the four assignment classes in the documented order')
    exported = model.export(format='onnx', imgsz=args.size, batch=1, dynamic=False,
                            half=False, simplify=False, opset=17, end2end=True, device='cpu')
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    if Path(exported).resolve() != target.resolve():
        shutil.copy2(exported, target)
    onnx.checker.check_model(onnx.load(str(target)))
    detector = Detector(target)
    detector.run(np.zeros((args.size,args.size,3), np.uint8))
    write_json(str(target)+'.json', {'classes':NAMES, 'shape':[1,3,args.size,args.size], 'sha256':digest(target), 'checkpoint_sha256':digest(args.weights)})


def images(root, split):
    files = sorted(p for p in (Path(root)/'images'/split).glob('*') if p.suffix.lower() in {'.jpg','.jpeg','.png','.bmp'})
    if not files:
        raise ValueError(f'No {split} images in {root}')
    return files


def quantize(args):
    import cv2
    import onnx
    from onnxruntime.quantization import CalibrationDataReader, CalibrationMethod, QuantFormat, QuantType, quantize_static
    from onnxruntime.quantization.shape_inference import quant_pre_process
    model = Detector(args.model)
    files = images(args.dataset, 'train')
    random.Random(42).shuffle(files)
    files = files[:args.samples]
    if len(files) < 32:
        raise ValueError('At least 32 real training images required; recommend 200–500 representative images')
    class Reader(CalibrationDataReader):
        def __init__(self):
            self.iterator = iter(files)
        def get_next(self):
            path = next(self.iterator, None)
            if path is None:
                return None
            image = cv2.imread(str(path))
            if image is None:
                raise ValueError(f'Unreadable image {path}')
            return {model.name:letterbox(image, model.size)[0]}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pre = output.with_name(output.stem+'.preprocessed.onnx')
    quant_pre_process(args.model, str(pre), skip_symbolic_shape=True)
    quantize_static(str(pre), str(output), Reader(), quant_format=QuantFormat.QDQ,
                    activation_type=QuantType.QInt8, weight_type=QuantType.QInt8,
                    per_channel=True, calibrate_method=CalibrationMethod.MinMax,
                    op_types_to_quantize=['Conv','MatMul'])
    graph = onnx.load(str(output))
    onnx.checker.check_model(graph)
    qnodes = sum(n.op_type == 'QuantizeLinear' for n in graph.graph.node)
    if not qnodes:
        raise RuntimeError('No quantized operators found')
    Detector(output).run(cv2.imread(str(files[0])))
    write_json(str(output)+'.json', {'sha256':digest(output), 'fp32_sha256':digest(args.model),
        'format':'QDQ signed INT8, per-channel weights; unsupported operators stay floating point',
        'quantize_nodes':qnodes, 'calibration':[{'path':str(p), 'sha256':digest(p)} for p in files]})
    pre.unlink()


def accuracy(detector, files, root):
    import cv2
    from pycocotools.coco import COCO
    from pycocotools.cocoeval import COCOeval
    annotations, predictions, metadata = [], [], []
    for i, path in enumerate(files):
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f'Unreadable image {path}')
        h,w = image.shape[:2]
        metadata.append({'id':i, 'width':w, 'height':h})
        for c,x,y,bw,bh in labels(Path(root)/'labels/test'/f'{path.stem}.txt'):
            box = [(x-bw/2)*w,(y-bh/2)*h,bw*w,bh*h]
            annotations.append({'id':len(annotations)+1,'image_id':i,'category_id':int(c), 'bbox':box,'area':box[2]*box[3],'iscrowd':0})
        detections, _ = detector.run(image, .001)
        for x1,y1,x2,y2,score,cls in detections:
            predictions.append({'image_id':i,'category_id':int(cls),'bbox':[float(x1),float(y1),float(x2-x1),float(y2-y1)],'score':float(score)})
    gt = COCO()
    gt.dataset = {'images':metadata,'annotations':annotations,'categories':[{'id':i,'name':n} for i,n in enumerate(NAMES)],'info':{}}
    gt.createIndex()
    if not predictions:
        return {'mAP50_95':0.0,'mAP50':0.0,'per_class_mAP50_95':dict.fromkeys(NAMES,0.0)}
    evaluation = COCOeval(gt, gt.loadRes(predictions), 'bbox')
    evaluation.evaluate(); evaluation.accumulate(); evaluation.summarize()
    per_class = {}
    for i,name in enumerate(NAMES):
        precision = evaluation.eval['precision'][:,:,i,0,-1]
        valid = precision[precision >= 0]
        per_class[name] = float(valid.mean()) if valid.size else None
    return {'mAP50_95':float(evaluation.stats[0]),'mAP50':float(evaluation.stats[1]),'per_class_mAP50_95':per_class}


def benchmark(args):
    import cv2
    import importlib.metadata
    files = images(args.dataset, 'test')
    samples = [cv2.imread(str(p)) for p in files[:min(32,len(files))]]
    if any(x is None for x in samples):
        raise ValueError('Unreadable benchmark image')
    result = {'hardware':{'platform':platform.platform(),'processor':platform.processor(), 'machine':platform.machine(), 'cpu_threads':args.threads},
              'versions':{n:importlib.metadata.version(n) for n in ['numpy','onnxruntime','pycocotools']},
              'test_images':len(files),'test_sha256':[digest(p) for p in files],
              'protocol':{'warmup':args.warmup,'iterations':args.iterations,'provider':'CPUExecutionProvider','batch':1,'accuracy_confidence':.001,'COCO_max_detections':100}, 'models':{}}
    sizes = []
    for name,path in [('FP32',args.fp32),('INT8',args.int8)]:
        detector = Detector(path,args.threads)
        sizes.append(detector.size)
        if len(set(sizes)) != 1:
            raise ValueError('Models have different input sizes')
        for i in range(args.warmup):
            detector.run(samples[i % len(samples)])
        inference, pipeline = [], []
        for i in range(args.iterations):
            start = time.perf_counter()
            _, seconds = detector.run(samples[i % len(samples)])
            pipeline.append((time.perf_counter()-start)*1000)
            inference.append(seconds*1000)
        result['models'][name] = {'path':path,'sha256':digest(path),'size_MiB':Path(path).stat().st_size/2**20,
            'input':[1,3,detector.size,detector.size], 'inference_median_ms':float(np.median(inference)),
            'inference_p95_ms':float(np.percentile(inference,95)), 'inference_FPS':1000/float(np.mean(inference)),
            'pipeline_mean_ms':float(np.mean(pipeline)),'pipeline_FPS':1000/float(np.mean(pipeline)),
            'accuracy':accuracy(detector,files,args.dataset)}
    write_json(args.output,result)
    fp, qi = result['models']['FP32'],result['models']['INT8']
    lines = ['| Model | mAP50 | mAP50–95 | MiB | Median inference ms | p95 ms | Inference FPS | Pipeline FPS |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,r in result['models'].items():
        lines.append(f"| {name} | {r['accuracy']['mAP50']:.4f} | {r['accuracy']['mAP50_95']:.4f} | {r['size_MiB']:.2f} | {r['inference_median_ms']:.2f} | {r['inference_p95_ms']:.2f} | {r['inference_FPS']:.2f} | {r['pipeline_FPS']:.2f} |")
    lines += ['', f"INT8 mAP50–95 change: {qi['accuracy']['mAP50_95']-fp['accuracy']['mAP50_95']:+.4f}", f"Median inference speedup: {fp['inference_median_ms']/qi['inference_median_ms']:.2f}x", '', 'Pipeline timing includes preprocessing, inference and decoding; excludes video I/O and drawing.']
    Path(args.output).with_suffix('.md').write_text('\n'.join(lines),encoding='utf-8')


def demo(args):
    import cv2
    detector = Detector(args.model,args.threads)
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise ValueError(f'Cannot open {args.video}')
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        fps = 25
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    writer, frames, smoothed = None, 0, None
    try:
        while True:
            ok,frame = cap.read()
            if not ok:
                break
            start = time.perf_counter()
            detections, seconds = detector.run(frame,args.conf)
            for x1,y1,x2,y2,score,cls in detections:
                x1,y1,x2,y2 = map(int,(x1,y1,x2,y2))
                color = [(0,200,0),(255,180,0),(0,220,255),(0,0,255)][int(cls)]
                cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
                cv2.putText(frame,f'{NAMES[int(cls)]} {score:.2f}',(x1,max(20,y1-6)),cv2.FONT_HERSHEY_SIMPLEX,.5,color,2)
            elapsed = time.perf_counter()-start
            smoothed = elapsed if smoothed is None else .9*smoothed+.1*elapsed
            cv2.putText(frame,f'Processing {1/smoothed:.1f} FPS | inference {seconds*1000:.1f} ms',(12,30),cv2.FONT_HERSHEY_SIMPLEX,.65,(255,255,255),2)
            if writer is None:
                writer = cv2.VideoWriter(args.output,cv2.VideoWriter_fourcc(*'mp4v'),fps,(frame.shape[1],frame.shape[0]))
                if not writer.isOpened():
                    raise RuntimeError('Video encoder unavailable')
            writer.write(frame)
            frames += 1
            if args.show:
                cv2.imshow('Road scene',frame)
                if cv2.waitKey(1) & 255 == ord('q'):
                    break
            if args.seconds and frames >= round(args.seconds*fps):
                break
    finally:
        cap.release()
        if writer:
            writer.release()
        if args.show:
            cv2.destroyAllWindows()
    if frames == 0:
        raise ValueError('No decoded video frames')
    write_json(str(args.output)+'.json',{'frames':frames,'source_fps':fps,'model_sha256':digest(args.model),'confidence':args.conf,'overlay':'EMA processing FPS; excludes read/write/display and text overlay'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    p = sub.add_parser('prepare'); p.add_argument('--manifest',required=True); p.add_argument('--output',default='data/roadscene'); p.set_defaults(func=prepare)
    p = sub.add_parser('train'); p.add_argument('--data',required=True); p.add_argument('--weights',default='yolo26n.pt'); p.add_argument('--epochs',type=int,default=80); p.add_argument('--size',type=int,default=640); p.add_argument('--batch',type=int,default=8); p.add_argument('--device',default='cpu'); p.add_argument('--workers',type=int,default=0); p.set_defaults(func=train)
    p = sub.add_parser('export'); p.add_argument('--weights',required=True); p.add_argument('--size',type=int,default=640); p.add_argument('--output',default='models/roadscene_fp32.onnx'); p.set_defaults(func=export)
    p = sub.add_parser('quantize'); p.add_argument('--model',required=True); p.add_argument('--dataset',required=True); p.add_argument('--samples',type=int,default=300); p.add_argument('--output',default='models/roadscene_int8.onnx'); p.set_defaults(func=quantize)
    p = sub.add_parser('benchmark'); p.add_argument('--fp32',required=True); p.add_argument('--int8',required=True); p.add_argument('--dataset',required=True); p.add_argument('--threads',type=int,default=4); p.add_argument('--warmup',type=int,default=30); p.add_argument('--iterations',type=int,default=200); p.add_argument('--output',default='results/benchmark.json'); p.set_defaults(func=benchmark)
    p = sub.add_parser('demo'); p.add_argument('--model',required=True); p.add_argument('--video',required=True); p.add_argument('--output',default='demo/demo.mp4'); p.add_argument('--threads',type=int,default=4); p.add_argument('--conf',type=float,default=.25); p.add_argument('--seconds',type=float,default=30); p.add_argument('--show',action='store_true'); p.set_defaults(func=demo)
    args = parser.parse_args()
    for key in ['threads','iterations','warmup','samples','epochs','size','batch']:
        if hasattr(args,key) and getattr(args,key) <= 0:
            parser.error(f'--{key} must be positive')
    args.func(args)


if __name__ == '__main__':
    main()
