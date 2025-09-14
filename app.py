def download_audio(url: str) -> str:
    output_dir = r"C:\Users\Admin\Downloads\transcriber-app-main\transcriber-app-main\Downloads"
    os.makedirs(output_dir, exist_ok=True)

    filepath = None

    def download_hook(d):
        nonlocal filepath
        if d['status'] == 'finished':
            filepath = os.path.join(output_dir, f"{d['info_dict']['id']}.mp3")

    ydl_opts = {
        'format': 'bestaudio/best',
        'cookiefile': 'cookies.txt',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.60',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'progress_hooks': [download_hook],
        'verbose': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if not filepath:
        raise Exception("Audio file download failed.")

    return filepath
