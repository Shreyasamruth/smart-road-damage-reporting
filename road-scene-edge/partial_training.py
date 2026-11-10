"""Train with source-aware class masking for partially annotated public datasets.
Pinned implementation: ultralytics 8.4.205. Mosaic/MixUp/CutMix must remain OFF.
"""
import argparse
from pathlib import Path
import torch
from torch import nn
from ultralytics import YOLO
from ultralytics.utils.loss import E2ELoss, v8DetectionLoss


def annotation_mask(paths, device=None):
    masks=[]
    for path in paths:
        name=Path(path).name
        if name.startswith('traffic_'):masks.append([1,1,1,0])
        elif name.startswith('rdd_'):masks.append([0,0,0,1])
        else:raise ValueError(f'Unknown annotation source: {name}')
    return torch.tensor(masks,device=device,dtype=torch.float32)[:,None,:]


class MaskedBCE(nn.Module):
    def __init__(self):
        super().__init__();self.mask=None
    def forward(self, logits, targets):
        if self.mask is None or self.mask.shape[0] != logits.shape[0]:
            raise ValueError('Missing/mismatched annotation mask')
        return nn.functional.binary_cross_entropy_with_logits(logits,targets,reduction='none') * self.mask.to(logits.device)


class PartialDetectionLoss(v8DetectionLoss):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.bce=MaskedBCE()
    def loss(self,preds,batch):
        self.bce.mask=annotation_mask(batch['im_file'],self.device)
        return super().loss(preds,batch)


def install_masked_loss(trainer):
    for key in ['mosaic','mixup','cutmix','copy_paste']:
        if getattr(trainer.args,key,0):raise ValueError(f'{key} must be disabled for source-aware loss')
    trainer.model.criterion=E2ELoss(trainer.model,PartialDetectionLoss)


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--weights',default='yolo26n.pt')
    p.add_argument('--epochs',type=int,default=20);p.add_argument('--size',type=int,default=320)
    p.add_argument('--batch',type=int,default=16);p.add_argument('--threads',type=int,default=4)
    p.add_argument('--freeze',type=int,default=10);p.add_argument('--name',default='public_baseline')
    a=p.parse_args()
    for key in ['epochs','size','batch','threads']:
        if getattr(a,key) <= 0:p.error(f'--{key} must be positive')
    if a.freeze < 0:p.error('--freeze must be nonnegative')
    torch.set_num_threads(a.threads)
    model=YOLO(a.weights);model.add_callback('on_pretrain_routine_end',install_masked_loss)
    # Device initialization resets PyTorch's thread count; enforce it after setup.
    model.add_callback('on_train_start',lambda trainer: torch.set_num_threads(a.threads))
    model.train(data=a.data,epochs=a.epochs,imgsz=a.size,batch=a.batch,device='cpu',workers=0,
        seed=42,deterministic=True,freeze=a.freeze,mosaic=0,mixup=0,cutmix=0,copy_paste=0,
        close_mosaic=0,project=str(Path('runs').resolve()),name=a.name,exist_ok=False,patience=0,
        optimizer='AdamW',lr0=.001,amp=False,plots=False,val=False,save=True)
    # Use fixed-budget last.pt, not best.pt chosen by the unmasked upstream validator.
    # Only source-aware external evaluation is authoritative for this partially labelled corpus.


if __name__=='__main__':main()
