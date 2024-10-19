import configparser
import gi
gi.require_version("GstRtspServer", "1.0")
from gi.repository import GstRtspServer, GstRtsp

config = configparser.ConfigParser()
config.read('config/config.ini')


RTSP_PORT = config.getint('Settings', 'RTSP_PORT')
RTSP_UDPSYNC = config.getint('Settings', 'RTSP_UDPSYNC')
RTSP_FACTORY = config.get('Settings', 'RTSP_FACTORY')
 
 

def create_rtsp_server():
    rtsp_port_num = RTSP_PORT
    rtsp_stream_end = RTSP_FACTORY
    updsink_port_num = RTSP_UDPSYNC
    codec = 'H264'

    server = GstRtspServer.RTSPServer.new()
    auth = GstRtspServer.RTSPAuth()

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
    
    server.get_mount_points().add_factory(rtsp_stream_end, factory)
    print("\n *** DeepStream: Launched RTSP Streaming at rtsp://%s:%d%s ***\n\n" %
        ('localhost', rtsp_port_num, rtsp_stream_end))