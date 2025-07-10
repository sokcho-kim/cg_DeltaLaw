# === 개선된 배치 처리 코드 ===
# 이 코드를 Jupyter 노트북의 새로운 셀에 복사하여 사용하세요

import re
import pdfplumber
import csv
from difflib import SequenceMatcher
import os

# === 실행 ===

folder_path = r"C:\Jimin\cg_DeltaLaw\data\no_upload"
output_folder = r"C:\Jimin\cg_DeltaLaw\data\processed"

# 출력 폴더 생성
os.makedirs(output_folder, exist_ok=True)

# PDF 파일만 필터링
file_list = os.listdir(folder_path)
pdf_files = [f for f in file_list if f.lower().endswith('.pdf')]

print(f"처리할 PDF 파일 수: {len(pdf_files)}")
print(f"입력 폴더: {folder_path}")
print(f"출력 폴더: {output_folder}")
print("-" * 50)

# 파일별 처리
success_count = 0
error_count = 0

for i, file_name in enumerate(pdf_files, 1):
    print(f"[{i}/{len(pdf_files)}]")
    
    try:
        file_path = os.path.join(folder_path, file_name)
        law_name = os.path.splitext(file_name)[0]
        
        print(f"  처리 중: {file_name}")
        
        # 좌우 열 추출
        left, right = extract_left_right_columns(file_path)
        if not left and not right:
            print(f"    건너뜀: 텍스트 추출 실패")
            error_count += 1
            continue
            
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
        
        # 결과 저장 (파일명에 법률명 포함)
        output_filename = f"조문_비교결과_{law_name}.csv"
        output_path = os.path.join(output_folder, output_filename)
        save_to_csv(results, output_path, law_name=law_name)
        
        print(f"    저장 완료: {output_filename}")
        success_count += 1
        
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