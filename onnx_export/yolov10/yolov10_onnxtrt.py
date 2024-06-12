import os
import sys
import argparse
import warnings
import onnx
import onnxsim
import torch
import torch.nn as nn
from copy import deepcopy
from ultralytics import YOLO
from ultralytics.utils.torch_utils import select_device
from ultralytics.nn.modules import C2f, Detect, RTDETRDecoder, v10Detect

 

class End2End(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x):
        det_boxes = x[:, :, :4]
        det_scores = x[:, :, 4]
        det_classes = x[:, :, 5].int()
        num_dets = (x[:, :, 4] > 0.0).sum(dim=1, keepdim=True).int() 
        return num_dets, det_boxes, det_scores, det_classes


def suppress_warnings():
    warnings.filterwarnings('ignore', category=torch.jit.TracerWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)


def yolov10_export(weights, device):
    model = YOLO(weights)
    model = deepcopy(model.model).to(device)
    for p in model.parameters():
        p.requires_grad = False
    model.eval()
    model.float()
    model = model.fuse()
    for k, m in model.named_modules():
        if isinstance(m, (Detect, RTDETRDecoder)):
            m.dynamic = False
            m.export = True
            m.format = 'onnx'
            if isinstance(m, v10Detect):
                m.max_det = args.max_det
        elif isinstance(m, C2f):
            m.forward = m.forward_split
    return model


def main(args):
    suppress_warnings()

    print('\nStarting: %s' % args.weights)

    device = select_device('cpu')
    model = yolov10_export(args.weights, device)
    batch_size = 'batch'

    if len(model.names.keys()) > 0:
        print('\nCreating labels.txt file')
        f = open('labels.txt', 'w')
        for name in model.names.values():
            f.write(name + '\n')
        f.close()
    
    model = nn.Sequential(model, End2End())

    img_size = args.size * 2 if len(args.size) == 1 else args.size

    onnx_input_im = torch.zeros(args.batch, 3, *img_size).to(device)
    onnx_output_file = os.path.basename(args.weights).split('.pt')[0] + '.onnx'

    output_names = ['num_dets', 'det_boxes', 'det_scores', 'det_classes'] 
    shapes = [ batch_size, 1,  
            batch_size,  args.max_det, 4,
            batch_size,  args.max_det,  
            batch_size,  args.max_det]
    dynamic_axes = {'images': {0 : 'batch', 2: 'height', 3:'width'}, } # variable length axes

    output_axes = {
                    'num_dets': {0: 'batch'},
                    'det_boxes': {0: 'batch'},
                    'det_scores': {0: 'batch'},
                    'det_classes': {0: 'batch'},
                 }

    dynamic_axes.update(output_axes)

    print('\nExporting the model to ONNX')
    torch.onnx.export(model, onnx_input_im, onnx_output_file, verbose=False, opset_version=args.opset,
                      do_constant_folding=True, input_names=['images'], output_names=output_names,
                      dynamic_axes=dynamic_axes)

    model_onnx = onnx.load(onnx_output_file)  # load onnx model
    onnx.checker.check_model(model_onnx)  # check onnx model

    for i in model_onnx.graph.output:
        for j in i.type.tensor_type.shape.dim:
            j.dim_param = str(shapes.pop(0))


    print('Simplifying the ONNX model')
    model_onnx, _ = onnxsim.simplify(model_onnx)
    onnx.save(model_onnx, onnx_output_file)

    print('Done: %s\n' % onnx_output_file)


def parse_args():
    parser = argparse.ArgumentParser(description='DeepStream YOLOv10 conversion')
    parser.add_argument('-w', '--weights', required=True, help='Input weights (.pt) file path (required)')
    parser.add_argument('-s', '--size', nargs='+', type=int, default=[640], help='Inference size [H,W] (default [640])')
    parser.add_argument('--opset', type=int, default=16, help='ONNX opset version')
    parser.add_argument('--max_det', type=int, default=300, help='Max detections per image')
    args = parser.parse_args()
    if not os.path.isfile(args.weights):
        raise SystemExit('Invalid weights file')
    return args


if __name__ == '__main__':
    args = parse_args()
    sys.exit(main(args))