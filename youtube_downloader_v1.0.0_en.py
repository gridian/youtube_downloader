"""
YouTube Downloader
=================

This is a desktop application for downloading YouTube videos and extracting subtitles.
It provides a GUI environment for convenient downloading of videos, subtitles, and audio.

Copyright (c) 2025 Knowledge Explorer (https://small-tip.co.kr)
All rights reserved.

License:
--------
This program is free software.
It is distributed under the GNU General Public License v3.0.
Anyone can use, copy, modify, and distribute this program.
For more details, please refer to the LICENSE file.

External Libraries Used:
---------------------
1. pytube (MIT License)
   - YouTube video information extraction
   - https://github.com/pytube/pytube
   
2. youtube_transcript_api (MIT License)
   - YouTube subtitle extraction
   - https://github.com/jdepoix/youtube-transcript-api

3. yt-dlp (The Unlicense)
   - High-quality video/audio download
   - https://github.com/yt-dlp/yt-dlp

4. FFmpeg (LGPL 2.1+ License)
   - Media file processing
   - https://ffmpeg.org/

Key Features:
-----------
1. High-quality video download (up to 4K/2160p)
2. Subtitle download (txt/srt format)
3. Audio extraction (mp3 format)
4. Multi-language subtitle support
5. Real-time progress display
6. Custom filename support
7. Download path persistence

Developer: MJ (Knowledge Explorer)
Version: 1.0.0
Last Modified: 2025-02-20
"""

import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import yt_dlp
import os
import json
from datetime import datetime

# Define configuration file path
CONFIG_FILE = 'youtube_downloader_config.json'

class DownloadStatus(tk.Frame):
    """Progress display component class
    
    This class is a UI component that visually displays download progress.
    It includes a label, progress bar, and percentage display.
    
    Attributes:
        label (ttk.Label): Download type label (Subtitle/Video/Audio)
        progress (ttk.Progressbar): Progress bar
        percent_label (ttk.Label): Percentage display
    """
    
    def __init__(self, parent, label, progress_var):
        """
        Args:
            parent: Parent widget
            label (str): Progress bar label
            progress_var (tk.DoubleVar): Variable storing progress value
        """
        super().__init__(parent)
        self.columnconfigure(1, weight=1)
        
        # Create label
        self.label = ttk.Label(self, text=label, width=10)
        self.label.grid(row=0, column=0, padx=(0, 5))
        
        # Create progress bar
        self.progress = ttk.Progressbar(self, variable=progress_var, maximum=100)
        self.progress.grid(row=0, column=1, sticky='ew', padx=(0, 5))
        
        # Create percentage label
        self.percent_label = ttk.Label(self, text="0%", width=5, anchor='e')
        self.percent_label.grid(row=0, column=2)
        
        # Update percentage display when progress value changes
        progress_var.trace('w', lambda *args: self.update_percent(progress_var.get()))
        
    def update_percent(self, value):
        """Updates the progress percentage value.
        
        Args:
            value (float): Current progress value (0-100)
        """
        self.percent_label.configure(text=f"{int(value)}%")

