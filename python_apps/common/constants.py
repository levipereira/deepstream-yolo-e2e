import configparser

config = configparser.ConfigParser()
config.read('config/config.ini')

MUXER_BATCH_TIMEOUT_USEC = config.getint('Settings', 'MUXER_BATCH_TIMEOUT_USEC')
MUXER_OUTPUT_WIDTH = config.getint('Settings', 'MUXER_OUTPUT_WIDTH')
MUXER_OUTPUT_HEIGHT = config.getint('Settings', 'MUXER_OUTPUT_HEIGHT')

TILED_OUTPUT_WIDTH = config.getint('Settings', 'TILED_OUTPUT_WIDTH')
TILED_OUTPUT_HEIGHT = config.getint('Settings', 'TILED_OUTPUT_HEIGHT')
OSD_PROCESS_MODE = config.getint('Settings', 'OSD_PROCESS_MODE')
OSD_DISPLAY_TEXT = config.getint('Settings', 'OSD_DISPLAY_TEXT')
RTSP_UDPSYNC = config.getint('Settings', 'RTSP_UDPSYNC')

CONFIG_PGIE_YOLO_DET_PATH = "/apps/deepstream-yolo-e2e/config/pgie/config_pgie_yolo_det.txt"
CONFIG_PGIE_YOLO_SEG_PATH = "/apps/deepstream-yolo-e2e/config/pgie/config_pgie_yolo_seg.txt"
CONFIG_NEW_STREAMMUX_PATH = "/apps/deepstream-yolo-e2e/config/streammux/new_streammux_config.txt"
