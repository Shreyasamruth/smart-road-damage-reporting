# Indian road-scene edge detection — trained public-data baseline

Trained YOLO26n for 20 epochs at 320 pixels on 352 images; 103 validation and 94 held-out test images. Uses RDD2022 India (damage annotations) and Visaitech South Asian traffic frames (traffic annotations). Source-aware classification masks prevent treating unlabelled classes as background. Evaluation scores only annotated classes in each source; this is not exhaustive four-class ground truth. RDD split uses separated filename bands, not verified drive identities.

Measured on a cloud CPU with four ONNX Runtime threads, not the user laptop:

| Model | mAP50 | mAP50–95 | MiB | Median inference ms | p95 ms | Inference FPS | Pipeline FPS |
|---|---:|---:|---:|---:|---:|---:|---:|
| FP32 | 0.4262 | 0.2527 | 9.24 | 11.92 | 13.19 | 83.09 | 77.44 |
| INT8 | 0.4120 | 0.2508 | 2.78 | 32.63 | 36.43 | 31.06 | 30.26 |

INT8 mAP50–95 change: -0.0019
Median inference speedup: 0.37x

Pipeline timing includes preprocessing, inference and decoding; excludes video I/O and drawing.

INT8 is smaller but slower on this CPU. Pedestrian AP50–95 is only 0.013 and pothole AP is about 0.115: this is a limited baseline, not a reliable road-safety model. Night/rain performance has not been tested.

Reproduce the executed run with `fetch_public_data.py`, `build_public_dataset.py`, and `partial_training.py` (20 epochs, 320px, fixed last checkpoint). Generic fully annotated workflow below is retained for future improved training. Source-aware benchmark requires `--source-aware`.

Demo source: L. Shyamal, Bangalore C V Raman Road, CC0: https://commons.wikimedia.org/wiki/File:Bangalore_20220814_154815.webm

## Reproduction

```bash
pip install -r requirements.txt
python fetch_public_data.py --output public_data
python build_public_dataset.py --source public_data --output data/public
python partial_training.py --data data/public/data.yaml --epochs 20 --size 320
```

Use the printed run directory's `weights/last.pt`. Export with `roadscene.py export --weights PATH --size 320`; calibrate with `roadscene.py quantize --model models/roadscene_fp32.onnx --dataset data/public --samples 128`; benchmark with `roadscene.py benchmark --fp32 models/roadscene_fp32.onnx --int8 models/roadscene_int8.onnx --dataset data/public --source-aware`.

Class order: vehicle, two_wheeler, pedestrian, pothole. Traffic annotations merge 3- and 4-wheelers into vehicle. Model input is static [1,3,320,320]. INT8 uses signed QDQ with per-channel weights; unsupported operators remain floating point. Calibration uses only training images. Timing excludes video I/O and drawing.

## Reuse and sources

No code or weights from the earlier road-damage project were copied. The repository and project topic are reused. New code implements acquisition, source-aware training, ONNX deployment, evaluation and video rendering. Pretrained YOLO26n initializes training.

- RDD2022 authors: https://github.com/sekilab/RoadDamageDetector
- Downloaded YOLO-format mirror (CC BY-SA 4.0): https://huggingface.co/datasets/dronefreak/RDD2022
- Visaitech traffic annotations (CC BY 4.0): https://huggingface.co/datasets/visaitech/vehicle-mixed-traffic-detection
- Ultralytics licensing: https://www.ultralytics.com/license

Traffic train/validation/test groups are separated by source video. RDD true drive IDs are unavailable; filename bands with gaps reduce adjacency but do not establish independent drives. No identical image bytes were present. Neither dataset is exhaustively labelled for all four classes; unannotated classes are masked from classification loss and excluded from source-aware scoring. Mosaic, MixUp and CutMix are disabled to preserve per-image annotation masks. The fixed 20th-epoch checkpoint is used; upstream unmasked validation results are not the reported benchmark.

## Limitations and status

Small, daytime-heavy baseline. Only 28 pedestrian training boxes and 9 test boxes. Pedestrians and small potholes perform poorly. Night, rain and heavy-traffic generalization require further evaluation. The demo is a visual demonstration, not a quantified video benchmark. This model is not appropriate for safety-critical driving.

Eight local tests passed, plus a real YOLO26 masked-loss forward/backward check. Models and demo were generated locally; their GitHub upload is still pending. Laptop measurements are also pending. Code and measured JSON/Markdown results are published in this branch.
