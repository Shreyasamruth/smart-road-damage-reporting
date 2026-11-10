from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_public_dataset import training_entries


def test_repeat_people_only_in_training(tmp_path):
    (tmp_path/'labels/train').mkdir(parents=True)
    (tmp_path/'labels/train/traffic_person.txt').write_text('2 .5 .5 .2 .2')
    (tmp_path/'labels/train/rdd_road.txt').write_text('3 .5 .5 .2 .2')
    audit = [
        {'split':'train','prepared_image':'images/train/traffic_person.jpg'},
        {'split':'train','prepared_image':'images/train/rdd_road.jpg'},
        {'split':'test','prepared_image':'images/test/traffic_person.jpg'},
        {'split':'val','prepared_image':'images/val/traffic_person.jpg'},
    ]
    entries = training_entries(audit, tmp_path, 4)
    assert len(entries) == 5
    assert sum('traffic_person' in p for p in entries) == 4
    assert all('/train/' in p for p in entries)
    with pytest.raises(ValueError):
        training_entries(audit, tmp_path, 0)


def test_source_aware_rejects_unknown_source(tmp_path):
    import cv2
    import numpy as np
    from roadscene import accuracy
    image = tmp_path/'unknown.jpg'
    cv2.imwrite(str(image), np.zeros((32,32,3),np.uint8))
    with pytest.raises(ValueError, match='Unknown annotation source'):
        accuracy(None, [image], tmp_path, source_aware=True)
