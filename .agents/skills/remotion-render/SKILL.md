---
name: remotion-render
description: outputs 하위폴더의 scene_data.json, 음성, 씬별 비디오를 합성하고 자막을 입혀 Remotion 비디오를 렌더링합니다.
---

# remotion-render

`outputs/` 하위 폴더에 생성된 `scene_data.json`, `output_1.2x.wav`, 그리고 각 씬에 해당하는 비디오 파일(`scene1.mp4`, `scene2.mp4` 등)을 읽어와서, Remotion을 사용해 음성과 자막이 싱크에 맞게 결합된 최종 비디오(`output.mp4`)를 자동 렌더링하는 스킬입니다.

## 주요 기능
- **파라미터화된 렌더링**: 각 작업 폴더의 `scene_data.json` 데이터와 폴더명을 Remotion에 `inputProps`로 넘겨 동적으로 렌더링합니다.
- **씬 영상 및 음성 합성**: 씬별 시작 시간에 맞추어 해당 비디오를 배치하고 전체 1.2배속 음성을 오디오 트랙으로 합성합니다.
- **자동 자막 생성**: `scene_data.json`에 정의된 개별 자막 블록의 타임스탬프(`start`, `end`)에 맞추어 Noto Sans KR 폰트 기반의 세련된 반투명 자막 오버레이를 띄웁니다.
- **자동 폴더 탐색**: `outputs` 디렉토리 내에서 처리되지 않은 가장 최신의 하위폴더(즉, `scene_data.json`은 있지만 `output.mp4`는 없는 폴더)를 자동으로 찾아 렌더링을 진행할 수 있습니다.

## 사용 방법
아래 방식들 중 하나를 사용해 렌더링 스크립트를 실행합니다.

```bash
# 방법 1: 인자 없이 실행 (outputs 폴더 내 미처리된 최신 하위 폴더 자동 렌더링)
python3 .agents/skills/remotion-render/scripts/render.py

# 방법 2: 하위 폴더 이름만 지정
python3 .agents/skills/remotion-render/scripts/render.py test_project

# 방법 3: 전체 상대/절대 경로 지정
python3 .agents/skills/remotion-render/scripts/render.py outputs/test_project
```

## 완료 시 결과물 (`outputs/하위폴더/` 하위)
- `output.mp4`: 최종 합성 완료된 자막 및 음성 포함 비디오 파일
