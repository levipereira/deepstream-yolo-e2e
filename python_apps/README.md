## Usage

### Running the Application

You can run the application using the following command-line arguments:

```bash
python main.py -mt <model_type> -o <output>
```

## Command Line Arguments

| Argument          | Short Form | Description                                                | Required |
|-------------------|------------|------------------------------------------------------------|----------|
| `--model-type`    | `-mt`      | Type of model to use (detection or segmentation). Choices: `det` for detection, `seg` for segmentation. | Yes      |
| `--output`        | `-o`       | Output method. Choices: `display`, `file`, `rtsp`, `silent`. | Yes      |

### Output Method Descriptions
- **display**: Outputs video to the standard monitor display.
- **file**: Generates a video file saved on disk.
- **rtsp**: Outputs video via RTSP (Real-Time Streaming Protocol).
- **silent**: No video output is generated.


### Example Commands:

**For detection:**

```bash
python main.py -mt det -o display
```

**For Segmentation:**

```bash
python main.py  -mt seg -o display
```

# Media Configuration File

This repository includes a media configuration file named `media.ini`, located in the `config` directory. This file allows you to specify media sources that can be utilized by the application. Each media source is defined by a section in the `.ini` file.

## File Structure

The `media.ini` file is structured as follows:

```ini
[MediaSettings-0]
type = file  
url = /opt/nvidia/deepstream/deepstream/samples/streams/sample_1080p_h264.mp4    
enable = 0   

[MediaSettings-2]
type = file   
url = /opt/nvidia/deepstream/deepstream/samples/streams/sample_ride_bike.mov
enable = 0  

[MediaSettings-3]
type = rtsp 
url = rtsp://localhost/live   
enable = 0 

[MediaSettings-4]
type = youtube 
url = https://www.youtube.com/watch?v=Uqg8kZjmNIs
enable = 1 

```
# Section Breakdown

Each section is denoted by a header in square brackets, such as `[MediaSettings-0]`, which uniquely identifies a media source.

Each section contains the following parameters:

- **type**: Specifies the type of media source. Possible values include:
  - `file`: Indicates that the media is a file on the local filesystem.
  - `rtsp`: Indicates that the media source is a Real-Time Streaming Protocol (RTSP) stream.
  - `youtube`: Indicates that the media source is a YouTube video.

- **url**: Provides the path or URL to the media source.

- **enable**: A binary flag (0 or 1) indicating whether the media source is active:
  - `1`: The media source is enabled and will be processed.
  - `0`: The media source is disabled and will be ignored by the application.



## General Configuration Settings
The application can be configured using the config/config.init file. Below are the key settings you can modify:

The application can be configured using the `config/config.init` file. Below are the key settings you can modify:

```ini
[Settings]
MUXER_BATCH_TIMEOUT_USEC = 33000
MUXER_OUTPUT_WIDTH = 1280
MUXER_OUTPUT_HEIGHT = 720

TILED_OUTPUT_WIDTH = 1280
TILED_OUTPUT_HEIGHT = 720

OSD_PROCESS_MODE = 0
OSD_DISPLAY_TEXT = 1

OUTPUT_DIRECTORY = ./videos_output
OUTPUT_PREFIX = deepstream_out

RTSP_PORT = 8554
RTSP_FACTORY = "/live"
RTSP_UDPSYNC = 8255


