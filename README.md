# YouTube Downloader

YouTube 동영상을 다운로드하고 자막을 추출할 수 있는 데스크톱 애플리케이션입니다.

## 주요 기능

- 고화질 영상 다운로드 (최대 4K/2160p 지원)
- 자막 다운로드 (txt/srt 형식)
  - 한국어/영어/모든 언어 선택 가능
  - 언어별 자동 대체 지원 (선택한 언어가 없을 경우)
- 음성 추출 (mp3 형식)
- 진행률 실시간 표시
- 사용자 지정 파일명 설정
- 다운로드 경로 저장 및 관리
- 다운로드 폴더 바로 열기 기능

## 설치 방법

1. Python 3.8 이상 설치
2. 필요한 라이브러리 설치:
```bash
pip install pytube youtube_transcript_api yt-dlp
```
3. ffmpeg 설치:
   - Windows: [ffmpeg 다운로드](https://ffmpeg.org/download.html) 후 C:/ffmpeg/bin에 압축 해제
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`

## 사용 방법

1. 프로그램 실행:
```bash
python youtube_downloader.py
```
2. YouTube URL 입력
3. 원하는 경우 제목 입력 (입력하지 않으면 원본 제목 사용)
4. 다운로드 옵션 선택:
   - 영상: 해상도 선택 가능 (2160p, 1080p, 720p)
   - 자막: 언어 선택 가능 (한국어, 영어, 모든 언어)
   - 음성: mp3 형식으로 추출
5. '다운로드 시작' 버튼 클릭
6. '경로 열기' 버튼으로 다운로드된 파일이 있는 폴더 확인 가능

## 시스템 요구사항

- Windows, macOS 또는 Linux
- Python 3.8 이상
- 인터넷 연결

## 문제 해결

- 상태 표시줄에 오류 메시지가 표시되면 해당 내용을 확인하여 문제 해결 가능
- 자막이 없는 경우 상태 표시줄에 안내 메시지 표시
- 다운로드 진행 상황은 각 항목별 진행률 바에서 확인 가능

## 라이선스

이 프로젝트는 GNU General Public License v3.0 라이선스 하에 배포됩니다.
자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 저작권

Copyright (c) 2025 지식에 대한 탐구 (https://small-tip.co.kr)

## 기여

버그 리포트, 기능 제안, Pull Request는 언제나 환영합니다.