class YouTubeDownloader(tk.Tk):
    """YouTube Downloader main application class
    
    This class is the main window containing all major functionality.
    It provides YouTube video download, subtitle extraction, and audio extraction.
    
    Attributes:
        download_path (tk.StringVar): Download path
        video_check (tk.BooleanVar): Video download checkbox state
        sub_check (tk.BooleanVar): Subtitle download checkbox state
        srt_check (tk.BooleanVar): SRT format usage state
        audio_check (tk.BooleanVar): Audio download checkbox state
        resolution_var (tk.StringVar): Selected resolution
        title_var (tk.StringVar): Custom filename
    """
    
    def __init__(self):
        """Initialize YouTubeDownloader class"""
        super().__init__()
        self.title("YouTube Downloader v1.0.0")
        self.geometry("600x324")
        
        self.padding = 20
        main_frame = ttk.Frame(self, padding=self.padding)
        main_frame.pack(fill='both', expand=True)
        
        self.setup_variables()
        self.create_widgets(main_frame)
        
        # Save settings on program exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_config(self):
        """Load download path from configuration file.
        
        Returns:
            str: Saved download path or default downloads folder path
        """
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('download_path', os.path.expanduser("~/Downloads"))
        except Exception as e:
            print(f"Error loading configuration file: {e}")
        return os.path.expanduser("~/Downloads")
        
    def save_config(self):
        """Save current download path to configuration file."""
        try:
            config = {
                'download_path': self.download_path.get()
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving configuration file: {e}")
            
    def on_closing(self):
        """Save settings and exit program."""
        self.save_config()
        self.quit()
        
    def setup_variables(self):
        """Initialize program variables."""
        self.download_path = tk.StringVar(value=self.load_config())
        self.video_check = tk.BooleanVar(value=True)
        self.sub_check = tk.BooleanVar(value=True)
        self.srt_check = tk.BooleanVar()
        self.audio_check = tk.BooleanVar()
        self.resolution_var = tk.StringVar(value='2160p')
        self.title_var = tk.StringVar()
        
        self.caption_progress_var = tk.DoubleVar()
        self.video_progress_var = tk.DoubleVar()
        self.audio_progress_var = tk.DoubleVar()
        
    def create_widgets(self, parent):
        """Create and arrange UI widgets.
        
        Args:
            parent: Parent frame for widgets
        """
        # URL input frame
        url_frame = ttk.Frame(parent)
        url_frame.pack(fill='x', pady=(0, 5))
        url_frame.columnconfigure(1, weight=1)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, padx=(0, 5))
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.grid(row=0, column=1, sticky='ew')
        self.url_entry.focus_set()
        
        path_button = ttk.Button(url_frame, text="Save Path", command=self.select_download_path)
        path_button.grid(row=0, column=2, padx=5)
        
        start_button = ttk.Button(url_frame, text="Start Download", command=self.start_download)
        start_button.grid(row=0, column=3)
        
        # Title input frame
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill='x', pady=(0, 5))
        title_frame.columnconfigure(1, weight=1)
        
        ttk.Label(title_frame, text="Title:").grid(row=0, column=0, padx=(0, 5))
        title_entry = ttk.Entry(title_frame, textvariable=self.title_var)
        title_entry.grid(row=0, column=1, columnspan=3, sticky='ew')
        
        # Current download path display
        path_frame = ttk.Frame(parent)
        path_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(path_frame, text="Save Path:").pack(side='left')
        ttk.Label(path_frame, textvariable=self.download_path).pack(side='left', padx=(5, 0))
        
        # Options frame
        options_frame = ttk.Frame(parent)
        options_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Checkbutton(options_frame, text="Video", variable=self.video_check).pack(side='left', padx=5)
        ttk.Combobox(options_frame, textvariable=self.resolution_var, 
                    values=["2160p", "1080p", "720p"]).pack(side='left', padx=5)
        ttk.Checkbutton(options_frame, text="Subtitle", variable=self.sub_check).pack(side='left', padx=5)
        ttk.Checkbutton(options_frame, text="Audio", variable=self.audio_check).pack(side='left', padx=5)
        
        # Status frame
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(0, 20))
        
        self.caption_status = DownloadStatus(status_frame, "Subtitle", self.caption_progress_var)
        self.caption_status.pack(fill='x', pady=2)
        
        self.video_status = DownloadStatus(status_frame, "Video", self.video_progress_var)
        self.video_status.pack(fill='x', pady=2)
        
        self.audio_status = DownloadStatus(status_frame, "Audio", self.audio_progress_var)
        self.audio_status.pack(fill='x', pady=2)
        
        # Completion status message
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(5, 5))
        self.status_label = ttk.Label(status_frame, text="")
        self.status_label.pack(side='right')
        
        # Bottom frame
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill='x', pady=(5, 0))
        
        copyright_label = ttk.Label(
            bottom_frame, 
            text="© 2025 Knowledge Explorer (https://small-tip.co.kr) - All Rights Reserved",
            cursor="hand2"
        )
        copyright_label.pack(side='left')
        copyright_label.bind("<Button-1>", lambda e: self.open_website())
        
        exit_button = ttk.Button(bottom_frame, text="Exit", command=self.on_closing)
        exit_button.pack(side='right')

    def open_website(self):
        """Opens the copyright information website link."""
        import webbrowser
        webbrowser.open("https://small-tip.co.kr")

    def get_safe_filename(self, url, video_id):
        """Generate a safe filename.
        
        Determines filename in the following priority:
        1. User-entered title
        2. Original YouTube video title
        3. Auto-generated name with date_time format
        
        Args:
            url (str): YouTube video URL
            video_id (str): YouTube video ID
            
        Returns:
            str: Filename to use
        """
        if self.title_var.get().strip():
            return self.title_var.get().strip()
        
        try:
            yt = YouTube(url)
            return yt.title
        except:
            current_time = datetime.now().strftime('%y%m%d_%H%M')
            return f"download_{current_time}"

    def extract_percent(self, percent_str):
        """Extract number from progress string.
        
        Removes ANSI color codes and other characters to extract number.
        
        Args:
            percent_str (str): Progress string
            
        Returns:
            float: Extracted progress value (0-100)
        """
        clean_str = re.sub(r'\x1b\[[0-9;]*m', '', percent_str)
        clean_str = re.sub(r'[^\d.]', '', clean_str)
        try:
            return float(clean_str)
        except ValueError:
            return 0.0

    def format_time(self, seconds):
        """Convert seconds to subtitle time format.
        
        Converts to SRT time format (HH:MM:SS,mmm).
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Converted time string (HH:MM:SS,mmm format)
        """
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"

    def progress_hook(self, mode):
        """Returns callback function for download progress updates.
        
        Used in yt-dlp's progress_hooks to reflect download progress
        in real-time on the UI.
        
        Args:
            mode (str): Download mode ('video' or 'audio')
            
        Returns:
            function: Progress update callback function
        """
        def hook(d):
            if d['status'] == 'downloading':
                percent = self.extract_percent(d['_percent_str'])
                if mode == 'video':
                    self.video_progress_var.set(percent)
                elif mode == 'audio':
                    self.audio_progress_var.set(percent)
            elif d['status'] == 'finished':
                if mode == 'video':
                    self.video_progress_var.set(100)
                elif mode == 'audio':
                    self.audio_progress_var.set(100)
        return hook

    def download_caption(self, video_id, url, safe_title, is_srt):
        """Download and save subtitles.
        
        Downloads YouTube video subtitles and saves in TXT or SRT format.
        Prioritizes Korean, English, Japanese subtitles, and falls back to
        auto-generated subtitles if needed.
        
        Args:
            video_id (str): YouTube video ID
            url (str): YouTube video URL
            safe_title (str): Filename to save as
            is_srt (bool): True for SRT format, False for TXT format
        """
        try:
            available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

            transcript = None
            try:
                transcript = available_transcripts.find_transcript(['ko', 'en', 'ja'])
            except NoTranscriptFound:
                try:
                    transcript = available_transcripts.find_generated_transcript(['ja', 'en'])
                except:
                    transcript = next(iter(available_transcripts), None)

            if transcript is None:
                raise NoTranscriptFound("No available subtitles found.")

            if transcript.is_translatable:
                transcript = transcript.translate('en')

            transcript_data = transcript.fetch()
            file_ext = 'srt' if is_srt else 'txt'
            file_path = os.path.join(self.download_path.get(), f"{safe_title}.{file_ext}")

            with open(file_path, 'w', encoding='utf-8') as file:
                if is_srt:
                    for i, entry in enumerate(transcript_data):
                        start = entry['start']
                        duration = entry.get('duration', 0)
                        end = start + duration
                        text = entry['text'].replace('\n', ' ')
                        file.write(f"{i + 1}\n{self.format_time(start)} --> {self.format_time(end)}\n{text}\n\n")
                else:
                    for entry in transcript_data:
                        file.write(entry['text'] + '\n')

            self.caption_progress_var.set(100)

        except Exception as e:
            self.update_status(f"Subtitle download failed: {str(e)}")

    def download_video_audio(self, url, safe_title, mode):
        """Download video or audio.
        
        Uses yt-dlp to download high-quality video or audio content.
        
        Args:
            url (str): YouTube video URL
            safe_title (str): Filename to save as
            mode (str): Download mode ('video' or 'audio')
        """
        file_ext = 'mp4' if mode == 'video' else 'mp3'
        resolution = self.resolution_var.get().replace('p', '')

        ffmpeg_path = 'C:/ffmpeg/bin'

        ydl_opts = {
            'format': f"bv*[height<={resolution}]+ba/b[height<={resolution}]" if mode == 'video' else 'bestaudio/best',
            'outtmpl': os.path.join(self.download_path.get(), f"{safe_title}.{file_ext}"),
            'merge_output_format': file_ext,
            'ffmpeg_location': ffmpeg_path,
            'progress_hooks': [self.progress_hook(mode)],
            'no_color': True,
            'noprogress': True,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def select_download_path(self):
        """Select download path and save settings."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.download_path.set(folder_selected)
            self.save_config()
            
    def update_status(self, message):
        """Update status message.
        
        Args:
            message (str): Status message to display
        """
        self.status_label.config(text=message)
            
    def start_download(self):
        """Start download process.
        
        Asynchronously executes video, subtitle, and audio downloads
        based on user-selected options.
        """
        url = self.url_entry.get()
        if not url:
            self.update_status("Please enter a URL.")
            return
            
        video_id = url.split("v=")[-1].split("&")[0]
        safe_title = self.get_safe_filename(url, video_id)
        
        tasks = []
        if self.sub_check.get():
            tasks.append(lambda: self.download_caption(video_id, url, safe_title, self.srt_check.get()))
        if self.video_check.get():
            tasks.append(lambda: self.download_video_audio(url, safe_title, 'video'))
        if self.audio_check.get():
            tasks.append(lambda: self.download_video_audio(url, safe_title, 'audio'))
            
        if not tasks:
            self.update_status("Please select download options.")
            return
            
        def run_tasks():
            try:
                for task in tasks:
                    task()
                self.update_status("All downloads completed!")
            except Exception as e:
                self.update_status(f"Error occurred: {str(e)}")
                
        threading.Thread(target=run_tasks, daemon=True).start()

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()