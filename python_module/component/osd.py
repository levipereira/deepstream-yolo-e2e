from collections import namedtuple
from operator import attrgetter
import gi
import pyds
import random
gi.require_version("Gst", "1.0")
from gi.repository import Gst




past_tracking_meta = [0]

MetaObject = namedtuple(
    "MetaObject",
    ["left", "top", "height", "width", "area", "bottom", "id", "text", "class_id"],
)

ColorObject = namedtuple("ColorObject", ["red", "green", "blue", "alpha"])

def create_dynamic_labels(config_path):
    """Create dynamic colors for labels based on the label file path specified in the config."""
    
    # Load label file path from the configuration
    label_file_path = None
    with open(config_path, 'r') as file:
        for line in file:
            if line.startswith("labelfile-path="):
                label_file_path = line.strip().split('=')[1]
                break

    # Load labels from the label file
    labels = []
    with open(label_file_path, 'r') as file:
        labels = [line.strip() for line in file if line.strip()]

    # Generate random colors for each label ID (index)
    dynamic_labels = {}
    for idx, label in enumerate(labels):
        dynamic_labels[idx] = ColorObject(
            red=random.random(),
            green=random.random(),
            blue=random.random(),
            alpha=1.0  # Alpha is set to 1 for full opacity
        )

    return dynamic_labels

def osd_sink_pad_buffer_probe(pad, info, u_data, dynamic_labels ):
    frame_number = 0
    num_rects = 0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list
    meta_list = []

    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number = frame_meta.frame_num
        num_rects = frame_meta.num_obj_meta
        l_obj = frame_meta.obj_meta_list

        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            obj = MetaObject(
                left=obj_meta.tracker_bbox_info.org_bbox_coords.left,
                top=obj_meta.tracker_bbox_info.org_bbox_coords.top,
                height=obj_meta.tracker_bbox_info.org_bbox_coords.height,
                width=obj_meta.tracker_bbox_info.org_bbox_coords.width,
                area=obj_meta.tracker_bbox_info.org_bbox_coords.height
                * obj_meta.tracker_bbox_info.org_bbox_coords.width,
                bottom=obj_meta.tracker_bbox_info.org_bbox_coords.top
                + obj_meta.tracker_bbox_info.org_bbox_coords.height,
                id=obj_meta.object_id,
                text=f"ID: {obj_meta.object_id:04d}, Class: {pyds.get_string(obj_meta.text_params.display_text)}",
                class_id=obj_meta.class_id,
            )
            meta_list.append(obj)

            obj_meta.text_params.display_text = ""
            obj_meta.text_params.set_bg_clr = 0
            obj_meta.rect_params.border_width = 0

            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        meta_list_sorted = sorted(meta_list, key=attrgetter("bottom"))
        max_labels = 10  # Define a suitable number for max_labels
        num_objects = len(meta_list_sorted)
        num_meta_objects = (num_objects + max_labels - 1) // max_labels

        # Create a single display_meta for the frame counter and object counts
        display_meta_main = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta_main.num_labels = 1
        py_nvosd_text_params = display_meta_main.text_params[0]
        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 10
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
        py_nvosd_text_params.set_bg_clr = 1
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta_main)

        for i in range(num_meta_objects):
            display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            display_meta.num_labels = 0

            start_idx = i * max_labels
            end_idx = min((i + 1) * max_labels, num_objects)

            for j, idx in enumerate(range(start_idx, end_idx)):
                x = int(meta_list_sorted[idx].left)
                y = int(meta_list_sorted[idx].top) - 15

                if x < 0 or y < 0:
                    continue

                display_meta.text_params[
                    display_meta.num_labels
                ].display_text = meta_list_sorted[idx].text
                display_meta.text_params[display_meta.num_labels].x_offset = x
                display_meta.text_params[display_meta.num_labels].y_offset = y
                display_meta.text_params[
                    display_meta.num_labels
                ].font_params.font_name = "Serif"
                display_meta.text_params[
                    display_meta.num_labels
                ].font_params.font_size = 10
                display_meta.text_params[
                    display_meta.num_labels
                ].font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
                display_meta.text_params[display_meta.num_labels].set_bg_clr = 1
                display_meta.text_params[display_meta.num_labels].text_bg_clr.set(
                    0.45, 0.20, 0.50, 0.75
                )
                display_meta.num_labels += 1

            display_meta.num_rects = end_idx - start_idx
 

            for j, idx in enumerate(range(start_idx, end_idx)):
                class_id = meta_list_sorted[idx]['class_id']
                color = dynamic_labels.get(class_id)
                red = color.red
                green = color.green
                blue = color.blue
                alpha = color.alpha


                display_meta.rect_params[j].left = meta_list_sorted[idx].left
                display_meta.rect_params[j].top = meta_list_sorted[idx].top
                display_meta.rect_params[j].width = meta_list_sorted[idx].width
                display_meta.rect_params[j].height = meta_list_sorted[idx].height
                display_meta.rect_params[j].border_width = 2
                display_meta.rect_params[j].border_color.red = red
                display_meta.rect_params[j].border_color.green = green
                display_meta.rect_params[j].border_color.blue = blue
                display_meta.rect_params[j].border_color.alpha = alpha
                display_meta.rect_params[j].has_bg_color = 0

            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    # Past tracking meta data
    if past_tracking_meta[0] == 1:
        l_user = batch_meta.batch_user_meta_list
        while l_user is not None:
            try:
                user_meta = pyds.NvDsUserMeta.cast(l_user.data)
            except StopIteration:
                break
            if (
                user_meta
                and user_meta.base_meta.meta_type
                == pyds.NvDsMetaType.NVDS_TRACKER_PAST_FRAME_META
            ):
                try:
                    pPastFrameObjBatch = pyds.NvDsPastFrameObjBatch.cast(
                        user_meta.user_meta_data
                    )
                except StopIteration:
                    break
                for trackobj in pyds.NvDsPastFrameObjBatch.list(pPastFrameObjBatch):
                    print("streamId=", trackobj.streamID)
                    print("surfaceStreamID=", trackobj.surfaceStreamID)
                    for pastframeobj in pyds.NvDsPastFrameObjStream.list(trackobj):
                        print("numobj=", pastframeobj.numObj)
                        print("uniqueId=", pastframeobj.uniqueId)
                        print("classId=", pastframeobj.classId)
                        print("objLabel=", pastframeobj.objLabel)
                        for objlist in pyds.NvDsPastFrameObjList.list(pastframeobj):
                            print("frameNum:", objlist.frameNum)
                            print("tBbox.left:", objlist.tBbox.left)
                            print("tBbox.width:", objlist.tBbox.width)
                            print("tBbox.top:", objlist.tBbox.top)
                            print("tBbox.right:", objlist.tBbox.height)
                            print("confidence:", objlist.confidence)
                            print("age:", objlist.age)
            try:
                l_user = l_user.next
            except StopIteration:
                break

    return Gst.PadProbeReturn.OK
