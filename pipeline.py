import sys
import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst
import pyds

# Constants for class IDs used in nvinfer
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3
MUXER_BATCH_TIMEOUT_USEC = 33000

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

def osd_sink_pad_buffer_probe(pad, info, u_data):
    # Processing metadata for further use or visualization
    frame_number = 0
    num_rects = 0

    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    # Retrieve batch metadata from the gst buffer
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Note that l_obj.data needs a cast to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            # Analytics of detected objects can be done here

            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK

def create_pipeline(input_file, output_file):
    # Initialize GStreamer
    Gst.init(None)

    # Create pipeline element
    print("Creating Pipeline \n")
    pipeline = Gst.Pipeline()

    if not pipeline:
        sys.stderr.write("Unable to create Pipeline\n")
        return None

    # Create elements for the pipeline
    elements = {
        "source": ("filesrc", "file-source"),
        "h264parser": ("h264parse", "h264-parser"),
        "decoder": ("nvv4l2decoder", "nvv4l2-decoder"),
        "streammux": ("nvstreammux", "stream-muxer"),
        "pgie": ("nvinfer", "primary-inference"),
        "nvvidconv": ("nvvideoconvert", "convertor"),
        "nvosd": ("nvdsosd", "onscreendisplay"),
        "nvvidconv2": ("nvvideoconvert", "convertor2"),
        "cap_filter": ("capsfilter", "capsfilter"),
        "encoder": ("nvv4l2h264enc", "encoder"),
        "codeparser": ("h264parse", "h264-parser2"),
        "container": ("qtmux", "muxer"),
        "sink": ("filesink", "file-sink")
    }

    # Instance and check elements
    for name, val in elements.items():
        element = Gst.ElementFactory.make(val[0], val[1])
        if not element:
            sys.stderr.write(f"Unable to create {name}\n")
            return None
        elements[name] = element

    # Set properties
    elements["source"].set_property('location', input_file)
    elements["sink"].set_property('location', output_file)
    elements["encoder"].set_property('bitrate', 2000000)
    elements["cap_filter"].set_property('caps', Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))

    if os.environ.get('USE_NEW_NVSTREAMMUX') != 'yes':
        elements["streammux"].set_property('width', 1920)
        elements["streammux"].set_property('height', 1080)
        elements["streammux"].set_property('batched-push-timeout', MUXER_BATCH_TIMEOUT_USEC)
    elements["streammux"].set_property('batch-size', 1)
    elements["pgie"].set_property('config-file-path', "config_pgie_yolo_det.txt")

    # Add elements to pipeline
    for element in elements.values():
        pipeline.add(element)

    # Link elements together
    elements["source"].link(elements["h264parser"])
    elements["h264parser"].link(elements["decoder"])

    sinkpad = elements["streammux"].get_request_pad("sink_0")
    if not sinkpad:
        sys.stderr.write("Unable to get the sink pad of streammux\n")
        return None

    srcpad = elements["decoder"].get_static_pad("src")
    if not srcpad:
        sys.stderr.write("Unable to get source pad of decoder\n")
        return None

    srcpad.link(sinkpad)
    elements["streammux"].link(elements["pgie"])
    elements["pgie"].link(elements["nvvidconv"])
    elements["nvvidconv"].link(elements["nvosd"])
    elements["nvosd"].link(elements["nvvidconv2"])
    elements["nvvidconv2"].link(elements["cap_filter"])
    elements["cap_filter"].link(elements["encoder"])
    elements["encoder"].link(elements["codeparser"])
    elements["codeparser"].link(elements["container"])
    elements["container"].link(elements["sink"])

    return pipeline

def run_pipeline(input_file, output_file):
    pipeline = create_pipeline(input_file, output_file)

    if not pipeline:
        sys.stderr.write("Failed to create pipeline\n")
        return

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Add probe to get metadata
    nvosd = pipeline.get_by_name("onscreendisplay")
    osdsinkpad = nvosd.get_static_pad("sink")
    if not osdsinkpad:
        sys.stderr.write("Unable to get sink pad of nvosd\n")
        return
    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    # Start playback and listen to events
    print("Starting pipeline \n")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except:
        pass

    # Clean up
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input media file> <output media file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    run_pipeline(input_file, output_file)