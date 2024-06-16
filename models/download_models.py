#!/usr/bin/python3
import os
import urllib.request

# URLs of files to download
urls = {
    "yolov10": [
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov10n-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov10s-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov10m-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov10b-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov10l-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov10x-trt.onnx",
    ],
    "yolov8_detection": [
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8n-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8s-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8m-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8l-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8x-trt.onnx",
    ],
    "yolov8_segmentation": [
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8n-seg-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8s-seg-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8m-seg-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8l-seg-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov8x-seg-trt.onnx",
    ],
    "yolov9_detection": [
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov9-t-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov9-s-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov9-m-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov9-c-trt.onnx",
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov9-e-trt.onnx",
    ],
    "yolov9_segmentation": [
        "https://github.com/levipereira/yolo_e2e/releases/download/v1.0/yolov9-c-seg-trt.onnx"
    ]
}

# Destination directory
destination = "./"

# Function to download files
def download_files(file_urls):
    for url in file_urls:
        filename = os.path.join(destination, os.path.basename(url))
        print(f"\n\nDownloading: {filename}...")
        try:
            urllib.request.urlretrieve(url, filename)
            print(f"Download complete: {filename}.\n")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")

def main():
    print("Choose the model:")
    print("1. YOLOv10")
    print("2. YOLOv8")
    print("3. YOLOv9")

    choice = input("Enter 1, 2, or 3: ")

    if choice == "1":
        print("You chose YOLOv10.")
        print("Choose the download option:")
        print("1. Download all models")
        print("2. Choose a specific model to download")

        download_choice = input("Enter 1 or 2: ")

        if download_choice == "1":
            download_files(urls["yolov10"])
        elif download_choice == "2":
            print("Choose the specific model:")
            models = ["yolov10n", "yolov10s", "yolov10m", "yolov10b", "yolov10l", "yolov10x"]
            for i, model in enumerate(models):
                print(f"{i + 1}. {model}")
            model_choice = int(input("Enter the number of the model you want to download: ")) - 1
            if 0 <= model_choice < len(models):
                download_files([urls["yolov10"][model_choice]])
            else:
                print("Invalid choice. Exiting the program.")
        else:
            print("Invalid choice. Exiting the program.")

    elif choice == "2":
        print("You chose YOLOv8.")
        print("Choose the type:")
        print("1. Detection")
        print("2. Segmentation")

        yolov8_choice = input("Enter 1 or 2: ")

        if yolov8_choice == "1":
            print("You chose Detection.")
            print("Choose the download option:")
            print("1. Download all detection models")
            print("2. Choose a specific detection model to download")

            download_choice = input("Enter 1 or 2: ")

            if download_choice == "1":
                download_files(urls["yolov8_detection"])
            elif download_choice == "2":
                print("Choose the specific model:")
                models = ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"]
                for i, model in enumerate(models):
                    print(f"{i + 1}. {model}")
                model_choice = int(input("Enter the number of the model you want to download: ")) - 1
                if 0 <= model_choice < len(models):
                    download_files([urls["yolov8_detection"][model_choice]])
                else:
                    print("Invalid choice. Exiting the program.")
            else:
                print("Invalid choice. Exiting the program.")

        elif yolov8_choice == "2":
            print("You chose Segmentation.")
            print("Choose the download option:")
            print("1. Download all segmentation models")
            print("2. Choose a specific segmentation model to download")

            download_choice = input("Enter 1 or 2: ")

            if download_choice == "1":
                download_files(urls["yolov8_segmentation"])
            elif download_choice == "2":
                print("Choose the specific model:")
                models = ["yolov8n-seg", "yolov8s-seg", "yolov8m-seg", "yolov8l-seg", "yolov8x-seg"]
                for i, model in enumerate(models):
                    print(f"{i + 1}. {model}")
                model_choice = int(input("Enter the number of the model you want to download: ")) - 1
                if 0 <= model_choice < len(models):
                    download_files([urls["yolov8_segmentation"][model_choice]])
                else:
                    print("Invalid choice. Exiting the program.")
            else:
                print("Invalid choice. Exiting the program.")

        else:
            print("Invalid choice. Exiting the program.")

    elif choice == "3":
        print("You chose YOLOv9.")
        print("Choose the type:")
        print("1. Detection")
        print("2. Segmentation")

        yolov9_choice = input("Enter 1 or 2: ")

        if yolov9_choice == "1":
            print("You chose Detection.")
            print("Choose the download option:")
            print("1. Download all detection models")
            print("2. Choose a specific detection model to download")

            download_choice = input("Enter 1 or 2: ")

            if download_choice == "1":
                download_files(urls["yolov9_detection"])
            elif download_choice == "2":
                print("Choose the specific model:")
                models = ["yolov9-t", "yolov9-s", "yolov9-m", "yolov9-c", "yolov9-e"]
                for i, model in enumerate(models):
                    print(f"{i + 1}. {model}")
                model_choice = int(input("Enter the number of the model you want to download: ")) - 1
                if 0 <= model_choice < len(models):
                    download_files([urls["yolov9_detection"][model_choice]])
                else:
                    print("Invalid choice. Exiting the program.")
            else:
                print("Invalid choice. Exiting the program.")

        elif yolov9_choice == "2":
            print("You chose Segmentation.")
            print("Choose the download option:")
            print("1. Download all segmentation models")
            print("2. Choose a specific segmentation model to download")

            download_choice = input("Enter 1 or 2: ")

            if download_choice == "1":
                download_files(urls["yolov9_segmentation"])
            elif download_choice == "2":
                print("Choose the specific model:")
                models = ["yolov9-c-seg"]
                for i, model in enumerate(models):
                    print(f"{i + 1}. {model}")
                model_choice = int(input("Enter the number of the model you want to download: ")) - 1
                if 0 <= model_choice < len(models):
                    download_files([urls["yolov9_segmentation"][model_choice]])
                else:
                    print("Invalid choice. Exiting the program.")
            else:
                print("Invalid choice. Exiting the program.")

        else:
            print("Invalid choice. Exiting the program.")

    else:
        print("Invalid choice. Exiting the program.")

if __name__ == "__main__":
    main()
