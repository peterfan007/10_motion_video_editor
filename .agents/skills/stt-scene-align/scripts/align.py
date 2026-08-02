import os
import json
import sys
import glob
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FPS = 30

def get_stt_data(file_path):
    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    return response.segments

def refine_text_llm(segments, script_text):
    stt_texts = [f"[{i}] {seg.text}" for i, seg in enumerate(segments)]
    stt_combined = "\n".join(stt_texts)
    
    prompt = """
    원본 대본을 참고하여 STT 결과를 자막용으로 교정하고, 자연스러운 자막 호흡을 위해 분할된 조각들을 병합하세요.
    
    [교정 및 병합 가이드라인]
    1. 숫자 및 단위 교정 (예: 칠십 퍼센트 -> 70%)
    2. 고유명사 교정 (예: 에이아이 -> AI, 쥐스택 -> G-Stack, 슈퍼파워스 -> Superpowers)
    3. 중요: 한국어 조사, 어미, 합성어 등이 segment 경계에서 어색하게 쪼개진 경우(예: "첫" / "번째", "던져" / "주면", "학습" / "하고", "안" / "들인" 등), 인접한 segment들을 하나로 합쳐서 자연스러운 자막 문구로 만드세요.
    4. 병합한 자막 텍스트와 함께, 병합에 사용된 원래 STT segments의 인덱스 번호 배열(indices)을 반환해야 합니다.
    5. 반환 형식은 반드시 아래 예시와 같은 JSON 배열 형식이어야 합니다. 마크다운 백틱(```json)을 제외한 다른 설명 텍스트는 일체 출력하지 마세요.
    
    [반환 형식 예시]
    [
      {
        "text": "전 세계 기업 10곳 중 9곳이 AI를 쓰고 있습니다.",
        "indices": [0]
      },
      {
        "text": "많은 경영진이 값비싼 AI 소프트웨어 면허증만 사서 직원들에게 던져주면 혁신이 일어날 거라고 믿습니다.",
        "indices": [3, 4]
      }
    ]
    
    [원본 대본]
    {script_text}
    
    [STT 결과]
    {stt_combined}
    """
    prompt = prompt.replace("{script_text}", script_text).replace("{stt_combined}", stt_combined)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```json"): content = content[7:-3].strip()
    elif content.startswith("```"): content = content[3:-3].strip()
    return json.loads(content)

def main():
    if len(sys.argv) < 2: return
    folder = sys.argv[1]
    wav_path = os.path.join(folder, "output_1.2x.wav")
    
    md_files = glob.glob(os.path.join(folder, "*.md"))
    if not md_files:
        print(f"에러: {folder} 내에 MD 대본 파일이 없습니다.")
        return
    script_path = md_files[0]
    
    with open(script_path, 'r', encoding='utf-8') as f: 
        script_text = f.read()

    print(f"[*] STT 시작: {wav_path}")
    segments = get_stt_data(wav_path)
    
    # RAW 저장
    raw_path = os.path.join(folder, "raw_stt.json")
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump([{"text": s.text, "start": s.start, "end": s.end} for s in segments], f, ensure_ascii=False, indent=2)

    print(f"[*] 하이브리드 교정 및 병합 중...")
    try:
        refined_blocks = refine_text_llm(segments, script_text)
        if not isinstance(refined_blocks, list) or not all(isinstance(b, dict) and "text" in b and "indices" in b for b in refined_blocks):
            raise ValueError("Invalid LLM response format")
    except Exception as e:
        print(f"[!] LLM 교정/병합 실패. 기본 STT 결과를 사용합니다. 에러: {e}")
        refined_blocks = [{"text": seg.text, "indices": [i]} for i, seg in enumerate(segments)]
    
    print(f"[*] 씬 그룹화 중 (한 문장 단위 1씬 구성)...")
    scenes = []
    scene_id = 1
    
    for block in refined_blocks:
        text = block["text"]
        indices = block["indices"]
        
        if not indices:
            continue
            
        # 안전장치: 인덱스가 segments 범위를 벗어나는 것 방지
        valid_indices = [idx for idx in indices if 0 <= idx < len(segments)]
        if not valid_indices:
            continue
            
        start = round(segments[valid_indices[0]].start, 2)
        end = round(segments[valid_indices[-1]].end, 2)
        
        # 한 문장(1 블록) 단위로 씬을 바로 생성하여 추가
        scenes.append(create_scene(scene_id, [{"text": text, "start": start, "end": end}]))
        scene_id += 1
    
    out_path = os.path.join(folder, "scene_data.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, ensure_ascii=False, indent=2)
    print(f"[+] 성공: {out_path}")

def create_scene(scene_id, blocks):
    start, end = blocks[0]["start"], blocks[-1]["end"]
    return {
        "scene_id": scene_id,
        "start": start, "end": end,
        "duration_frames": int((end - start) * FPS),
        "text_blocks": blocks
    }

if __name__ == "__main__":
    main()
