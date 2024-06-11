# deepstream-yolo-e2e
Implementation of End-to-End YOLO Models for DeepStream


 This repository provides an implementation of End-to-End YOLO models for DeepStream, aiming to streamline the inference process by offloading Non-Maximum Suppression computations onto the YOLO model itself. This design allows users to leverage dynamic batch sizes and input sizes seamlessly.

By eliminating the need for local NMS processing, users gain the flexibility to configure batch sizes and input sizes on-demand without compromising performance. All NMS computations remain integral to the YOLO model, optimizing resource utilization and simplifying model deployment.
