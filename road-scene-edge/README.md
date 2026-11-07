# Indian road-scene edge detection — implementation, experiments pending

**Status: NOT a completed trained-model submission.** Code is implemented and six local tests pass (including a synthetic ONNX/video smoke test). No Indian training data or dashcam clip was supplied to this workspace. No trained four-class weights, real FP32/INT8 exports, laptop measurements, or real detection demo have been produced. Synthetic test fixtures are not submission models or demo evidence.

## Architecture and classes

Fine-tune **Ultralytics YOLO26n**, the released nano detector verified against official documentation on 7 November 2026. Export its end-to-end head to static **[1, 3, 640, 640]** FP32 ONNX. Quantize Conv/MatMul to signed INT8 with ONNX Runtime QDQ and per-channel weights, calibrating only with training images. Some operators remain floating point. Both variants use the same RGB/255 letterbox preprocessing and end-to-end decoder; no additional NMS is applied.

| ID | Class | Annotation policy |
|---|---|---|
| 0 | vehicle | Cars, buses, trucks, vans and autorickshaws; exclude two-wheelers |
| 1 | two_wheeler | Motorcycles, scooters and bicycles, including ridden ones |
| 2 | pedestrian | People on foot; exclude riders already associated with two-wheelers |
| 3 | pothole | Visible road depressions; RDD D40; exclude D00/D10/D20 cracks |

## Reuse disclosure

The existing repository README identifies a YOLOv8 pothole **segmentation** workflow and a React/FastAPI reporting application. This assignment reuses the project topic and repository only. **No old code, weights, dataset, or evaluation numbers have been copied.** All files in this directory are new. Segmentation polygon labels and checkpoints cannot be used as this four-class detection model without explicit conversion/retraining.

## 1. Install (Windows PowerShell)

