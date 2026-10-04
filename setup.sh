#!/bin/bash
# Antigravity Remotion Pipeline - Auto Setup Script

echo "=================================================="
echo "🎬 Antigravity Remotion Pipeline 자동 설정 스크립트"
echo "=================================================="

# 1. Python 패키지 설치
echo -e "\n1. Python 의존성 라이브러리 설치 중..."
pip install -r requirements.txt

# 2. Node.js/Remotion 패키지 설치
echo -e "\n2. Remotion (Node.js) 패키지 설치 중..."
if [ -d "my-video" ]; then
  cd my-video
  npm install
  cd ..
  echo "✅ Remotion 패키지 설치 완료!"
else
  echo "❌ Error: my-video 폴더를 찾을 수 없습니다."
  exit 1
fi

# 3. 환경 변수 파일 생성 (.env)
echo -e "\n3. 환경 변수 (.env) 확인 중..."
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "⚠️ .env 파일이 생성되었습니다. 파일 내의 OpenAI API Key를 설정해 주세요."
else
  echo "✅ .env 파일이 이미 존재합니다."
fi

# 4. FFmpeg 설치 여부 확인
echo -e "\n4. FFmpeg 시스템 도구 확인 중..."
if command -v ffmpeg >/dev/null 2>&1; then
  echo "✅ FFmpeg가 정상 설치되어 있습니다."
else
  echo "⚠️ Warning: FFmpeg가 설치되어 있지 않거나 PATH에 없습니다."
  echo "   Remotion 및 오디오 속도 조절을 위해 FFmpeg 설치가 필수적입니다."
  echo "   - macOS: brew install ffmpeg"
  echo "   - Windows: winget install GnuWin.FFmpeg 또는 수동 다운로드 후 환경변수 등록"
  echo "   - Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg"
fi

echo -e "\n=================================================="
echo "🎉 설정 완료! 아래 단계를 진행해 주세요:"
echo "1. .env 파일에 OpenAI API Key 등록하기"
echo "2. outputs/ 폴더에 대본(script.md) 작성 후 파이프라인 가동"
echo "=================================================="
