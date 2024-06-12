import argparse
import os
import platform
import sys
import time
from pathlib import Path
import pandas as pd
import torch

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLO root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
if platform.system() != 'Windows':
    ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.experimental import attempt_load
from models.experimental_trt import End2End_TRT
from models.yolo import ClassificationModel, Detect, DDetect, DualDetect, DualDDetect, DetectionModel, SegmentationModel, DSegment
from utils.general import (LOGGER, Profile, check_img_size, check_requirements, 
                            colorstr, file_size, get_default_args, print_args, url2file)
from utils.torch_utils import select_device, smart_inference_mode
from torch.jit import TracerWarning
import warnings

warnings.filterwarnings("ignore", category=TracerWarning)
warnings.filterwarnings("ignore", category=FutureWarning )

MACOS = platform.system() == 'Darwin'  # macOS environment

def export_formats():
    # YOLO export formats
    x = [
        ['PyTorch', '-', '.pt', True, True],
        ['ONNX TRT', 'onnx_trt', '_trt.onnx', True, True],
        ]
    return pd.DataFrame(x, columns=['Format', 'Argument', 'Suffix', 'CPU', 'GPU'])


def try_export(inner_func):
    # YOLO export decorator, i..e @try_export
    inner_args = get_default_args(inner_func)

    def outer_func(*args, **kwargs):
        prefix = inner_args['prefix']
        try:
            with Profile() as dt:
                f, model = inner_func(*args, **kwargs)
            LOGGER.info(f'{prefix} export success ✅ {dt.t:.1f}s, saved as {f} ({file_size(f):.1f} MB)')
            return f, model
        except Exception as e:
            LOGGER.info(f'{prefix} export failure ❌ {dt.t:.1f}s: {e}')
            return None, None

    return outer_func

@try_export
def export_onnx_trt(model, im, file, class_agnostic, topk_all, iou_thres, conf_thres, device, labels, mask_resolution, pooler_scale, sampling_ratio, prefix=colorstr('ONNX TRT:')):
    is_det_model=True
    if isinstance(model, SegmentationModel):
        is_det_model=False

    ## force SegmentationModel  
    env_is_det_model = os.getenv("MODEL_DET")
    if env_is_det_model == "0":
        is_det_model = False
    # YOLO ONNX export
    check_requirements('onnx')
    import onnx
    LOGGER.info(f'\n{prefix} starting export with onnx {onnx.__version__}...')
    f = os.path.splitext(file)[0] + "-trt.onnx"
    batch_size = 'batch'
    d = {
        'stride': int(max(model.stride)),
        'names': model.names,
        'model type' : 'Detection' if is_det_model else 'Segmentation',
        'TRT Compatibility': '8.6 or above',
        'TRT Plugins': 'EfficientNMS_TRT' if is_det_model else 'EfficientNMSX_TRT, ROIAlign'
        }

    dynamic_axes = {'images': {0 : 'batch', 2: 'height', 3:'width'}, } # variable length axes

    output_axes = {
                    'num_dets': {0: 'batch'},
                    'det_boxes': {0: 'batch'},
                    'det_scores': {0: 'batch'},
                    'det_classes': {0: 'batch'},
                 }

    if is_det_model:
        output_names = ['num_dets', 'det_boxes', 'det_scores', 'det_classes'] 
        shapes = [ batch_size, 1,  
                batch_size,  topk_all, 4,
                batch_size,  topk_all,  
                batch_size,  topk_all]
        
    else:
        output_axes['det_masks'] = {0: 'batch'}
        output_names = ['num_dets', 'det_boxes', 'det_scores', 'det_classes', 'det_masks'] 
        shapes = [ batch_size, 1,  
                batch_size,  topk_all, 4,
                batch_size,  topk_all,  
                batch_size,  topk_all, 
                batch_size,  topk_all, mask_resolution * mask_resolution]

    dynamic_axes.update(output_axes)
    
    model = End2End_TRT(model, class_agnostic, topk_all, iou_thres, conf_thres, mask_resolution, pooler_scale, sampling_ratio, None ,device, labels, is_det_model )

    torch.onnx.export(model, 
                          im, 
                          f, 
                          verbose=False, 
                          export_params=True,       # store the trained parameter weights inside the model file
                          opset_version=16, 
                          do_constant_folding=True, # whether to execute constant folding for optimization
                          input_names=['images'],
                          output_names=output_names,
                          dynamic_axes=dynamic_axes)

    # Checks
    model_onnx = onnx.load(f)  # load onnx model
    onnx.checker.check_model(model_onnx)  # check onnx model

    for k, v in d.items():
        meta = model_onnx.metadata_props.add()
        meta.key, meta.value = k, str(v)
        

    for i in model_onnx.graph.output:
        for j in i.type.tensor_type.shape.dim:
            j.dim_param = str(shapes.pop(0))

    check_requirements('onnxsim')
    try:
        import onnxsim
        LOGGER.info(f'\n{prefix} Starting to simplify ONNX...')
        model_onnx, check = onnxsim.simplify(model_onnx)
        assert check, 'assert check failed'
    except Exception as e:
        LOGGER.info(f'\n{prefix} Simplifier failure: {e}')

    onnx.save(model_onnx,f)
    
    check_requirements('onnx_graphsurgeon')
    LOGGER.info(f'\n{prefix} Starting to cleanup ONNX using onnx_graphsurgeon...')
    try:
        import onnx_graphsurgeon as gs

        graph = gs.import_onnx(model_onnx)
        graph = graph.cleanup().toposort()
        model_onnx = gs.export_onnx(graph)
    except Exception as e:
        LOGGER.info(f'\n{prefix} Cleanup failure: {e}')

    return f, model_onnx


