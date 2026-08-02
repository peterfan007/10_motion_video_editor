# Motion Video Editor (Remotion & Local TTS Pipeline)

이 프로젝트는 대본(`script.md`)을 바탕으로 **로컬 Qwen3-TTS를 통한 음성 합성**, **OpenAI Whisper 및 LLM 기반의 자막 씬 정렬**, 그리고 **Remotion을 활용한 최종 비디오 자동 렌더링**을 수행하는 자동화 파이프라인입니다.

---

## 🚀 빠른 시작 및 설치 (Quick Start)

이 저장소를 클론한 뒤 아래 단계에 따라 설정을 진행하세요.

### 1. 사전 요구 사항 (Prerequisites)
설정을 시작하기 전에 시스템에 다음 항목들이 설치되어 있어야 합니다.
* **Node.js**: v18 이상 (Remotion 실행용)
* **Python**: v3.9 이상 (파이프라인 스크립트 실행용)
* **FFmpeg**: 시스템 전역 경로에 설치되어 있어야 합니다. (음성 배속 및 비디오 GOP=1 인코딩 최적화용)
* **로컬 Qwen3-TTS 서버**: Pinokio 등을 통해 로컬 `http://127.0.0.1:7860`에서 TTS API가 정상 실행 중이어야 합니다.

---

### 2. 저장소 클론 및 이동
터미널을 열고 저장소를 클론한 뒤 해당 디렉토리로 이동합니다.
```bash
git clone <Repository_URL>
cd <Repository_Name>
```

---

### 3. 환경 변수 설정 (`.env`)
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 OpenAI API 키를 설정합니다. (Whisper STT 및 자막 교정에 사용됩니다.)
```env
OPENAI_API_KEY=your_openai_api_key_here
```

---

### 4. 의존성 설치 (리모션 및 파이썬)

#### A. Remotion (Node.js) 패키지 설치
리모션 비디오 프로젝트 엔진이 있는 `my-video` 디렉토리로 이동하여 의존성을 설치합니다.
```bash
cd my-video
npm install
cd ..
```

#### B. Python 라이브러리 설치
파이프라인 실행 스크립트에서 사용하는 Python 패키지를 설치합니다.
```bash
pip install requests openai python-dotenv
```

---

## 🎬 파이프라인 실행 방법

전체 공정은 **[음성 생성] ➡️ [자막/씬 데이터 매핑] ➡️ [비디오 렌더링]** 순서로 진행됩니다.

### 1단계: 대본 작성
루트의 `outputs/` 폴더 내에 작업 폴더(예: `outputs/my_project`)를 생성하고, 그 안에 `script.md` 파일을 작성해 넣습니다.

### 2단계: 파이프라인 실행
준비한 폴더 경로(`outputs/my_project`)를 인자로 주어 아래 스크립트를 차례대로 실행합니다.

```bash
# 1. 로컬 TTS 서버 호출을 통한 음성 생성 (1.2배속 wav 파일 생성)
python3 .agents/skills/tts-generate/scripts/generate.py outputs/my_project

# 2. Whisper STT 분석 및 대본 기반 자막 씬 데이터(scene_data.json) 생성
python3 .agents/skills/stt-scene-align/scripts/align.py outputs/my_project

# 3. Remotion을 통한 씬 영상 합성 및 최종 비디오(output.mp4) 렌더링
python3 .agents/skills/remotion-render/scripts/render.py outputs/my_project
```
> **Tip:** 인자를 전달하지 않으면 `outputs/` 폴더 내에서 아직 처리되지 않은 가장 최신의 하위 폴더를 자동으로 찾아 처리합니다.

---

## 🖥️ 리모션 스튜디오 프리뷰 실행
렌더링하기 전에 리모션 브라우저(Remotion Studio)를 통해 실시간으로 자막 위치와 씬 전환을 미리 보고 싶다면 아래 명령어를 사용하세요.

```bash
cd my-video
npm run dev
```
명령어를 실행하면 웹 브라우저(`http://localhost:3000`)를 통해 비디오를 미리 볼 수 있습니다.

---

## 📂 최종 산출물 구성 (`outputs/작업폴더/`)
* `script.md`: 원본 대본
* `output_1.2x.wav`: Qwen3-TTS가 생성한 1.2배속 오디오
* `raw_stt.json`: Whisper STT 원본 타임라인
* `scene_data.json`: 최종 자막 씬 정보 (싱크 시간 포함)
* `output.mp4`: 최종 렌더링 완료된 자막+음성 결합 비디오 파일