Use Python 3.11 or 3.12. Open a terminal in this directory.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests -q
```

For NVIDIA training, install the appropriate CUDA-enabled PyTorch build using the official PyTorch installation selector before installing the requirements. CPU training works but can take much longer. Dependencies use compatibility ranges because a complete training environment was not validated here. Record the actual working environment with `python -m pip freeze > results/environment.txt` after creating `results`.

## 2. Obtain and annotate Indian footage

- IDD Detection: https://insaan.iiit.ac.in/ — obtain the detection dataset under its access and usage terms.
- RDD2022: https://github.com/sekilab/RoadDamageDetector — use the India portion and its training annotations; D40 denotes potholes.
- Alternatively record Indian dashcam video you have permission to use and annotate extracted frames.

**Do not naively concatenate IDD and RDD annotations.** RDD damage annotations do not label all traffic objects, and IDD traffic annotations may not include potholes. For a single four-class model, review every selected image and add missing target boxes. Otherwise visible but unlabelled targets become false background during training and evaluation. Keep source annotations separately. Manually verify auto-assisted labels.

Export complete annotations in YOLO detection format: each row is `class_id x_center y_center width height`, normalized to [0,1]. Empty files are allowed only for verified negatives. Use the table above consistently for all sources. `convert_voc.py` offers initial conversion for Pascal VOC XML; its output is explicitly NOT a completeness audit.

Split by **whole drive/sequence/location**, approximately 70% train / 15% validation / 15% test. Keep adjacent frames, repeated routes, and near-duplicates together. The code rejects identical image bytes and cross-split sequence IDs, but manual/visual checks are still needed for near-duplicates. All four classes must occur in each split. Choose the checkpoint using validation only; reserve test for final comparison.

Create `manifest.csv` with paths relative to the CSV:

```csv
image,label,group,split,source,fully_annotated
raw/images/drive01_001.jpg,raw/labels/drive01_001.txt,drive01,train,IDD,true
raw/images/drive02_001.jpg,raw/labels/drive02_001.txt,drive02,val,IDD,true
raw/images/drive03_001.jpg,raw/labels/drive03_001.txt,drive03,test,RDD2022_India,true
```

These are illustrative filenames, not included data. `fully_annotated=true` is your review attestation, not something the script can infer.

```powershell
python roadscene.py prepare --manifest manifest.csv --output data/roadscene
```

The preparation command validates labels, sequence isolation, duplicate bytes, class coverage and readable images; it creates a YAML and provenance audit. It refuses to overwrite an existing dataset.

## 3. Train

```powershell
python roadscene.py train --data data/roadscene/data.yaml --epochs 80 --size 640 --batch 8 --device 0
```

Without an NVIDIA GPU use `--device cpu --batch 4`. The initial pretrained checkpoint is downloaded by Ultralytics; it is NOT already a pothole detector. Training uses seed 42, validation-based checkpoint selection and early stopping. Ultralytics may create `runs/roadscene2`, etc., for repeated runs; use the `best.pt` path printed by your run in subsequent commands.

## 4. Static FP32 export and real-data INT8 calibration

```powershell
python roadscene.py export --weights runs/roadscene/weights/best.pt --output models/roadscene_fp32.onnx
python roadscene.py quantize --model models/roadscene_fp32.onnx --dataset data/roadscene --samples 300 --output models/roadscene_int8.onnx
```

Export checks class names, graph validity, static dimensions and output layout. Calibration selects up to 300 training images deterministically (minimum 32). Use a training set representative of road conditions; inspect the recorded calibration manifest for condition coverage. Never calibrate on validation or test. Quantization checks that QDQ nodes exist and performs a runtime smoke test. Export metadata records file hashes. These operations have not yet been exercised on a real YOLO26 checkpoint here.

## 5. Measure on the actual laptop

Plug into power, select a fixed power mode, close other heavy applications, and record laptop model/CPU/RAM/OS. Run both models on the same CPU provider and thread count:

```powershell
python roadscene.py benchmark --fp32 models/roadscene_fp32.onnx --int8 models/roadscene_int8.onnx --dataset data/roadscene --threads 4 --warmup 30 --iterations 200
```

The command generates `results/benchmark.json` and `results/benchmark.md`. It records model/test-image hashes, installed package versions, platform, input dimensions and protocol. Add the exact laptop model, RAM and power mode manually. Repeat on a thermally stable laptop and retain individual results if checking variability.

Accuracy uses COCO mAP50 and mAP50–95 (100 detections/image), with a common 0.001 score cutoff and per-class mAP. Detection labels must be exhaustive. Speed uses preloaded real test frames, warm-up, median/p95 inference latency, and FPS from mean latency. Pipeline FPS includes preprocessing and decoding, but excludes video I/O, drawing and display. Results are CPU measurements, not claimed embedded-device performance. INT8 speedup is not guaranteed; small models, QDQ overhead and CPU instruction support can make INT8 slower.

### Results — not yet measured

| Model | Test mAP50 | Test mAP50–95 | Median latency | p95 latency | FPS | Size |
|---|---|---|---|---|---|---|
| FP32 ONNX | Pending | Pending | Pending | Pending | Pending | Pending |
| INT8 QDQ ONNX | Pending | Pending | Pending | Pending | Pending | Pending |

Replace this table with generated measurements; discuss class-level accuracy changes, model size and actual speedup. Do not copy Ultralytics COCO numbers as assignment results.

## 6. Record a short video

Use an unseen Indian road clip, with no overlap with training/calibration drives:

```powershell
python roadscene.py demo --model models/roadscene_int8.onnx --video input/dashcam.mp4 --output demo/roadscene_int8.mp4 --seconds 30 --show
```

Omit `--show` on a headless machine. The output keeps the original playback frame rate. Overlay shows smoothed processing FPS (preprocess, inference, decode, box drawing; excludes input/output/display and overlay text) plus inference milliseconds, not the source-video FPS. Its JSON sidecar records the model hash and confidence threshold. Review the rendered video for false positives and missed detections.

## Failure analysis — hypotheses awaiting real evaluation

| Condition | Risk to investigate | Evidence to collect |
|---|---|---|
| Night/glare | Low contrast and headlight saturation | Timestamped missed pedestrians/potholes |
| Rain/wet roads | Reflections and puddles resemble potholes | FP32 vs INT8 false positives at same timestamps |
| Heavy traffic | Occluded people and two-wheelers | Class recall and crowded-scene examples |
| Distant/small targets | 640px resizing loses detail | Small-object misses and distance context |
| Shadows/patches | Dark texture mistaken for potholes | Label-reviewed false positives |
| Camera changes | Different mounting, vibration, blur | Separate unseen-camera clip |

These are expected risks, **not observed results**. Fill `docs/failure_log.csv` after testing and describe what was actually seen. This demo is not a safety-critical driving system.

## Deliverable checklist

- [x] Training, export, quantization, benchmark and video scripts
- [x] Dataset validation, provenance and reuse disclosure
- [x] Six local tests (geometry, decoder contract, labels, leakage, ONNX/video plumbing, perfect/empty COCO metrics)
- [ ] Reviewed Indian dataset and held-out sequences
- [ ] Trained `best.pt` and training logs
- [ ] Real `roadscene_fp32.onnx` and `roadscene_int8.onnx`, metadata/hashes
- [ ] Laptop accuracy/speed comparison and environment capture
- [ ] Real short demo clip and observed failure log

Store trained artifacts under `models/` and the demo under `demo/`. Git LFS patterns are provided; install Git LFS before committing binary artifacts, or use a GitHub Release and add exact download links and SHA256 hashes. Do not upload dataset images without redistribution permission. Review Ultralytics' AGPL-3.0 / enterprise licensing and source-dataset terms for any use beyond the assignment.

## Walkthrough preparation

Explain the four-class mapping and missing-label problem; demonstrate sequence-separated splits; show how static shapes and calibration work; distinguish inference latency from pipeline/video FPS; show measured FP32/INT8 tradeoffs; finish with actual failure clips. Be explicit about new code versus the previous segmentation project.

## References

- YOLO26 and nano model: https://docs.ultralytics.com/models/yolo26/
- ONNX export: https://docs.ultralytics.com/integrations/onnx/
- ONNX Runtime quantization: https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html
- IDD: https://insaan.iiit.ac.in/
- RDD2022: https://github.com/sekilab/RoadDamageDetector
