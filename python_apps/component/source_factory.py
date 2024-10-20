import sys
import gi # type: ignore
import os
import configparser
from component.yt_factory import get_yt_uri
from common.constants import *

gi.require_version('Gst', '1.0')
from gi.repository import Gst # type: ignore


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
#    if "souphttpsrc" in name:
#        Object.set_property("user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")

 
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

def parse_media_source(media_config_file, resolution=1080):
    # Read media configuration
    media_config = configparser.ConfigParser()
    media_config.read(media_config_file)
    
    # Read streammux configuration
    streammux_config = configparser.ConfigParser()
    streammux_config.read(CONFIG_NEW_STREAMMUX_PATH)
    
    media_entries = []
    source_count = 0
    max_fps = 0
    
    for section in media_config.sections():
        enable = media_config.getint(section, 'enable', fallback=0)
        if enable == 1:
            type = media_config.get(section, 'type')
            url = media_config.get(section, 'url')
            uri = url
            resolution = media_config.getint(section, 'resolution', fallback=1080)
            fps = media_config.getfloat(section, 'fps', fallback=30.0)
            
            if not os.path.isfile(url) and type == 'file':
                print(f"File not found: {url}")
            if type == "file":
                uri = f"file://{url}"
            if type == 'youtube':
                uri = get_yt_uri(url, resolution, fps)
            media_entries.append((type, url, uri))
            
            # Update or add source-config section in streammux config
            source_section = f'source-config-{source_count}'
            if not streammux_config.has_section(source_section):
                streammux_config.add_section(source_section)
            
            # Update max-fps-n and max-fps-d
            streammux_config[source_section]['max-fps-n'] = str(int(fps))
            streammux_config[source_section]['max-fps-d'] = '1'
            
            # Update max_fps if this source has a higher fps
            max_fps = max(max_fps, fps)
            
            source_count += 1
    
    # Update overall-max-fps-n in the [property] section if it exists
    if 'property' in streammux_config:
        streammux_config['property']['overall-max-fps-n'] = str(int(max_fps))
    
    # Write the updated configuration back to the streammux config file
    with open(CONFIG_NEW_STREAMMUX_PATH, 'w') as configfile:
        streammux_config.write(configfile)
    
    return media_entries

def float_to_fraction(x, error=0.000001):
    n = int(x)
    x -= n
    if x < error:
        return n, 1
    elif 1 - error < x:
        return n+1, 1
    
    # The lower fraction is 0/1
    lower_n, lower_d = 0, 1
    # The upper fraction is 1/1
    upper_n, upper_d = 1, 1
    while True:
        # The middle fraction is (lower_n + upper_n) / (lower_d + upper_d)
        middle_n = lower_n + upper_n
        middle_d = lower_d + upper_d
        # If x + error < middle
        if middle_d * (x + error) < middle_n:
            # middle is our new upper
            upper_n, upper_d = middle_n, middle_d
        # Else If middle < x - error
        elif middle_n < (x - error) * middle_d:
            # middle is our new lower
            lower_n, lower_d = middle_n, middle_d
        # Else middle is our best fraction
        else:
            return n * middle_d + middle_n, middle_d

# Example usage:
# parse_media_source('media.ini', 'new_streammux_config.txt')