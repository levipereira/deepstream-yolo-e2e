#!/usr/bin/python3
import sys
import os
import gi
gi.require_version('Gst', '1.0')
gi.require_version("GstRtspServer", "1.0")
from gi.repository import GLib, Gst, GstRtspServer, GstRtsp
import pyds
from common.FPS import PERF_DATA
import time, threading
import configparser
import argparse
import math

# Constants for class IDs used in nvinfer
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3

MUXER_BATCH_TIMEOUT_USEC = 33000

MUXER_OUTPUT_WIDTH=1280
MUXER_OUTPUT_HEIGHT=720

TILED_OUTPUT_WIDTH=1280
TILED_OUTPUT_HEIGHT=720
OSD_PROCESS_MODE= 0
OSD_DISPLAY_TEXT= 1



# Function to handle messages on the bus
def bus_call(bus, message, loop):
    msg_type = message.type
    if msg_type == Gst.MessageType.EOS:
        print("End-of-stream")
        loop.quit()
    elif msg_type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"Error {err}: {debug}")
        loop.quit()
    return True

def cb_newpad(decodebin, decoder_src_pad,data):

    print("In cb_newpad\n")
    caps=decoder_src_pad.get_current_caps()
    if not caps:        
        caps = decoder_src_pad.query_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    source_bin=data
    features=caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    print("gstname=",gstname)
    if(gstname.find("video")!=-1):
        print("features=",features)
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad=source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")

def decodebin_child_added(child_proxy, Object, name, user_data):
    print("Decodebin child added:", name, "\n")
    if name.find("decodebin") != -1:
        Object.connect("child-added", decodebin_child_added, user_data)

    if "source" in name:
        source_element = child_proxy.get_by_name("source")
        if source_element.find_property('drop-on-latency') != None:
            Object.set_property("drop-on-latency", True)

 
def create_source_bin(index,uri):
    print("Creating source bin")

    bin_name="source-bin-%02d" %index
    print(bin_name)
    nbin=Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin \n")

    uri_decode_bin=Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
        
    if not uri_decode_bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    
    uri_decode_bin.set_property("uri",uri)
    uri_decode_bin.connect("pad-added",cb_newpad,nbin)
    uri_decode_bin.connect("child-added",decodebin_child_added,nbin)

    Gst.Bin.add(nbin,uri_decode_bin)
    bin_pad=nbin.add_pad(Gst.GhostPad.new_no_target("src",Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None
    return nbin

def create_rtsp_server():
    rtsp_port_num = 8554
    rtsp_stream_end = "/live"
    username =  'user'
    password =  "pass"
    updsink_port_num = 8245
    codec = 'H264'

    server = GstRtspServer.RTSPServer.new()
    server.props.service = "%d" % rtsp_port_num
    server.attach(None)

    factory = GstRtspServer.RTSPMediaFactory.new()
    factory.set_protocols(GstRtsp.RTSPLowerTrans.TCP)
    factory.set_transport_mode(GstRtspServer.RTSPTransportMode.PLAY)
    factory.set_latency(1)
    factory.set_launch(
        '( udpsrc name=pay0  port=%d buffer-size=10485760  caps="application/x-rtp, media=video, clock-rate=90000, mtu=1300, encoding-name=(string)%s, payload=96 " )'
        % (updsink_port_num, codec)
    )
    factory.set_shared(True)
    permissions = GstRtspServer.RTSPPermissions()
    permissions.add_permission_for_role(username, "media.factory.access", True)
    permissions.add_permission_for_role(username, "media.factory.construct", True)
    factory.set_permissions(permissions)
    server.get_mount_points().add_factory(rtsp_stream_end, factory)
    print("\n *** DeepStream: Launched RTSP Streaming at rtsp://%s:%s@%s:%d%s ***\n\n" %
        (username, password, 'localhost', rtsp_port_num, rtsp_stream_end))

# Function for probe to extract metadata
def sink_pad_buffer_probe(pad, info, u_data):
    frame_number = 0
    num_rects = 0

    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer")
        return Gst.PadProbeReturn.OK

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            # Here you can process metadata as needed

            try:
                l_obj = l_obj.next
            except StopIteration:
                break
        # update frame rate through this probe
        stream_index = "stream{0}".format(frame_meta.pad_index)
        global perf_data
        perf_data.update_fps(stream_index)

        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK

# Function to create the pipeline
def create_pipeline(args):
    Gst.init(None)
    stream_input=args.input
    stream_output=args.output.upper()
    

    number_sources=len(stream_input)
    
    global perf_data
    perf_data = PERF_DATA(len(stream_input))



    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write("Unable to create Pipeline\n")
        return None

    elements = {
        "streammux": ("nvstreammux", "stream-muxer"),
        "pgie": ("nvinfer", "primary-inference"),
    }
 
    if stream_output == "NONE":
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


    elements["pgie"].set_property('config-file-path', "config_pgie_yolo_det.txt")

    if stream_output == "NONE":
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

        if stream_output in ("FILE", "RTSP"):
            elements["filter_encoder"].set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))
            elements["encoder"].set_property('bitrate', 4097152)
 
            if stream_output == "FILE":
                elements["sink"].set_property('location', 'output_file.mp4')
                elements["sink"].set_property('sync', 1)
            
            if stream_output == "RTSP":
                elements["sink"].set_property('host', "127.0.0.1")
                elements["sink"].set_property('port', 8245)
                elements["sink"].set_property('async', False)
                elements["sink"].set_property('sync', 1)
            

    ## Add Elements to Pipeline

    for element in elements.values():
        pipeline.add(element)


    ## Create Sources 
    for i in range(number_sources):
        # os.mkdir(folder_name + "/stream_" + str(i))
        print("Creating source_bin ", i, " \n ")
        uri_name = stream_input[i]
        if uri_name.find("rtsp://") == 0:
            is_live = True
        source_bin = create_source_bin(i, uri_name)
        if not source_bin:
            sys.stderr.write("Unable to create source bin \n")
        pipeline.add(source_bin)
        padname = "sink_%u" % i
        sinkpad = elements["streammux"].request_pad_simple(padname)
        if not sinkpad:
            sys.stderr.write("Unable to create sink pad bin \n")
        srcpad = source_bin.get_static_pad("src")
        if not srcpad:
            sys.stderr.write("Unable to create src pad bin \n")
        srcpad.link(sinkpad)


    elements["streammux"].link(elements["pgie"])

    if stream_output == "NONE":
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

    return pipeline , element_probe

# Function to run the pipeline
def run_pipeline(args):
    if args.output == "RTSP":
        create_rtsp_server()

    pipeline, element_probe = create_pipeline(args)
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
    elementsinkpad.add_probe(Gst.PadProbeType.BUFFER, sink_pad_buffer_probe, 0)
    GLib.timeout_add(5000, perf_data.perf_print_callback)

    print("Starting pipeline \n")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except:
        pass

    pipeline.set_state(Gst.State.NULL)


def parse_args():

    parser = argparse.ArgumentParser(prog="pipeline_yolo.py",
                    description="pipeline_yolo multi stream, multi model inference reference app")
    parser.add_argument(
        "-i",
        "--input",
        help="Path to input streams",
        nargs="+",
        metavar="URIs",
        default=["a"],
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        default="None",
        help="Output",
        choices=["Display", "File", "RTSP", "None"],
    )
    # Check input arguments
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    print(vars(args))
    return args

if __name__ == '__main__':
    args = parse_args()
    sys.exit(run_pipeline(args))
