# Road-scene detector: fresh laptop model

A newly trained YOLO26n detects vehicles, two-wheelers, pedestrians and potholes. The FP32 model is the default for this laptop.

## Results

Intel Core i5-8350U, Windows, ONNX Runtime CPU, two threads, batch 1, static input [1,3,416,416]. Timing uses 30 warmups and 200 iterations. Accuracy uses the exact same 94 test images as the earlier baseline (SHA-256 lists matched).

| Model | mAP50 | mAP50-95 | Size | Inference FPS | Pipeline FPS |
|---|---:|---:|---:|---:|---:|
| FP32 | 47.41% | 28.35% | 9.27 MiB | 26.47 | 23.59 |
| INT8 | 47.54% | 28.71% | 2.81 MiB | 12.11 | 11.51 |

INT8 is about 70% smaller but slower, so FP32 remains the default. Its small accuracy increase on this test set does not establish that quantization generally improves accuracy. Pipeline FPS includes preprocessing, inference and decoding, excluding video I/O, drawing and display. Full measurements and hashes: results/laptop_benchmark.json.

| Class AP50-95 | Earlier FP32 | New FP32 |
|---|---:|---:|
| Vehicle | 50.38% | 51.33% |
| Two-wheeler | 37.93% | 38.70% |
| Pedestrian | 1.29% | 7.95% |
| Pothole | 11.47% | 15.43% |

Overall mAP50 improved from 42.62% to 47.41% (+4.78 percentage points). Earlier speed results used a cloud CPU and 320-pixel inputs, so they are not directly comparable with these laptop speeds. Historical results remain in results/benchmark.json.

## Changes made

- Fresh 20-epoch training at 416 pixels, increased from 320.
- Pedestrian-containing training images repeated four times: 430 training entries, still only 352 unique images. Validation/test images are excluded from this sampling.
- Batch 2 and two CPU threads for the 8 GB laptop. Fixed YOLO initialization overriding the requested thread count.
- Fixed Windows output paths so training runs stay inside the project.
- Source-aware evaluation rejects unknown source names, and now accepts an explicit evaluation split.
- Exported static FP32 and signed QDQ INT8 models; calibrated using 200 unique training images only.
- Added regression checks, a Windows demo launcher, exact dependency versions and this report. Ten tests passed.

## Run

Python 3.11 was used. Install dependencies in a virtual environment:

```powershell
python -m pip install -r requirements-lock.txt
python roadscene.py demo --model models/roadscene_fp32.onnx --video demo/source.mp4 --output demo/latest.mp4 --seconds 20 --threads 2 --show
```

Press Q to close the display. Alternatively use run_demo.ps1 -Python PATH_TO_PYTHON -Video PATH_TO_VIDEO. The completed detection video is demo/bangalore_demo.mp4. Its overlay measures processing FPS and inference latency, not full camera-to-display throughput.

## Reproduce training

```powershell
python fetch_public_data.py --output public_data
python build_public_dataset.py --source public_data --output data/retrained --pedestrian-repeat 4
python partial_training.py --data data/retrained/data.yaml --weights yolo26n.pt --epochs 20 --size 416 --batch 2 --threads 2 --freeze 10 --name laptop_final
python roadscene.py export --weights runs/laptop_final/weights/last.pt --size 416 --output models/roadscene_fp32.onnx
python roadscene.py quantize --model models/roadscene_fp32.onnx --dataset data/retrained --samples 200 --output models/roadscene_int8.onnx
python roadscene.py benchmark --fp32 models/roadscene_fp32.onnx --int8 models/roadscene_int8.onnx --dataset data/retrained --source-aware --threads 2 --output results/laptop_benchmark.json
python -m pytest -q
```

Use the fixed final last.pt, not the checkpoint selected by upstream unmasked validation. The delivered copy is models/roadscene.pt. Training took about 74 minutes. Use fresh dataset/run directories when reproducing.

## Data and limitations

352 unique training, 103 validation and 94 test images. RDD2022 India supplies damage labels; Visaitech South Asian traffic supplies traffic labels. Neither has exhaustive four-class annotations. Training masks unknown classes. Reported accuracy evaluates only each source's annotated categories; cross-source false positives on unannotated classes are not measured.

Traffic splits use distinct video groups. RDD filename bands with gaps reduce adjacency, but true drive identities are unavailable, so drive independence is not established. Duplicate image bytes were checked. There are only 28 pedestrian training boxes, 2 validation boxes and 9 test boxes. Pedestrian and pothole accuracy remain weak despite improvement. Night, rain and heavy-traffic generalization were not validated. This is a demonstration model, not a driving safety system.

Mosaic, MixUp, CutMix and copy-paste remain disabled to preserve annotation masks. INT8 uses signed QDQ and per-channel weights; unsupported operators remain floating point.

## Reuse and sources

Reused and improved the existing road-scene assignment pipeline and its pretrained YOLO26n initializer. No previous trained four-class checkpoint was available or used. The older road-damage segmentation models were not used.

- RDD2022: https://github.com/sekilab/RoadDamageDetector
- Downloaded mirror, CC BY-SA 4.0: https://huggingface.co/datasets/dronefreak/RDD2022
- Traffic labels, CC BY 4.0: https://huggingface.co/datasets/visaitech/vehicle-mixed-traffic-detection
- Video: L. Shyamal, Bangalore C V Raman Road, CC0: https://commons.wikimedia.org/wiki/File:Bangalore_20220814_154815.webm
- Ultralytics licensing: https://www.ultralytics.com/license

The included source clip is a 20-second resized excerpt of the credited Bangalore video. Git LFS is needed to retrieve model and video binaries from GitHub.

Observed demo failure: at about 10 seconds the detector labels a roadside wall as a vehicle (approximately 0.57 confidence). The demo shows visible false positives; it is not evidence of reliable detection in all scenes.
