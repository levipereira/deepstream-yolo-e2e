import sys
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib


def bus_call(bus, message, loop):
    msg_type = message.type
    if msg_type == Gst.MessageType.EOS:
        print("End-of-stream")
        loop.quit()
    elif msg_type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"Error: {err}, {debug}")
        loop.quit()
    return True


def create_pipeline(input_file, output_file):
    Gst.init(None)

    # Create GStreamer elements
    pipeline = Gst.Pipeline()

    source = Gst.ElementFactory.make("filesrc", "file-source")
    h264parser = Gst.ElementFactory.make("h264parse", "h264-parser")
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "nvvideo-converter")
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    nvvidconv2 = Gst.ElementFactory.make("nvvideoconvert", "nvvideo-converter2")
    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
    codeparser = Gst.ElementFactory.make("h264parse", "h264-parser2")
    container = Gst.ElementFactory.make("qtmux", "qtmux")
    sink = Gst.ElementFactory.make("filesink", "file-sink")

    if not pipeline or not source or not h264parser or not decoder or not streammux or not pgie or not nvvidconv or not nvosd or not nvvidconv2 or not encoder or not codeparser or not container or not sink:
        print("Unable to create GStreamer elements")
        return None

    # Set properties
    source.set_property('location', input_file)
    sink.set_property('location', output_file)
    streammux.set_property('batch-size', 1)
    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)
    streammux.set_property('batched-push-timeout', 40000)
    pgie.set_property('config-file-path', "config_infer_primary.txt")

    # Add elements to pipeline
    pipeline.add(source)
    pipeline.add(h264parser)
    pipeline.add(decoder)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(nvvidconv2)
    pipeline.add(encoder)
    pipeline.add(codeparser)
    pipeline.add(container)
    pipeline.add(sink)

    # Link elements
    source.link(h264parser)
    h264parser.link(decoder)
    decoder_sinkpad = streammux.get_request_pad("sink_0")
    decoder_srcpad = decoder.get_static_pad("src")
    if not decoder_sinkpad or not decoder_srcpad:
        print("Unable to get source or sink pad")
        return None

    decoder_srcpad.link(decoder_sinkpad)
    streammux.link(pgie)
    pgie.link(nvvidconv)
    nvvidconv.link(nvosd)
    nvosd.link(nvvidconv2)
    nvvidconv2.link(encoder)
    encoder.link(codeparser)
    codeparser.link(container)
    container.link(sink)

    return pipeline


def main(input_file, output_file):
    pipeline = create_pipeline(input_file, output_file)
    if not pipeline:
        print("Failed to create pipeline")
        return

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except:
        pass

    # Cleanup
    pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input file> <output file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file, output_file)
