"""
YouTube Downloader
=================

이 프로그램은 YouTube 동영상을 다운로드하고 자막을 추출할 수 있는 데스크톱 애플리케이션입니다.
GUI 환경에서 YouTube 영상, 자막, 음성을 편리하게 다운로드할 수 있습니다.

Copyright (c) 2025 지식에 대한 탐구 (https://small-tip.co.kr)
All rights reserved.

라이선스:
--------
이 프로그램은 자유 소프트웨어입니다.
GNU General Public License v3.0에 따라 배포됩니다.
누구나 이 프로그램을 사용, 복사, 수정, 배포할 수 있습니다.
자세한 내용은 LICENSE 파일을 참조하세요.

사용된 외부 라이브러리:
-------------------
1. pytube (MIT License)
   - YouTube 영상 정보 추출
   - https://github.com/pytube/pytube
   
2. youtube_transcript_api (MIT License)
   - YouTube 자막 추출
   - https://github.com/jdepoix/youtube-transcript-api

3. yt-dlp (The Unlicense)
   - 고품질 영상/음성 다운로드
   - https://github.com/yt-dlp/yt-dlp

4. FFmpeg (LGPL 2.1+ License)
   - 미디어 파일 처리
   - https://ffmpeg.org/

주요 기능:
--------
1. 고화질 영상 다운로드 (최대 4K/2160p)
2. 자막 다운로드 (txt/srt 형식)
3. 음성 추출 (mp3 형식)
4. 다국어 자막 지원
5. 진행률 실시간 표시
6. 사용자 지정 파일명
7. 다운로드 경로 저장

개발자: MJ (지식에 대한 탐구)
버전: 1.0.0
최종 수정일: 2025-02-20
"""

import re
import sys
import os
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import yt_dlp
from datetime import datetime

# ctypes 모듈 import
if sys.platform == 'win32':
    import ctypes

# Windows에서 콘솔 창이 보이지 않도록 설정
try:  
    if sys.platform == 'win32':
        # Windows에서 콘솔 창이 보이지 않도록 설정
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)
except Exception:
    pass  # 오류가 발생해도 계속 실행

# 설정 파일 경로 정의
CONFIG_FILE = 'youtube_downloader_config.json'

class DownloadStatus(tk.Frame):
    """진행률 표시 컴포넌트 클래스
    
    이 클래스는 다운로드 진행 상태를 시각적으로 표시하는 UI 컴포넌트입니다.
    레이블, 진행률 바, 퍼센트 표시를 포함합니다.
    
    Attributes:
        label (ttk.Label): 다운로드 유형 레이블 (자막/영상/음성)
        progress (ttk.Progressbar): 진행률 표시 바
        percent_label (ttk.Label): 진행률 퍼센트 표시
    """
    
    def __init__(self, parent, label, progress_var):
        """
        Args:
            parent: 부모 위젯
            label (str): 진행률 바 레이블
            progress_var (tk.DoubleVar): 진행률 값을 저장하는 변수
        """
        super().__init__(parent)
        self.columnconfigure(1, weight=1)
        
        # 레이블 생성
        self.label = ttk.Label(self, text=label, width=10)
        self.label.grid(row=0, column=0, padx=(0, 5))
        
        # 진행률 바 생성
        self.progress = ttk.Progressbar(self, variable=progress_var, maximum=100)
        self.progress.grid(row=0, column=1, sticky='ew', padx=(0, 5))
        
        # 퍼센트 레이블 생성
        self.percent_label = ttk.Label(self, text="0%", width=5, anchor='e')
        self.percent_label.grid(row=0, column=2)
        
        # 진행률 값 변경 시 퍼센트 표시 업데이트
        progress_var.trace('w', lambda *args: self.update_percent(progress_var.get()))
        
    def update_percent(self, value):
        """진행률 퍼센트 값을 업데이트합니다.
        
        Args:
            value (float): 현재 진행률 값 (0-100)
        """
        self.percent_label.configure(text=f"{int(value)}%")

