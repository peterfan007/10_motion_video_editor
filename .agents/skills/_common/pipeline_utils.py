"""세 파이프라인 스크립트(generate / align / render)가 공유하는 유틸리티."""
import glob
import os

COMMON_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(COMMON_DIR, "..", "..", ".."))
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")


def find_script_md(folder):
    """대본 MD 파일을 찾는다. script.md를 우선하고, 없으면 이름순 첫 번째 .md를 사용."""
    preferred = os.path.join(folder, "script.md")
    if os.path.exists(preferred):
        return preferred
    md_files = sorted(glob.glob(os.path.join(folder, "*.md")))
    return md_files[0] if md_files else None


def resolve_folder(arg, is_ready, is_done):
    """작업 폴더를 결정한다. 못 찾으면 None.

    arg      : 사용자가 넘긴 경로/폴더명 (없으면 None)
    is_ready : 폴더가 이 단계를 처리할 준비가 됐는지 검사하는 함수
    is_done  : 폴더가 이 단계를 이미 마쳤는지 검사하는 함수
    """
    if arg:
        for cand in (arg, os.path.join(OUTPUTS_DIR, arg)):
            if os.path.isdir(cand):
                return os.path.abspath(cand)
        print(f"에러: 지정한 폴더를 찾을 수 없습니다: {arg}")
        return None

    if not os.path.isdir(OUTPUTS_DIR):
        print("에러: outputs 디렉토리가 존재하지 않습니다.")
        return None

    subdirs = [
        os.path.join(OUTPUTS_DIR, d)
        for d in os.listdir(OUTPUTS_DIR)
        if os.path.isdir(os.path.join(OUTPUTS_DIR, d))
    ]
    pending = [d for d in subdirs if is_ready(d) and not is_done(d)]
    if pending:
        pending.sort(key=os.path.getmtime, reverse=True)
        print(f"[*] 자동으로 처리할 최신 미처리 폴더를 탐색했습니다: {pending[0]}")
        return pending[0]

    ready = [d for d in subdirs if is_ready(d)]
    if ready:
        ready.sort(key=os.path.getmtime, reverse=True)
        print(f"[*] 미처리 폴더가 없어 가장 최근 수정된 폴더를 선택했습니다: {ready[0]}")
        return ready[0]

    print("에러: 처리할 수 있는 폴더가 outputs/ 안에 없습니다.")
    return None