@smart_inference_mode()
def run(
        weights=ROOT / 'yolo.pt',  # weights path
        imgsz=(640, 640),  # image (height, width)
        device='cpu',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        include=('onnx_trt',),  # include formats
        class_agnostic=False,  # TF: add agnostic NMS to model
        topk_all=100,  # TF.js NMS: topk for all classes to keep
        iou_thres=0.45,  # TF.js NMS: IoU threshold
        conf_thres=0.25,  # TF.js NMS: confidence threshold
        mask_resolution=56,
        pooler_scale=0.25,
        sampling_ratio=0,
):
    t = time.time()
    include = [x.lower() for x in include]  # to lowercase
    fmts = tuple(export_formats()['Argument'][1:])  # --include arguments
    flags = [x in include for x in fmts]
    assert sum(flags) == len(include), f'ERROR: Invalid --include {include}, valid --include arguments are {fmts}'
    onnx_trt = flags  # export booleans
    file = Path(url2file(weights) if str(weights).startswith(('http:/', 'https:/')) else weights)  # PyTorch weights

    # Load PyTorch model
    device = select_device(device)
    model = attempt_load(weights, device=device, inplace=True, fuse=True)  # load FP32 model
    # Checks
    imgsz *= 2 if len(imgsz) == 1 else 1  # expand
    
    # Input
    gs = int(max(model.stride))  # grid size (max stride)
    imgsz = [check_img_size(x, gs) for x in imgsz]  # verify img_size are gs-multiples
    im = torch.zeros(1, 3, *imgsz).to(device)  # image size(1,3,320,192) BCHW iDetection

    # Update model
    model.eval()
    for k, m in model.named_modules():
        if isinstance(m, (Detect, DDetect, DualDetect, DualDDetect)):
            m.inplace = True
            m.dynamic = True
            m.export = True

    for _ in range(2):
        y = model(im)  # dry runs

    shape = tuple((y[0] if isinstance(y, (tuple, list)) else y).shape)  # model output shape
    LOGGER.info(f"\n{colorstr('PyTorch:')} starting from {file} with output shape {shape} ({file_size(file):.1f} MB)")

    # Exports
    f = [''] * len(fmts)  # exported filenames
    if onnx_trt:
        labels = model.names
        f[0], _ = export_onnx_trt(model, im, file, class_agnostic, topk_all, iou_thres, conf_thres, device, len(labels), mask_resolution, pooler_scale, sampling_ratio )
    # Finish
    f = [str(x) for x in f if x]
    LOGGER.info(f'\nExport complete ({time.time() - t:.1f}s)'
                f"\nResults saved to {colorstr('bold', file.parent.resolve())}"
                f"\nVisualize:       https://netron.app")
    return f  # return list of exported files/dirs


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolo.pt', help='model.pt path(s)')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640, 640], help='image (h, w)')
    parser.add_argument('--device', default='cpu', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--class-agnostic', action='store_true', help='Agnostic NMS (single class)')
    parser.add_argument('--topk-all', type=int, default=100, help='Topk for all classes to keep')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='IoU threshold')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='Confidence threshold.')
    parser.add_argument('--mask-resolution', type=int, default=160, help='Mask pooled output.')
    parser.add_argument('--pooler-scale', type=float, default=0.25, help='Multiplicative factor used to translate the ROI coordinates. ')
    parser.add_argument('--sampling-ratio', type=int, default=0, help='Number of sampling points in the interpolation. Allowed values are non-negative integers.')
    parser.add_argument('--include', nargs='+', default=['onnx_trt'], help='onnx_trt')
    
    opt = parser.parse_args()

    print_args(vars(opt))
    return opt

def main(opt):
    for opt.weights in (opt.weights if isinstance(opt.weights, list) else [opt.weights]):
        run(**vars(opt))

if __name__ == "__main__":
    opt = parse_opt()
    main(opt)
