| Model | mAP50 | mAP50–95 | MiB | Median inference ms | p95 ms | Inference FPS | Pipeline FPS |
|---|---:|---:|---:|---:|---:|---:|---:|
| FP32 | 0.4741 | 0.2835 | 9.27 | 35.98 | 48.10 | 26.47 | 23.59 |
| INT8 | 0.4754 | 0.2871 | 2.81 | 80.56 | 110.90 | 12.11 | 11.51 |

INT8 mAP50–95 change: +0.0036
Median inference speedup: 0.45x

Pipeline timing includes preprocessing, inference and decoding; excludes video I/O and drawing.