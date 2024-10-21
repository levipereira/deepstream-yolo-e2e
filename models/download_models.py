#!/usr/bin/python3
import os
import urllib.request

# URLs of files to download
base_url = "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/"

urls = {
    "coco-labels": ["coco_labels.txt"],
    "person": [
        "yolov8n-person-trt.onnx",
        "person_labels.txt"
    ],
    "football": [
        "yolov8m-football-trt.onnx",
        "yolov8n-football-trt.onnx",
        "football_labels.txt"
    ],
    "face": [
        "yolov8l-face-trt.onnx",
        "yolov8m-face-trt.onnx",
        "yolov8n-face-trt.onnx",
        "face_labels.txt"
    ],
    "drone": [
        "yolov8m-drone-trt.onnx",
        "yolov8n-drone-trt.onnx",
        "drone_labels.txt"
    ],
    "parking": [
        "yolov8m-parking-trt.onnx",
        "parking_labels.txt"
    ],
    "coco-yolov10": [
        "yolov10n-trt.onnx",
        "yolov10s-trt.onnx",
        "yolov10m-trt.onnx",
        "yolov10b-trt.onnx",
        "yolov10l-trt.onnx",
        "yolov10x-trt.onnx"
    ],
    "coco-yolov8_detection": [
        "yolov8n-trt.onnx",
        "yolov8s-trt.onnx",
        "yolov8m-trt.onnx",
        "yolov8l-trt.onnx",
        "yolov8x-trt.onnx"
    ],
    "coco-yolov8_segmentation": [
        "yolov8n-seg-trt.onnx",
        "yolov8s-seg-trt.onnx",
        "yolov8m-seg-trt.onnx",
        "yolov8l-seg-trt.onnx",
        "yolov8x-seg-trt.onnx"
    ],
    "coco-yolov9_detection": [
        "yolov9-t-trt.onnx",
        "yolov9-s-trt.onnx",
        "yolov9-m-trt.onnx",
        "yolov9-c-trt.onnx",
        "yolov9-e-trt.onnx"
    ],
    "coco-yolov9_segmentation": [
        "yolov9-c-seg-trt.onnx"
    ]
}

# Destination directory
destination = "./"

# Function to download files
def download_files(file_urls):
    for file_name in file_urls:
        url = f"{base_url}{file_name}"
        filename = os.path.join(destination, os.path.basename(file_name))
        print(f"\n\nDownloading: {filename}...")
        try:
            urllib.request.urlretrieve(url, filename)
            print(f"Download complete: {filename}.\n")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")

def main():
    print("Choose the model type:")
    print("1. COCO-YOLOv10")
    print("2. COCO-YOLOv8")
    print("3. COCO-YOLOv9")
    print("4. Person Models")
    print("5. Football Models")
    print("6. Face Models")
    print("7. Drone Models")
    print("8. Parking Models")

    choice = input("Enter a number from 1 to 8: ")

    if choice == "1":
        print("You chose COCO-YOLOv10.")
        download_yolov10()

    elif choice == "2":
        print("You chose COCO-YOLOv8.")
        download_yolov8()

    elif choice == "3":
        print("You chose COCO-YOLOv9.")
        download_yolov9()

    elif choice == "4":
        print("You chose Person Models.")
        download_model("person")

    elif choice == "5":
        print("You chose Football Models.")
        download_model("football")

    elif choice == "6":
        print("You chose Face Models.")
        download_model("face")

    elif choice == "7":
        print("You chose Drone Models.")
        download_model("drone")

    elif choice == "8":
        print("You chose Parking Models.")
        download_model("parking")

    else:
        print("Invalid choice. Exiting the program.")

def download_yolov10():
    print("Choose the download option:")
    print("1. Download all models")
    print("2. Choose a specific model to download")

    download_choice = input("Enter 1 or 2: ")

    if download_choice == "1":
        download_files(urls["coco-yolov10"])
    elif download_choice == "2":
        select_specific_model("coco-yolov10", ["yolov10n", "yolov10s", "yolov10m", "yolov10b", "yolov10l", "yolov10x"])
    else:
        print("Invalid choice. Exiting the program.")

def download_yolov8():
    print("Choose the type:")
    print("1. Detection")
    print("2. Segmentation")

    yolov8_choice = input("Enter 1 or 2: ")

    if yolov8_choice == "1":
        print("You chose Detection.")
        download_model_type("coco-yolov8_detection", ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"])
    elif yolov8_choice == "2":
        print("You chose Segmentation.")
        download_model_type("coco-yolov8_segmentation", ["yolov8n-seg", "yolov8s-seg", "yolov8m-seg", "yolov8l-seg", "yolov8x-seg"])
    else:
        print("Invalid choice. Exiting the program.")

def download_yolov9():
    print("Choose the type:")
    print("1. Detection")
    print("2. Segmentation")

    yolov9_choice = input("Enter 1 or 2: ")

    if yolov9_choice == "1":
        print("You chose Detection.")
        download_model_type("coco-yolov9_detection", ["yolov9-t", "yolov9-s", "yolov9-m", "yolov9-c", "yolov9-e"])
    elif yolov9_choice == "2":
        print("You chose Segmentation.")
        download_model_type("coco-yolov9_segmentation", ["yolov9-c-seg"])
    else:
        print("Invalid choice. Exiting the program.")

def download_model(model_type):
    print("Choose the download option:")
    print("1. Download all models")
    print("2. Choose a specific model to download")

    download_choice = input("Enter 1 or 2: ")

    if download_choice == "1":
        download_files(urls[model_type])
    elif download_choice == "2":
        models = [f for f in urls[model_type] if not f.endswith("labels.txt")]
        select_specific_model(model_type, models)
        download_files([urls[model_type][-1]])  # Last item is the labels file
    else:
        print("Invalid choice. Exiting the program.")

def download_model_type(model_type, models):
    print("Choose the download option:")
    print("1. Download all models")
    print("2. Choose a specific model to download")

    download_choice = input("Enter 1 or 2: ")

    if download_choice == "1":
        download_files(urls[model_type])
    elif download_choice == "2":
        select_specific_model(model_type, models)
    else:
        print("Invalid choice. Exiting the program.")

def select_specific_model(model_type, models):
    print("Choose the specific model:")
    for i, model in enumerate(models):
        print(f"{i + 1}. {model}")
    model_choice = int(input("Enter the number of the model you want to download: ")) - 1
    if 0 <= model_choice < len(models):
        download_files([urls[model_type][model_choice]])
    else:
        print("Invalid choice. Exiting the program.")

if __name__ == "__main__":
    main()
