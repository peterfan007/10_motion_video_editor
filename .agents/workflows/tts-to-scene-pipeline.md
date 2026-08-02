---
name: tts-to-scene-pipeline
description: 특정 폴더의 대본을 TTS로 변환하고, 자막용 씬 데이터(JSON) 및 최종 자막+음성 결합 비디오까지 한 번에 생성하는 전체 공정 워크플로우입니다.
---

# tts-to-scene-pipeline

이 워크플로우는 영상 제작을 위한 음성 소스, 자막 데이터를 생성하고, 리모션을 활용해 최종 비디오까지 자동으로 결합 및 렌더링합니다.

## 실행 단계

### 1단계: 음성 생성 (tts-generate)
- `reference_voice.mp3`를 사용하여 보이스 클로닝을 수행합니다.
- 생성된 음성을 1.2배속으로 변환하여 `output_1.2x.wav`를 생성합니다.

### 2단계: 자막 및 씬 데이터 생성 (stt-scene-align)
- 생성된 음성을 Whisper STT로 변환합니다.
- 원본 대본과 대조하여 숫자, 고유명사 등을 교정합니다.
- 한 문장(블록) 단위로 씬을 분리하여 `scene_data.json`을 생성합니다.

### 3단계: 최종 비디오 렌더링 (remotion-render)
- 각 씬별 비디오(`scene{id}.mp4` 등)가 존재하면 가져와 합성하고, 전체 오디오 트랙과 싱크에 맞춘 가독성 높은 한국어 자막 오버레이를 입혀 최종 비디오(`output.mp4`)를 구워냅니다.

## 실행 방법

루트의 `outputs/` 폴더 내에 주제별 폴더(예: `outputs/my_topic`)를 생성하고, 해당 경로 또는 하위 폴더명을 인자로 주어 아래 스크립트를 순차적으로 실행합니다.

```bash
# 1. TTS 생성 (인자가 없으면 outputs/ 내 미처리 최신 폴더를 자동 추적합니다)
python3 .agents/skills/tts-generate/scripts/generate.py outputs/my_topic

# 2. STT 및 씬 데이터 생성
python3 .agents/skills/stt-scene-align/scripts/align.py outputs/my_topic

# 3. Remotion 최종 영상 렌더링
python3 .agents/skills/remotion-render/scripts/render.py outputs/my_topic
```

## 완료 시 결과물 (`outputs/하위폴더/` 하위)
- `output.mp4`: 최종 합성 완료된 자막 및 음성 포함 비디오 파일
- `output_1.2x.wav`: 1.2배속 음성 파일
- `raw_stt.json`: 원본 STT 데이터
- `scene_data.json`: 최종 자막용 씬 데이터
- `script.md`: 원본 대본

