import requests
import os
import json
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "..", "..", "_common"))
from pipeline_utils import PROJECT_ROOT, find_script_md, resolve_folder  # noqa: E402

# 설정
BASE_URL = "http://127.0.0.1:7860"
API_PREFIX = "/gradio_api"
SPEED_RATE = 1.2

# 레퍼런스 설정
REF_AUDIO_PATH = os.path.join(PROJECT_ROOT, "reference_voice.mp3")
REF_TEXT = "안녕하세요 여러분. 반갑습니다. 오늘도 저희 채널을 찾아주셔서 감사합니다. 영상이 도움되셨다면 구독과 좋아요를 눌러주세요."

def upload_file(file_path):
    url = f"{BASE_URL}{API_PREFIX}/upload"
    with open(file_path, "rb") as f:
        files = {"files": f}
        response = requests.post(url, files=files, timeout=60)
    if response.status_code == 200:
        result = response.json()
        path = result[0]
        return {"path": path, "meta": {"_type": "gradio.FileData"}}
    else:
        raise Exception(f"파일 업로드 실패: {response.text}")

def call_api(api_name, data):
    url = f"{BASE_URL}{API_PREFIX}/call{api_name}"
    payload = {"data": data}
    response = requests.post(url, json=payload, timeout=60)
    if response.status_code == 200:
        return response.json()["event_id"]
    else:
        raise Exception(f"API 호출 시작 실패 ({api_name}): {response.text}")

def get_result(api_name, event_id):
    url = f"{BASE_URL}{API_PREFIX}/call{api_name}/{event_id}"
    # 연결 10초, 응답(TTS 생성 대기) 최대 30분
    response = requests.get(url, stream=True, timeout=(10, 1800))
    current_event = None
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8').strip()
            if line_str.startswith("event:"):
                current_event = line_str[6:].strip()
            elif line_str.startswith("data:"):
                data_str = line_str[5:].strip()
                if current_event == "complete":
                    return json.loads(data_str)
                if current_event == "error":
                    raise Exception(f"API 에러 이벤트: {data_str}")
    raise Exception("결과를 찾지 못했습니다.")

def change_speed(input_file, output_file, rate=SPEED_RATE):
    cmd = ["ffmpeg", "-i", input_file, "-filter:a", f"atempo={rate}", output_file, "-y"]
    # check=True: ffmpeg 실패 시 조용히 넘어가지 않고 예외 발생
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def main():
    arg = sys.argv[1] if len(sys.argv) >= 2 else None
    folder_path = resolve_folder(
        arg,
        is_ready=lambda d: find_script_md(d) is not None,
        is_done=lambda d: os.path.exists(os.path.join(d, "output_1.2x.wav")),
    )
    if not folder_path:
        sys.exit(1)

    script_path = find_script_md(folder_path)
    if not script_path:
        print(f"에러: {folder_path} 내에 MD 파일이 없습니다.")
        sys.exit(1)
    with open(script_path, 'r', encoding='utf-8') as f:
        script_text = f.read()

    print(f"[*] 처리 시작: {folder_path}")
    if not os.path.exists(REF_AUDIO_PATH):
        print(f"에러: 레퍼런스 오디오 파일을 찾을 수 없습니다: {REF_AUDIO_PATH}")
        sys.exit(1)

    # 1. 레퍼런스 처리 (업로드만 진행, 트랜스크립션은 고정 텍스트 사용)
    print("[*] 레퍼런스 오디오 업로드 중...")
    ref_file_info = upload_file(REF_AUDIO_PATH)
    ref_text = REF_TEXT

    # 2. TTS 생성
    print("[*] Voice Clone 생성 중...")
    clone_data = [ref_file_info, ref_text, script_text, "Korean", False, "1.7B", 200, 0.0, -1]
    event_id = call_api("/generate_voice_clone", clone_data)
    result_data = get_result("/generate_voice_clone", event_id)

    audio_file_info = result_data[0]
    if not audio_file_info:
        print("에러: TTS 생성 실패")
        sys.exit(1)

    # 3. 다운로드 및 배속 변환
    temp_wav = os.path.join(folder_path, "temp.wav")
    final_wav = os.path.join(folder_path, "output_1.2x.wav")

    remote_path = audio_file_info.get("path")
    audio_url = f"{BASE_URL}{API_PREFIX}/file={remote_path}"

    r = requests.get(audio_url, stream=True, timeout=(10, 300))
    if r.status_code != 200:
        print(f"에러: 다운로드 실패 ({r.status_code})")
        sys.exit(1)
    try:
        with open(temp_wav, 'wb') as f:
            # r.raw 직접 복사는 gzip 응답을 풀지 않으므로 iter_content 사용
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
        change_speed(temp_wav, final_wav)
        print(f"[+] 성공: {final_wav}")
    except Exception as e:
        print(f"에러: 음성 후처리 실패 - {e}")
        sys.exit(1)
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

if __name__ == "__main__":
    main()
