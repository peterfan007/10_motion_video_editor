import os
import sys
import json
import math
import glob
import subprocess

FPS = 30

# 프로젝트 루트 및 리모션 디렉토리 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
REMOTION_DIR = os.path.join(PROJECT_ROOT, "my-video")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

def has_audio_stream(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_name",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return len(result.stdout.strip()) > 0
    except Exception:
        # ffprobe 에러 발생 시 오디오가 있는 것으로 가정하고 최적화를 진행하도록 함
        return True

def is_all_keyframes(file_path):
    # 전체 비디오 프레임 수 카운트
    cmd_all = [
        "ffprobe", "-v", "error",
        "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames",
        "-of", "default=nokey=1:noprint_wrappers=1",
        file_path
    ]
    # 키프레임(I-frame) 수 카운트
    cmd_key = [
        "ffprobe", "-v", "error",
        "-skip_frame", "nokey", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames",
        "-of", "default=nokey=1:noprint_wrappers=1",
        file_path
    ]
    try:
        res_all = subprocess.run(cmd_all, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        res_key = subprocess.run(cmd_key, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        all_frames = int(res_all.stdout.strip())
        key_frames = int(res_key.stdout.strip())
        return all_frames == key_frames
    except Exception:
        return False

def main():
    folder_path = None

    # 1. 인자 처리
    if len(sys.argv) >= 2:
        arg_path = sys.argv[1]
        # 입력한 경로가 그대로 존재하는 경우
        if os.path.exists(arg_path):
            folder_path = os.path.abspath(arg_path)
        # outputs/<arg_path> 형태로 존재하는 경우
        elif os.path.exists(os.path.join(OUTPUTS_DIR, arg_path)):
            folder_path = os.path.abspath(os.path.join(OUTPUTS_DIR, arg_path))
        else:
            print(f"에러: 지정한 폴더를 찾을 수 없습니다: {arg_path}")
            return
    else:
        # 인자가 없는 경우, outputs/ 디렉토리 내의 하위 폴더 자동 스캔
        if not os.path.exists(OUTPUTS_DIR):
            print("에러: outputs 디렉토리가 존재하지 않습니다.")
            return
            
        subdirs = [os.path.join(OUTPUTS_DIR, d) for d in os.listdir(OUTPUTS_DIR) if os.path.isdir(os.path.join(OUTPUTS_DIR, d))]
        
        # scene_data.json 파일은 존재하고 output.mp4 파일은 존재하지 않는 폴더 목록 필터링
        target_dirs = []
        for sd in subdirs:
            has_scene_data = os.path.exists(os.path.join(sd, "scene_data.json"))
            has_output = os.path.exists(os.path.join(sd, "output.mp4"))
            if has_scene_data and not has_output:
                target_dirs.append(sd)
                
        if not target_dirs:
            # 만약 조건에 맞는 폴더가 없다면, 그냥 outputs 폴더 내에서 가장 최근에 수정된 폴더를 탐색
            if subdirs:
                subdirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                folder_path = subdirs[0]
                print(f"[*] 미처리 폴더가 없어 가장 최근 수정된 폴더를 선택했습니다: {folder_path}")
            else:
                print("사용법: python3 render.py <폴더경로>")
                print("또는 outputs/ 폴더 내에 하위 폴더와 scene_data.json 파일을 생성한 후 인자 없이 실행하세요.")
                return
        else:
            # 미처리 폴더 중 가장 최근 수정된 폴더 선택
            target_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            folder_path = target_dirs[0]
            print(f"[*] 자동으로 렌더링할 최신 미처리 폴더를 탐색했습니다: {folder_path}")

    # 2. 필수 파일 확인
    scene_data_path = os.path.join(folder_path, "scene_data.json")
    if not os.path.exists(scene_data_path):
        print(f"에러: {folder_path} 내에 scene_data.json 파일이 없습니다.")
        return

    print(f"[*] 렌더링 시작 대상 폴더: {folder_path}")

    # 3. scene_data.json 파싱 및 총 재생 길이 계산
    with open(scene_data_path, "r", encoding="utf-8") as f:
        try:
            scene_data = json.load(f)
        except Exception as e:
            print(f"에러: scene_data.json 파싱 실패 - {e}")
            return

    if not isinstance(scene_data, list) or len(scene_data) == 0:
        print("에러: scene_data.json 형식이 올바르지 않거나 비어 있습니다.")
        return

    # 마지막 씬의 end 시간을 기준으로 비디오 프레임 수 계산
    try:
        max_end_time = max(scene.get("end", 0.0) for scene in scene_data)
    except Exception as e:
        print(f"에러: 씬 데이터에서 시간 파싱 중 에러 발생 - {e}")
        return

    duration_in_frames = int(math.ceil(max_end_time * FPS))
    # 오버헤드를 막기 위한 최소 1프레임 보장
    duration_in_frames = max(1, duration_in_frames)

    # 4. 각 씬 비디오 트랜스코딩 최적화 (CFR 30fps, 오디오 제거, In-place 덮어쓰기)
    print("[*] 씬 비디오 파일 최적화 검사 중...")
    for scene in scene_data:
        scene_id = scene.get("scene_id")
        video_filename = f"scene{scene_id}.mp4"
        orig_filename = f"scene{scene_id}.orig.mp4"
        
        video_path = os.path.join(folder_path, video_filename)
        orig_path = os.path.join(folder_path, orig_filename)
        temp_video_path = os.path.join(folder_path, f"scene{scene_id}.transcode_temp.mp4")
        
        # 기존에 생성된 백업 파일(.orig.mp4)이 있다면 깔끔하게 삭제
        if os.path.exists(orig_path):
            try:
                os.remove(orig_path)
                print(f"[*] 기존 백업 파일 삭제 완료: {orig_filename}")
            except Exception as e:
                print(f"[!] 기존 백업 파일 삭제 실패 ({orig_filename}): {e}")
        
        if os.path.exists(video_path):
            # 오디오가 남아있거나, 혹은 모든 프레임이 키프레임이 아닌 경우(GOP > 1) 최적화 트랜스코딩 진행
            # GOP=1(All-Intra)로 만들어주어야 브라우저 단에서 프레임 탐색(seek) 시 잔떨림이나 렉이 발생하지 않습니다.
            needs_transcode = has_audio_stream(video_path) or not is_all_keyframes(video_path)
            
            if needs_transcode:
                print(f"[*] {video_filename} 최적화 및 GOP=1 변환 진행 중...")
                try:
                    # 1. 임시 파일로 H264 CFR 30fps, GOP=1(-g 1), 오디오 제거(-an) 트랜스코딩 수행
                    cmd = [
                        "ffmpeg", "-i", video_path,
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        "-profile:v", "high",
                        "-level:v", "4.0",
                        "-g", "1",  # 리모션 프레임 캡처 정확도를 위해 모든 프레임을 키프레임으로 강제 적용 (butter-smooth)
                        "-movflags", "+faststart",
                        "-r", str(FPS),
                        "-an",  # 오디오 스트림 제거
                        temp_video_path, "-y"
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    
                    # 2. 원본 파일을 임시 파일로 덮어쓰기
                    os.replace(temp_video_path, video_path)
                    print(f"[+] {video_filename} 최적화 완료 (H264 CFR 30fps + GOP=1 + Muted)")
                except Exception as e:
                    print(f"[!] {video_filename} 최적화 실패: {e}")
                    if os.path.exists(temp_video_path):
                        os.remove(temp_video_path)
            else:
                print(f"[*] {video_filename} 이미 최적화되어 있습니다. (건너뜀)")

    # 5. 임시 props JSON 생성
    folder_name = os.path.basename(folder_path)
    
    # 각 씬별 비디오 파일(scene{id}.mp4) 존재 여부 확인 후 metadata 추가
    for scene in scene_data:
        scene_id = scene.get("scene_id")
        video_file = f"scene{scene_id}.mp4"
        scene["has_video"] = os.path.exists(os.path.join(folder_path, video_file))

    props_data = {
        "folderName": folder_name,
        "sceneData": scene_data,
        "durationInFrames": duration_in_frames
    }

    temp_props_path = os.path.join(folder_path, "temp_props.json")
    with open(temp_props_path, "w", encoding="utf-8") as f:
        json.dump(props_data, f, ensure_ascii=False, indent=2)

    # 5. 리모션 렌더링 명령 실행
    output_video_path = os.path.join(folder_path, "output.mp4")
    
    # 렌더링 도중 폰트나 Rspack 관련 경고 등으로 터미널이 혼잡할 수 있으므로, standard CLI 실행
    # npx remotion render DynamicVideo <output_path> --props=<props_path>
    cmd = [
        "npx", "remotion", "render",
        "DynamicVideo",
        output_video_path,
        f"--props={temp_props_path}",
        "--yes"
    ]

    print(f"[*] Remotion 렌더링 실행 중 (출력 경로: {output_video_path})...")
    print(f"[*] 명령어: {' '.join(cmd)}")
    
    try:
        # my-video 디렉토리에서 명령어 실행
        result = subprocess.run(
            cmd,
            cwd=REMOTION_DIR,
            check=True
        )
        print(f"[+] 성공: 비디오가 성공적으로 생성되었습니다 -> {output_video_path}")
    except subprocess.CalledProcessError as e:
        print(f"[!] 에러: Remotion 렌더링 명령이 실패했습니다 (반환 코드: {e.returncode})")
    except Exception as e:
        print(f"[!] 에러: 렌더링 중 오류 발생 - {e}")
    finally:
        # 임시 props 파일 제거
        if os.path.exists(temp_props_path):
            os.remove(temp_props_path)
            print("[*] 임시 설정 파일을 삭제했습니다.")

if __name__ == "__main__":
    main()
