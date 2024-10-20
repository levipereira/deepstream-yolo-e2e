
import sys
import os
import math
from datetime import datetime
import gi # type: ignore
gi.require_version('Gst', '1.0')
from gi.repository import Gst,GLib # type: ignore

from common.FPS import PERF_DATA
from component.source_factory import create_source_bin , parse_media_source
from component.rtsp_server import create_rtsp_server
from component.probes import sink_pad_buffer_probe
from common.bus_call import bus_call
from common.constants import *

os.environ['USE_NEW_NVSTREAMMUX'] = 'yes'

# Function to create the pipeline
def create_pipeline(args):
    Gst.init(None)
    stream_output=args.output.upper()
    model_type = args.model_type
    
    output_file_path=None
    media_sources = parse_media_source('config/media.ini')

    number_sources = len(media_sources)
    if number_sources == 0:
        print("No active media sources found. Exiting...")
        sys.exit(1)
    perf_data = PERF_DATA(number_sources)



    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write("Unable to create Pipeline\n")
        return None

    elements = {
        "streammux": ("nvstreammux", "stream-muxer"),
        "pgie": ("nvinfer", "primary-inference"),
    }
 
    if stream_output == "SILENT":
        elements["sink"] = ("fakesink", "fakesink")

    if stream_output in ("FILE", "RTSP", "DISPLAY"):
        elements["nvvidconv_tiler"] = ("nvvideoconvert", "nvvidconv_tiler")
        elements["filter_tiler"] = ("capsfilter", "filter_tiler")
        elements["nvtiler"] = ("nvmultistreamtiler", "nvtiler")
        elements["nvosd"] = ("nvdsosd", "onscreendisplay")
        if stream_output in ("FILE","RTSP"):
            elements["nvvidconv_encoder"] = ("nvvideoconvert", "nvvidconv_encoder")
            elements["filter_encoder"] = ("capsfilter", "filter_encoder")
            elements["encoder"] = ("nvv4l2h264enc", "encoder")
            elements["codeparser"] = ("h264parse", "h264-parser2")
            if stream_output  == "FILE":
                elements["container"] = ("matroskamux", "muxer")
                elements["sink"] = ("filesink", "file-sink")
            if stream_output  == "RTSP":
                elements["rtppay"] = ("rtph264pay", "rtppay")
                elements["sink"] = ("udpsink", "udpsink")
        else:
            elements["sink"] = ("nveglglessink", "nvvideo-renderer")    

    
    ## Create Elements
    for name, val in elements.items():
        element = Gst.ElementFactory.make(val[0], val[1])
        if not element:
            sys.stderr.write(f"Unable to create {name}\n")
            return None
        elements[name] = element

    ## Configure Elements
    if os.environ.get('USE_NEW_NVSTREAMMUX') != 'yes':
        elements["streammux"].set_property('width', MUXER_OUTPUT_WIDTH)
        elements["streammux"].set_property('height', MUXER_OUTPUT_HEIGHT)
        elements["streammux"].set_property('batched-push-timeout', MUXER_BATCH_TIMEOUT_USEC)
    elements["streammux"].set_property('batch-size', number_sources)
    elements["streammux"].set_property('config-file-path', CONFIG_NEW_STREAMMUX_PATH)

    if model_type == 'det':
        elements["pgie"].set_property('config-file-path', CONFIG_PGIE_YOLO_DET_PATH)
    elif model_type == 'seg':
        elements["pgie"].set_property('config-file-path', CONFIG_PGIE_YOLO_SEG_PATH)
    else:
        sys.stderr.write(f"Model Type not supported {model_type}\n")
        exit

    if stream_output == "SILENT":
        elements["sink"].set_property('enable-last-sample', 0)
        elements["sink"].set_property('sync', 0)
    
    if stream_output in ("FILE", "RTSP", "DISPLAY"):
        elements["filter_tiler"].set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA"))
        tiler_rows=int(math.sqrt(number_sources))
        tiler_columns=int(math.ceil((1.0*number_sources)/tiler_rows))
        elements["nvtiler"].set_property("rows",tiler_rows)
        elements["nvtiler"].set_property("columns",tiler_columns)
        elements["nvtiler"].set_property("width", TILED_OUTPUT_WIDTH)
        elements["nvtiler"].set_property("height", TILED_OUTPUT_HEIGHT)

        elements["nvosd"].set_property('process-mode',OSD_PROCESS_MODE)
        elements["nvosd"].set_property('display-text',OSD_DISPLAY_TEXT)
        if model_type == 'det':
            elements["nvosd"].set_property('display-bbox', 1)
        if model_type == 'seg':
            elements["nvosd"].set_property('display-bbox', 0)
            elements["nvosd"].set_property('display-mask', 1)


        if stream_output in ("FILE", "RTSP"):
            elements["filter_encoder"].set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))
            elements["encoder"].set_property('bitrate', 4097152)
 
            if stream_output == "FILE":
                output_directory = config.get('Settings', 'OUTPUT_DIRECTORY')
                output_prefix =  config.get('Settings', 'OUTPUT_PREFIX') 

                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                output_file_name = f"{output_prefix}_{timestamp}.mp4"
                output_file_path = os.path.join(output_directory, output_file_name)

                if not os.path.exists(output_directory):
                    os.makedirs(output_directory)
                print(output_file_path)

                elements["sink"].set_property('location', output_file_path)
                elements["sink"].set_property('sync', 0)
            
            if stream_output == "RTSP":
                elements["sink"].set_property('host', "127.0.0.1")
                elements["sink"].set_property('port', RTSP_UDPSYNC)
                elements["sink"].set_property('async', False)
                elements["sink"].set_property('sync', 1)
            

    ## Add Elements to Pipeline

    for element in elements.values():
        pipeline.add(element)


    ## Create Sources 
    for index, (media, url, uri) in enumerate(media_sources):
        print(f"Source: {url}. Creating source_bin {index} \n ")
        source_bin = create_source_bin(index, uri)
        if not source_bin:
            sys.stderr.write("Unable to create source bin \n")
        pipeline.add(source_bin)
        padname = "sink_%u" % index
        # sinkpad = elements["streammux"].request_pad_simple(padname)
        sinkpad = elements["streammux"].request_pad_simple(padname)
        if not sinkpad:
            sys.stderr.write("Unable to create sink pad bin \n")
        srcpad = source_bin.get_static_pad("src")
        if not srcpad:
            sys.stderr.write("Unable to create src pad bin \n")
        srcpad.link(sinkpad)


    elements["streammux"].link(elements["pgie"])

    if stream_output == "SILENT":
        element_probe = elements["pgie"]
        elements["pgie"].link(elements["sink"])

    if stream_output in ("FILE", "RTSP", "DISPLAY"):
        element_probe = elements["nvtiler"]
        elements["pgie"].link(elements["nvvidconv_tiler"])
        elements["nvvidconv_tiler"].link(elements["filter_tiler"])
        elements["filter_tiler"].link(elements["nvtiler"])
        elements["nvtiler"].link(elements["nvosd"])
        if stream_output in ("FILE", "RTSP"):
            elements["nvosd"].link(elements["nvvidconv_encoder"])
            elements["nvvidconv_encoder"].link(elements["filter_encoder"])
            elements["filter_encoder"].link(elements["encoder"])
            if stream_output == "FILE":
                elements["encoder"].link(elements["codeparser"])
                elements["codeparser"].link(elements["container"])
                elements["container"].link(elements["sink"])
            if stream_output == "RTSP":
                elements["encoder"].link(elements["rtppay"])
                elements["rtppay"].link(elements["sink"])
        
        else:
            elements["nvosd"].link(elements["sink"])

    return pipeline , element_probe, perf_data, output_file_path


# Function to run the pipeline
def run_pipeline(args):
    if args.output == "rtsp":
        create_rtsp_server()

    pipeline, element_probe, perf_data, output_file_path  = create_pipeline(args)
    if not pipeline:
        sys.stderr.write("Failed to create pipeline\n")
        return

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    elementsinkpad = element_probe.get_static_pad("sink")
    if not elementsinkpad:
        sys.stderr.write("Unable to get sink pad of nvosd\n")
        return
    elementsinkpad.add_probe(Gst.PadProbeType.BUFFER, sink_pad_buffer_probe, 0, perf_data)
    GLib.timeout_add(5000, perf_data.perf_print_callback)

    print("Starting pipeline \n")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except:
        pass

    pipeline.set_state(Gst.State.NULL)
    if args.output == "file":
        print(f"File output :  {output_file_path}") 