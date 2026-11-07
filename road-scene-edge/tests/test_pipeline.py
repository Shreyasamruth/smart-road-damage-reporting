from pathlib import Path
from types import SimpleNamespace
import csv
import cv2
import numpy as np
import pytest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from roadscene import letterbox, decode, labels, prepare, Detector, demo


def test_letterbox_roundtrip():
    image = np.zeros((360,640,3),np.uint8)
    image[:,:,2] = 255
    tensor, transform = letterbox(image,640)
    assert tensor.shape == (1,3,640,640)
    assert tensor[0,0,200,200] == 1
    output = np.array([[[20,150,100,230,.9,3]]],np.float32)
    result = decode(output,transform,image.shape,.25)
    np.testing.assert_allclose(result[0,:4],[20,10,100,90])


def test_reject_wrong_decoder():
    with pytest.raises(ValueError):
        decode(np.zeros((1,8,8400)),(1,0,0),(640,640,3),.25)
    with pytest.raises(ValueError):
        decode(np.array([[[0,0,30,30,.9,7]]]),(1,0,0),(640,640,3),.25)


def test_labels_reject_segmentation_and_bad_boxes(tmp_path):
    p = tmp_path/'label.txt'
    for line in ['3 0 0 1 1','0 .5 .5 0 1','0 .1 .1 .2 .2 .3 .3']:
        p.write_text(line)
        with pytest.raises(ValueError):
            labels(p)


def manifest(tmp_path, leak=False):
    rows=[]
    for i,split in enumerate(['train','val','test']):
        cv2.imwrite(str(tmp_path/f'{i}.png'),np.full((32,32,3),i*30,np.uint8))
        (tmp_path/f'{i}.txt').write_text('\n'.join(f'{c} .5 .5 .2 .2' for c in range(4)))
        rows.append({'image':f'{i}.png','label':f'{i}.txt','group':'same' if leak else str(i),'split':split,'source':'synthetic-test-only','fully_annotated':'true'})
    p = tmp_path/'manifest.csv'
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    return p


def test_prepare_and_leakage(tmp_path):
    p=manifest(tmp_path,True)
    args=SimpleNamespace(manifest=p,output=tmp_path/'dataset')
    with pytest.raises(ValueError,match='leakage'):
        prepare(args)
    manifest(tmp_path)
    prepare(args)
    assert (tmp_path/'dataset/data.yaml').is_file()
    assert len(list((tmp_path/'dataset/labels/test').glob('*.txt'))) == 1


def test_static_onnx_and_video_smoke(tmp_path):
    # Constant synthetic graph tests plumbing ONLY, never accuracy or trained detection.
    import onnx
    from onnx import helper, TensorProto, numpy_helper
    prediction=np.array([[[5,5,20,20,.9,3]]],np.float32)
    graph=helper.make_graph([helper.make_node('Constant',[],['out'],value=numpy_helper.from_array(prediction))],
        'synthetic-smoke',[helper.make_tensor_value_info('images',TensorProto.FLOAT,[1,3,32,32])],
        [helper.make_tensor_value_info('out',TensorProto.FLOAT,[1,1,6])])
    model=helper.make_model(graph,opset_imports=[helper.make_opsetid('',17)],ir_version=9)
    model_path=tmp_path/'toy.onnx'; onnx.save(model,model_path)
    assert Detector(model_path).run(np.zeros((32,32,3),np.uint8))[0].shape == (1,6)
    source=tmp_path/'source.mp4'
    writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'mp4v'),10,(64,64))
    assert writer.isOpened()
    for _ in range(5): writer.write(np.zeros((64,64,3),np.uint8))
    writer.release()
    target=tmp_path/'demo.mp4'
    demo(SimpleNamespace(model=model_path,threads=1,video=str(source),output=str(target),conf=.25,seconds=1,show=False))
    cap=cv2.VideoCapture(str(target))
    assert cap.get(cv2.CAP_PROP_FRAME_COUNT)==5
    cap.release()


def test_accuracy_perfect_and_empty(tmp_path):
    from roadscene import accuracy
    (tmp_path/'labels/test').mkdir(parents=True)
    image=tmp_path/'image.png'
    cv2.imwrite(str(image),np.zeros((100,100,3),np.uint8))
    (tmp_path/'labels/test/image.txt').write_text('\n'.join(f'{c} .5 .5 .2 .2' for c in range(4)))
    class Perfect:
        def run(self,image,threshold):
            return np.array([[40,40,60,60,.99,c] for c in range(4)]),0.01
    result=accuracy(Perfect(),[image],tmp_path)
    assert result['mAP50_95'] == pytest.approx(1)
    class Empty:
        def run(self,image,threshold):
            return np.empty((0,6)),0.01
    assert accuracy(Empty(),[image],tmp_path)['mAP50_95']==0
