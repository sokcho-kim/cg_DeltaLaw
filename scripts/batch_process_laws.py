import re
import pdfplumber
import csv
from difflib import SequenceMatcher
import os
from pathlib import Path


def extract_left_right_columns(pdf_path):
    """
    PDF에서 신구조문대비표 영역의 좌측(현행) / 우측(개정) 열을 나누어 추출
    """
    left_clauses, right_clauses = [], []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                if not words:
                    continue
                midpoint = (page.bbox[2] - page.bbox[0]) / 2
                left_lines = {}
                right_lines = {}
                for w in words:
                    y0 = round(w["top"])
                    text = w["text"].strip()
                    if not text:
                        continue
                    target = left_lines if w["x0"] < midpoint else right_lines
                    if y0 not in target:
                        target[y0] = []
                    target[y0].append(text)
                for y in sorted(left_lines):
                    left_clauses.append(" ".join(left_lines[y]))
                for y in sorted(right_lines):
                    right_clauses.append(" ".join(right_lines[y]))
    except Exception as e:
        print(f"    PDF 읽기 오류: {str(e)}")
        return [], []
    
    return left_clauses, right_clauses


def merge_by_clause(lines):
    """제XX조, ①, 1. 기준으로 조문 묶기"""
    clause_blocks = []
    current_clause = ""
    clause_id = ""
    
    for line in lines:
        if re.match(r"제\d+조", line):
            if current_clause:
                clause_blocks.append((clause_id, current_clause.strip()))
            clause_id = re.findall(r"제\d+조(?:\s*제\d+항)?", line)[0]
            current_clause = line
        elif re.match(r"[\(\[]?\d+[\)\.]", line) or re.match(r"[\u2460-\u2473]", line):
            current_clause += "\n" + line
        else:
            current_clause += " " + line
    
    if current_clause:
        clause_blocks.append((clause_id, current_clause.strip()))
    
    return clause_blocks


def compare_clauses(old_clauses, new_clauses, threshold=0.85):
    """
    조문 ID 기준으로 비교 후 변경 유형 분류
    """
    results = []
    old_dict = {cid: text for cid, text in old_clauses}
    new_ids = set(cid for cid, _ in new_clauses)

    for cid, new_text in new_clauses:
        old_text = old_dict.get(cid)
        if old_text:
            sim = SequenceMatcher(None, old_text, new_text).ratio()
            if sim < threshold:
                results.append((cid, old_text, new_text, "변경"))
            else:
                results.append((cid, old_text, new_text, "동일"))
        else:
            results.append((cid, "", new_text, "신설"))

    for cid, old_text in old_clauses:
        if cid not in new_ids:
            results.append((cid, old_text, "", "삭제"))

    return results


def save_to_csv(data, path, law_name=""):
    """결과를 CSV 파일로 저장"""
    try:
        with open(path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["법률명", "조문ID", "현행", "개정", "변경유형"])
            for cid, old, new, chg in data:
                writer.writerow([law_name, cid, old, new, chg])
        return True
    except Exception as e:
        print(f"    CSV 저장 오류: {str(e)}")
        return False


def process_law_file(file_path, output_dir):
    """개별 법률 파일 처리"""
    file_name = os.path.basename(file_path)
    law_name = os.path.splitext(file_name)[0]
    
    print(f"  처리 중: {file_name}")
    
    # 좌우 열 추출
    left, right = extract_left_right_columns(file_path)
    if not left and not right:
        print(f"    건너뜀: 텍스트 추출 실패")
        return False
    
    print(f"    좌측 조문 수: {len(left)}, 우측 조문 수: {len(right)}")
    
    # 조문 단위로 묶기
    old_clauses = merge_by_clause(left)
    new_clauses = merge_by_clause(right)
    print(f"    현행 조문 블록: {len(old_clauses)}, 개정 조문 블록: {len(new_clauses)}")
    
    # 비교 분석
    results = compare_clauses(old_clauses, new_clauses)
    print(f"    분석 결과: {len(results)}개 항목")
    
    # 변경 유형별 통계
    change_types = {}
    for _, _, _, chg_type in results:
        change_types[chg_type] = change_types.get(chg_type, 0) + 1
    
    print(f"    변경 유형: {change_types}")
    
    # 결과 저장
    output_filename = f"조문_비교결과_{law_name}.csv"
    output_path = os.path.join(output_dir, output_filename)
    
    if save_to_csv(results, output_path, law_name):
        print(f"    저장 완료: {output_filename}")
        return True
    else:
        return False


def main():
    """메인 실행 함수"""
    # 경로 설정
    input_folder = r"C:\Jimin\cg_DeltaLaw\data\no_upload"
    output_folder = r"C:\Jimin\cg_DeltaLaw\data\processed"
    
    # 출력 폴더 생성
    os.makedirs(output_folder, exist_ok=True)
    
    # PDF 파일 목록 가져오기
    try:
        file_list = os.listdir(input_folder)
        pdf_files = [f for f in file_list if f.lower().endswith('.pdf')]
    except Exception as e:
        print(f"폴더 읽기 오류: {str(e)}")
        return
    
    print(f"처리할 PDF 파일 수: {len(pdf_files)}")
    print(f"입력 폴더: {input_folder}")
    print(f"출력 폴더: {output_folder}")
    print("-" * 50)
    
    # 파일별 처리
    success_count = 0
    error_count = 0
    
    for i, file_name in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}]")
        
        file_path = os.path.join(input_folder, file_name)
        
        # 파일 존재 확인
        if not os.path.isfile(file_path):
            print(f"  건너뜀: {file_name} (파일이 존재하지 않음)")
            error_count += 1
            continue
        
        # 파일 처리
        try:
            if process_law_file(file_path, output_folder):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"  오류 발생: {file_name} - {str(e)}")
            error_count += 1
        
        print()  # 빈 줄로 구분
    
    # 결과 요약
    print("=" * 50)
    print("처리 완료!")
    print(f"성공: {success_count}개 파일")
    print(f"실패: {error_count}개 파일")
    print(f"총 처리: {len(pdf_files)}개 파일")
    print(f"결과 파일 위치: {output_folder}")


if __name__ == "__main__":
    main() 