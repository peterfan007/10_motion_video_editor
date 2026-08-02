---
name: stt-scene-align
description: .wav 파일과 대본을 비교하여 정교한 자막용 씬 데이터를 생성합니다. (한 문장 단위 씬 구성)
---

# stt-scene-align

OpenAI Whisper API를 사용하여 음성을 텍스트로 변환하고, 원본 대본(`script.md`)을 참고하여 텍스트 교정 및 문장 단위 씬 그룹화 작업을 수행합니다.

## 주요 기능
- **Whisper STT**: OpenAI API를 통한 정확한 타임라인 추출.
- **하이브리드 교정**: 발음 위주의 대본을 자막용(숫자, 기호, 고유명사)으로 자동 변환 및 정렬.
- **문장 단위 씬 분리**: 기존 5개 블록 결합 규칙 대신, 각 문장(블록)마다 독립된 씬(`scene_id`)을 갖도록 1:1 매핑하여 `scene_data.json`을 구성합니다.
- **프레임 계산**: 30 FPS 기준 `duration_frames` 자동 계산.

## 사용 방법
1. `.env` 파일에 `OPENAI_API_KEY`가 설정되어 있는지 확인합니다.
2. 대상 폴더(예: `outputs/my_project`)에 `output_1.2x.wav`와 `script.md` 파일이 있어야 합니다.
3. 아래 명령어를 통해 스킬을 실행합니다.

```bash
python3 .agents/skills/stt-scene-align/scripts/align.py outputs/my_project
```

## 결과물
- `raw_stt.json`: Whisper에서 추출한 원본 데이터.
- `scene_data.json`: 최종 교정 및 문장 단위로 분할된 씬 데이터.
