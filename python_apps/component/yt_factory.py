import yt_dlp  # type: ignore

def format_selector(ctx, resolution, fps):
    # formats are already sorted worst to best
    formats = ctx.get('formats')[::-1]

    # Try to find the best video with the given resolution and fps
    best_video = next((f for f in formats
                       if f['vcodec'] != 'none' 
                       and f['acodec'] == 'none'
                       and f.get('height') is not None
                       and f['height'] == resolution
                       and f.get('fps') is not None
                       and f['fps'] == fps), None)
    
    # If not found, try with 1080p and 30fps
    if best_video is None:
        best_video = next((f for f in formats
                           if f['vcodec'] != 'none' 
                           and f['acodec'] == 'none'
                           and f.get('height') is not None
                           and f['height'] <= 1080
                           and f.get('fps') is not None
                           and f['fps'] <= 30), None)
        print("No suitable format found for the given resolution and fps. Using 1080p and 30fps")
    if best_video is None:
        return  # No suitable format found

    # These are the minimum required fields for a merged format
    print(f"Running at {best_video['height']}p and {best_video['fps']}fps")

    yield {
        'format_id': f'{best_video["format_id"]}',
        'ext': best_video['ext'],
        'requested_formats': [best_video],
        # Must be + separated list of protocols
        'protocol': f'{best_video["protocol"]}'
    }

def get_yt_uri(url, resolution, fps):
    ydl_opts = {
        'format': lambda ctx: format_selector(ctx, resolution, fps),  
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        requested_formats = info.get('requested_formats', [])
        uri = requested_formats[0].get('url') if requested_formats else None
    return uri