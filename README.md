# YouTube Downloader

YouTube 동영상을 다운로드하고 자막을 추출할 수 있는 데스크톱 애플리케이션입니다.

## 주요 기능

- 고화질 영상 다운로드 (최대 4K/2160p 지원)
- 자막 다운로드 (txt/srt 형식)
- 음성 추출 (mp3 형식)
- 진행률 실시간 표시
- 다국어 자막 지원

## 설치 방법

1. Python 3.8 이상 설치
2. 필요한 라이브러리 설치:
```bash
pip install -r requirements.txt
```
3. ffmpeg 설치:
   - Windows: [ffmpeg 다운로드](https://ffmpeg.org/download.html)
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`

## 사용 방법

1. 프로그램 실행:
```bash
python youtube_downloader.py
```
2. YouTube URL 입력
3. 다운로드 옵션 선택 (영상/자막/음성)
4. '다운로드 시작' 버튼 클릭

## 라이선스

이 프로젝트는 GNU General Public License v3.0 라이선스 하에 배포됩니다.
자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 저작권

Copyright (c) 2024 지식에 대한 탐구 (https://small-tip.co.kr)

## 기여

버그 리포트, 기능 제안, Pull Request는 언제나 환영합니다.
