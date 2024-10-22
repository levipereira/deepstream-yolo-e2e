import pyds
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Function for probe to extract metadata
def sink_pad_buffer_probe(pad, info, u_data, perf_data):
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
        perf_data.update_fps(stream_index)

        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK