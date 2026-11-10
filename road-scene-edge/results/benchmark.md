| Model | mAP50 | mAP50–95 | MiB | Median inference ms | p95 ms | Inference FPS | Pipeline FPS |
|---|---:|---:|---:|---:|---:|---:|---:|
| FP32 | 0.4262 | 0.2527 | 9.24 | 11.92 | 13.19 | 83.09 | 77.44 |
| INT8 | 0.4120 | 0.2508 | 2.78 | 32.63 | 36.43 | 31.06 | 30.26 |

INT8 mAP50–95 change: -0.0019
Median inference speedup: 0.37x

Pipeline timing includes preprocessing, inference and decoding; excludes video I/O and drawing.