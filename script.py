import tkinter as tk
from tkinter import messagebox, ttk
import requests
import threading

def download_streamable_video(video_code, status_label, custom_title):
    try:
        status_label.config(text="Downloading metadata...")
        api_url = f"https://api.streamable.com/videos/{video_code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(api_url, headers=headers)
        if r.status_code != 200:
            raise Exception(f"HTTP error: {r.status_code}")

        data = r.json()
        files = data.get('files', {})
        preferred_order = ['mp4', 'mp4-mobile', 'original']
        video_url = None
        for key in preferred_order:
            file_data = files.get(key)
            if file_data and file_data.get('url'):
                video_url = file_data['url']
                break

        if not video_url:
            raise Exception("Video file not found.")

        if not video_url.startswith("http"):
            video_url = "https:" + video_url

        status_label.config(text="Downloading video file...")
        video_data = requests.get(video_url, stream=True)
        if video_data.status_code != 200:
            raise Exception("Error downloading video file.")

        total_length = video_data.headers.get('content-length')
        if total_length is None:
            root.after(0, lambda: progress.config(mode='indeterminate'))
            root.after(0, progress.start)
        else:
            total_length = int(total_length)
            root.after(0, lambda: progress.config(mode='determinate', maximum=total_length))
            root.after(0, lambda: progress.stop())
            root.after(0, lambda: progress.config(value=0))

        # Set the file name
        if custom_title.strip():
            filename = custom_title.strip()
            if not filename.lower().endswith('.mp4'):
                filename += '.mp4'
        else:
            filename = f"{video_code}.mp4"

        downloaded = 0
        with open(filename, 'wb') as f:
            for chunk in video_data.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_length is not None:
                        root.after(0, lambda val=downloaded: progress.config(value=val))
                        root.update_idletasks()

        status_label.config(text=f"Downloaded and saved: {filename}")
        root.after(0, lambda: download_btn.config(state='normal'))
        root.after(0, lambda: progress.stop())
        root.after(0, lambda: progress.pack_forget())

    except Exception as e:
        status_label.config(text="Error!")
        root.after(0, lambda: download_btn.config(state='normal'))
        root.after(0, lambda: progress.stop())
        root.after(0, lambda: progress.pack_forget())
        messagebox.showerror("Error", str(e))

def on_download_click():
    url = url_entry.get().strip()
    custom_title = title_entry.get().strip()
    if not url:
        messagebox.showwarning("Warning", "Please enter a Streamable video link")
        return

    if '/' in url:
        video_code = url.rstrip('/').split('/')[-1]
    else:
        video_code = url

    download_btn.config(state='disabled')
    progress.config(value=0, mode='determinate')
    progress.pack(padx=10, pady=5)
    threading.Thread(target=download_streamable_video, args=(video_code, status_label, custom_title), daemon=True).start()

# --- GUI ---
root = tk.Tk()
root.title("Streamable Downloader")

tk.Label(root, text="Paste the Streamable video link:").pack(padx=10, pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.pack(padx=10, pady=5)
url_entry.focus()

tk.Label(root, text="Optional: Enter a custom title for the downloaded video:").pack(padx=10, pady=5)
title_entry = tk.Entry(root, width=50)
title_entry.pack(padx=10, pady=5)

download_btn = tk.Button(root, text="Download", command=on_download_click)
download_btn.pack(padx=10, pady=10)

status_label = tk.Label(root, text="")
status_label.pack(padx=10, pady=5)

progress = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate')

root.mainloop()