class YouTubeDownloader(tk.Tk):
    """YouTube 다운로더 메인 애플리케이션 클래스
    
    이 클래스는 프로그램의 주요 기능을 모두 포함하는 메인 윈도우입니다.
    YouTube 영상의 다운로드, 자막 추출, 음성 추출 기능을 제공합니다.
    
    Attributes:
        download_path (tk.StringVar): 다운로드 경로
        video_check (tk.BooleanVar): 영상 다운로드 체크박스 상태
        sub_check (tk.BooleanVar): 자막 다운로드 체크박스 상태
        srt_check (tk.BooleanVar): SRT 형식 사용 여부
        audio_check (tk.BooleanVar): 음성 다운로드 체크박스 상태
        resolution_var (tk.StringVar): 선택된 해상도
        title_var (tk.StringVar): 사용자 지정 파일명
        language_var (tk.StringVar): 선택된 자막 언어
    """
    
    def __init__(self):
        """YouTubeDownloader 클래스 초기화"""
        super().__init__()
        self.title("유튜브 다운로더 v1.0.1")
        self.geometry("600x350")  # 언어 선택 드롭다운 추가로 높이 약간 증가
        
        self.padding = 20
        main_frame = ttk.Frame(self, padding=self.padding)
        main_frame.pack(fill='both', expand=True)
        
        self.setup_variables()
        self.create_widgets(main_frame)
        
        # 초기화 시 예외 처리 설정
        # 기본 Tkinter 예외 핸들러 재정의
        self.report_callback_exception = self.handle_exception
        
        # 프로그램 종료 시 설정 저장
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_config(self):
        """설정 파일에서 저장된 다운로드 경로를 로드합니다.
        
        Returns:
            str: 저장된 다운로드 경로 또는 기본 다운로드 폴더 경로
        """
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('download_path', os.path.expanduser("~/Downloads"))
        except Exception as e:
            print(f"설정 파일 로드 중 오류 발생: {e}")
        return os.path.expanduser("~/Downloads")
        
    def save_config(self):
        """현재 다운로드 경로를 설정 파일에 저장합니다."""
        try:
            config = {
                'download_path': self.download_path.get()
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"설정 파일 저장 중 오류 발생: {e}")
            
    def on_closing(self):
        """프로그램 종료 시 설정을 저장하고 종료합니다."""
        self.save_config()
        self.quit()
        
    def setup_variables(self):
        """프로그램에서 사용하는 변수들을 초기화합니다."""
        self.download_path = tk.StringVar(value=self.load_config())
        self.video_check = tk.BooleanVar(value=True)
        self.sub_check = tk.BooleanVar(value=True)
        self.srt_check = tk.BooleanVar()
        self.audio_check = tk.BooleanVar()
        self.resolution_var = tk.StringVar(value='2160p')
        self.title_var = tk.StringVar()
        self.language_var = tk.StringVar(value='한국어')  # 자막 언어 설정 변수 추가
        
        self.caption_progress_var = tk.DoubleVar()
        self.video_progress_var = tk.DoubleVar()
        self.audio_progress_var = tk.DoubleVar()
        
    def create_widgets(self, parent):
        """UI 위젯을 생성하고 배치합니다.
        
        Args:
            parent: 위젯들이 배치될 부모 프레임
        """
        # URL 입력 프레임
        url_frame = ttk.Frame(parent)
        url_frame.pack(fill='x', pady=(0, 5))
        url_frame.columnconfigure(1, weight=1)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, padx=(0, 5))
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.grid(row=0, column=1, sticky='ew')
        self.url_entry.focus_set()
        
        path_button = ttk.Button(url_frame, text="저장 경로", command=self.select_download_path)
        path_button.grid(row=0, column=2, padx=5)
        
        start_button = ttk.Button(url_frame, text="다운로드 시작", command=self.start_download)
        start_button.grid(row=0, column=3)
        
        # 제목 입력 프레임
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill='x', pady=(0, 5))
        title_frame.columnconfigure(1, weight=1)
        
        ttk.Label(title_frame, text="제목:").grid(row=0, column=0, padx=(0, 5))
        title_entry = ttk.Entry(title_frame, textvariable=self.title_var)
        title_entry.grid(row=0, column=1, columnspan=3, sticky='ew')
        
        # 현재 다운로드 경로 표시
        path_frame = ttk.Frame(parent)
        path_frame.pack(fill='x', pady=(0, 10))
        path_frame.columnconfigure(1, weight=1)  # 경로 레이블이 늘어나도록 설정
        
        ttk.Label(path_frame, text="저장 경로:").grid(row=0, column=0, sticky='w')
        ttk.Label(path_frame, textvariable=self.download_path).grid(row=0, column=1, sticky='ew', padx=5)
        
        # 경로 열기 버튼 추가
        open_path_button = ttk.Button(path_frame, text="경로 열기", command=self.open_download_folder)
        open_path_button.grid(row=0, column=2, sticky='e')
        
        # 옵션 프레임
        options_frame = ttk.Frame(parent)
        options_frame.pack(fill='x', pady=(0, 20))  # 패딩 조정
        
        ttk.Checkbutton(options_frame, text="영상", variable=self.video_check).pack(side='left', padx=5)
        ttk.Combobox(options_frame, textvariable=self.resolution_var, 
                    values=["2160p", "1080p", "720p"], width=6).pack(side='left', padx=5)
        
        # 자막 옵션과 언어 드롭다운을 나란히 배치
        ttk.Checkbutton(options_frame, text="자막", variable=self.sub_check).pack(side='left', padx=5)
        language_dropdown = ttk.Combobox(options_frame, textvariable=self.language_var, 
                                       values=["한국어", "영어", "모든 언어"], width=8, state="readonly")
        language_dropdown.pack(side='left', padx=5)
        language_dropdown.current(0)  # 기본값은 한국어
        
        ttk.Checkbutton(options_frame, text="음성", variable=self.audio_check).pack(side='left', padx=5)
        
        # 상태 프레임
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(0, 20))
        
        self.caption_status = DownloadStatus(status_frame, "자막", self.caption_progress_var)
        self.caption_status.pack(fill='x', pady=2)
        
        self.video_status = DownloadStatus(status_frame, "영상", self.video_progress_var)
        self.video_status.pack(fill='x', pady=2)
        
        self.audio_status = DownloadStatus(status_frame, "음성", self.audio_progress_var)
        self.audio_status.pack(fill='x', pady=2)
        
        # 완료 상태 메시지
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(5, 5))
        self.status_label = ttk.Label(status_frame, text="")
        self.status_label.pack(side='right')
        
        # 하단 프레임
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill='x', pady=(5, 0))
        
        copyright_label = ttk.Label(
            bottom_frame, 
            text="© 2025 지식에 대한 탐구 (https://small-tip.co.kr) - All rights reserved.",
            cursor="hand2"
        )
        copyright_label.pack(side='left')
        copyright_label.bind("<Button-1>", lambda e: self.open_website())
        
        exit_button = ttk.Button(bottom_frame, text="종료", command=self.on_closing)
        exit_button.pack(side='right')

    def open_website(self):
        """저작권 정보의 웹사이트 링크를 엽니다."""
        import webbrowser
        webbrowser.open("https://small-tip.co.kr")

    def open_download_folder(self):
        """다운로드 폴더를 파일 탐색기에서 엽니다."""
        download_path = self.download_path.get()
        try:
            if sys.platform == 'win32':
                os.startfile(download_path)
            elif sys.platform == 'darwin':  # macOS
                import subprocess
                subprocess.Popen(['open', download_path])
            else:  # linux variants
                import subprocess
                subprocess.Popen(['xdg-open', download_path])
        except Exception as e:
            self.update_status(f"폴더 열기 실패: {str(e)}")

    def get_safe_filename(self, url, video_id):
        """안전한 파일명을 생성합니다.
        
        다음 우선순위로 파일명을 결정합니다:
        1. 사용자가 입력한 제목
        2. YouTube 영상의 원제목
        3. 날짜_시간 형식의 자동 생성 이름
        
        Args:
            url (str): YouTube 영상 URL
            video_id (str): YouTube 영상 ID
            
        Returns:
            str: 사용할 파일명
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
        """진행률 문자열에서 숫자만 추출합니다.
        
        ANSI 색상 코드와 기타 문자를 제거하고 숫자만 추출합니다.
        
        Args:
            percent_str (str): 진행률 문자열
            
        Returns:
            float: 추출된 진행률 값 (0-100)
        """
        clean_str = re.sub(r'\x1b\[[0-9;]*m', '', percent_str)
        clean_str = re.sub(r'[^\d.]', '', clean_str)
        try:
            return float(clean_str)
        except ValueError:
            return 0.0

    def format_time(self, seconds):
        """초 단위 시간을 자막 시간 형식으로 변환합니다.
        
        SRT 형식의 시간 표시(HH:MM:SS,mmm)로 변환합니다.
        
        Args:
            seconds (float): 초 단위 시간
            
        Returns:
            str: 변환된 시간 문자열 (HH:MM:SS,mmm 형식)
        """
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"

    def progress_hook(self, mode):
        """다운로드 진행률 업데이트를 처리하는 콜백 함수를 반환합니다.
        
        yt-dlp의 progress_hooks에서 사용되며, 다운로드 진행 상황을
        UI에 실시간으로 반영합니다.
        
        Args:
            mode (str): 다운로드 모드 ('video' 또는 'audio')
            
        Returns:
            function: 진행률 업데이트 콜백 함수
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

    def save_caption_to_file(self, transcript_data, file_path, is_srt, suffix):
        """자막 데이터를 파일로 저장합니다.
        
        Args:
            transcript_data (list): 자막 데이터 목록
            file_path (str): 저장할 파일 경로 (확장자 제외)
            is_srt (bool): True면 SRT 형식, False면 TXT 형식으로 저장
            suffix (str): 파일명에 추가할 접미사 (예: "_kr" 또는 "_en")
        """
        file_ext = 'srt' if is_srt else 'txt'
        full_path = f"{file_path}{suffix}.{file_ext}"
        
        with open(full_path, 'w', encoding='utf-8') as file:
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
        
        return full_path

    def download_caption(self, video_id, url, safe_title, is_srt):
        """자막을 다운로드하고 파일로 저장합니다.
        
        선택한 언어에 따라 자막을 다운로드하고 요청한 포맷으로 저장합니다.
        
        Args:
            video_id (str): YouTube 영상 ID
            url (str): YouTube 영상 URL
            safe_title (str): 저장할 파일명
            is_srt (bool): True면 SRT 형식, False면 TXT 형식으로 저장
            
        Returns:
            bool: 자막 다운로드 성공 여부
        """
        try:
            self.update_status("자막 다운로드 중...")
            available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            selected_language = self.language_var.get()
            file_path = os.path.join(self.download_path.get(), safe_title)
            
            # 다운로드된 자막 추적
            downloaded_subtitles = []
            
            # 한국어 자막 다운로드 시도
            if selected_language in ["한국어", "모든 언어"]:
                try:
                    ko_transcript = available_transcripts.find_transcript(['ko'])
                    ko_data = ko_transcript.fetch()
                    self.save_caption_to_file(ko_data, file_path, is_srt, "_kr")
                    downloaded_subtitles.append("한국어")
                except Exception:
                    if selected_language == "한국어":
                        self.update_status("한국어 자막이 없어 다운로드 하지 못했습니다.")
            
            # 영어 자막 다운로드 시도
            if selected_language in ["영어", "모든 언어"]:
                try:
                    en_transcript = available_transcripts.find_transcript(['en'])
                    en_data = en_transcript.fetch()
                    self.save_caption_to_file(en_data, file_path, is_srt, "_en")
                    downloaded_subtitles.append("영어")
                except Exception:
                    # 영어 자막 없을 때 자동 생성 영어 자막 시도
                    try:
                        auto_en_transcript = available_transcripts.find_generated_transcript(['en'])
                        auto_en_data = auto_en_transcript.fetch()
                        self.save_caption_to_file(auto_en_data, file_path, is_srt, "_auto_en")
                        downloaded_subtitles.append("영어 자동생성")
                    except Exception:
                        if selected_language == "영어":
                            self.update_status("영어 자막이 없어 다운로드 하지 못했습니다.")
            
            # 다운로드 결과 메시지 표시
            if downloaded_subtitles:
                if len(downloaded_subtitles) == 1:
                    self.update_status(f"{downloaded_subtitles[0]} 자막 다운로드 완료")
                else:
                    self.update_status(f"{' 및 '.join(downloaded_subtitles)} 자막 다운로드 완료")
                self.caption_progress_var.set(100)
                return True
            elif selected_language == "모든 언어":
                self.update_status("자막을 찾을 수 없어 다운로드 하지 못했습니다.")
                self.caption_progress_var.set(0)
                return False
            else:
                self.caption_progress_var.set(0)
                return False

        except Exception as e:
            error_msg = str(e)
            self.update_status(f"자막 다운로드 실패: {error_msg}")
            self.caption_progress_var.set(0)
            return False

    def download_video_audio(self, url, safe_title, mode):
        """영상 또는 음성을 다운로드합니다.
        
        yt-dlp를 사용하여 고품질의 영상 또는 음성을 다운로드합니다.
        
        Args:
            url (str): YouTube 영상 URL
            safe_title (str): 저장할 파일명
            mode (str): 다운로드 모드 ('video' 또는 'audio')
            
        Returns:
            bool: 다운로드 성공 여부
        """
        try:
            file_ext = 'mp4' if mode == 'video' else 'mp3'
            resolution = self.resolution_var.get().replace('p', '')

            # yt-dlp의 확장자 템플릿 사용
            output_filename = os.path.join(self.download_path.get(), f"{safe_title}.%(ext)s")

            ffmpeg_path = 'C:/ffmpeg/bin'

            ydl_opts = {
                'format': f"bv*[height<={resolution}]+ba/b[height<={resolution}]" if mode == 'video' else 'bestaudio/best',
                'outtmpl': output_filename,
                'merge_output_format': file_ext,
                'ffmpeg_location': ffmpeg_path,
                'progress_hooks': [self.progress_hook(mode)],
                'no_color': True,
                'noprogress': True,
                'quiet': True,
            }
            
            if mode == 'audio':
                ydl_opts.update({
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            return True
        except Exception as e:
            error_msg = str(e)
            self.update_status(f"{mode} 다운로드 실패: {error_msg}")
            return False

    def select_download_path(self):
        """다운로드 경로를 선택하고 설정을 저장합니다."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.download_path.set(folder_selected)
            self.save_config()
            
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """모든 예외를 처리하고 상태 표시줄에 표시합니다.
        
        Tkinter의 기본 예외 처리를 오버라이드하여 메시지 상자 대신
        상태 표시줄에 오류 메시지를 표시합니다.
        
        Args:
            exc_type: 예외 타입
            exc_value: 예외 값
            exc_traceback: 예외 트레이스백
        """
        error_msg = str(exc_value)
        self.update_status(f"오류 발생: {error_msg}")
        print(f"Error: {exc_type.__name__}: {error_msg}")
        
    def update_status(self, message):
        """상태 메시지를 업데이트합니다.
        
        Args:
            message (str): 표시할 상태 메시지
        """
        self.status_label.config(text=message)
            
    def start_download(self):
        """다운로드를 시작합니다.
        
        사용자가 선택한 옵션에 따라 영상, 자막, 음성 다운로드를
        비동기적으로 실행합니다.
        """
        url = self.url_entry.get()
        if not url:
            self.update_status("URL을 입력해주세요.")
            return
            
        video_id = url.split("v=")[-1].split("&")[0]
        safe_title = self.get_safe_filename(url, video_id)
        
        # 다운로드 성공 여부를 추적하는 변수
        success = {
            'caption': False,
            'video': False,
            'audio': False
        }
        
        # 선택된 옵션 추적
        options_selected = {
            'caption': self.sub_check.get(),
            'video': self.video_check.get(),
            'audio': self.audio_check.get()
        }
        
        def run_tasks():
            try:
                # 자막 다운로드
                if options_selected['caption']:
                    success['caption'] = self.download_caption(video_id, url, safe_title, self.srt_check.get())
                
                # 영상 다운로드
                if options_selected['video']:
                    success['video'] = self.download_video_audio(url, safe_title, 'video')
                
                # 음성 다운로드
                if options_selected['audio']:
                    success['audio'] = self.download_video_audio(url, safe_title, 'audio')
                
                # 자막만 선택했고 다운로드에 실패한 경우 최종 메시지를 출력하지 않음
                only_caption_failed = (
                    options_selected['caption'] and not success['caption'] and 
                    not options_selected['video'] and not options_selected['audio']
                )
                
                if not only_caption_failed:
                    all_selected_succeeded = all(
                        success[opt] for opt, selected in options_selected.items() if selected
                    )
                    if all_selected_succeeded:
                        self.update_status("모든 다운로드가 완료되었습니다!")
                    else:
                        # 자막 이외의 것이 선택되었고 실패하지 않았다면 일부 완료 메시지 표시
                        has_other_success = any(
                            success[opt] for opt, selected in options_selected.items() 
                            if selected and opt != 'caption'
                        )
                        if has_other_success:
                            self.update_status("일부 다운로드가 완료되었습니다.")
                
            except Exception as e:
                self.update_status(f"오류 발생: {str(e)}")
                
        if not any(options_selected.values()):
            self.update_status("다운로드 옵션을 선택해주세요.")
            return
        
        threading.Thread(target=run_tasks, daemon=True).start()

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()