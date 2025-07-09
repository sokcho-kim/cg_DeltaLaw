import pdfplumber
import pandas as pd
import os
import re
from collections import defaultdict, Counter

def normalize_text(text):
    return (
        text.replace("ㆍ", "·")
            .replace(" ", "")
            .replace("\n", "")
    )

def is_meaningless_dash_row(left, right):
    return all(re.fullmatch(r'[-‐‑‒–—−\s]*', side or '') for side in [left, right])

def clean_page_numbers(text):
    if not isinstance(text, str):
        return text
    return re.sub(r'-\s*\d+\s*-?', '', text).strip()

def extract_law_name(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        if not text:
            return "-"
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line for keyword in ["법률", "개정", "시행령", "시행규칙"]):
                return line.strip()
    return "-"

def extract_table_style(pdf_path, start_keyword="신ㆍ구조문대비표", line_tol=2):
    result_rows = []
    capturing = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if not capturing and normalize_text(start_keyword) in normalize_text(text):
                capturing = True

            if capturing:
                words = page.extract_words()
                if not words:
                    continue

                line_map = defaultdict(lambda: {'left': '', 'right': ''})
                midpoint = page.width / 2

                for word in words:
                    top_key = round(word['top'] / line_tol) * line_tol
                    if word['x0'] < midpoint:
                        line_map[top_key]['left'] += ' ' + word['text']
                    else:
                        line_map[top_key]['right'] += ' ' + word['text']

                for top in sorted(line_map.keys()):
                    left = clean_page_numbers(line_map[top]['left'].strip())
                    right = clean_page_numbers(line_map[top]['right'].strip())
                    if not is_meaningless_dash_row(left, right):
                        result_rows.append([left, right])

    return result_rows

def extract_text_by_clause_blocks(pdf_path, start_keyword="신ㆍ구조문대비표", max_follow_pages=3):
    capturing = False
    data_pairs = []
    current_left, current_right = [], []
    side = "left"
    follow_page_count = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                line_clean = line.strip()
                if not capturing:
                    if normalize_text(start_keyword) in normalize_text(line):
                        capturing = True
                    continue
                if not line_clean:
                    continue

                if re.match(r"^제?\d+조", line_clean) or re.match(r"^[\u2460-\u2473\d]+", line_clean) or line_clean.startswith("현행"):
                    if current_left or current_right:
                        l = clean_page_numbers(" ".join(current_left).strip())
                        r = clean_page_numbers(" ".join(current_right).strip())
                        if not is_meaningless_dash_row(l, r):
                            data_pairs.append([l, r])
                        current_left, current_right = [], []
                    side = "left"
                    current_left.append(line_clean)
                elif "개정안" in line_clean or "현행과 같음" in line_clean or "----------------" in line_clean:
                    side = "right"
                else:
                    if side == "left":
                        current_left.append(line_clean)
                    else:
                        current_right.append(line_clean)

            if capturing:
                follow_page_count += 1
                if follow_page_count >= max_follow_pages:
                    break

        if current_left or current_right:
            l = clean_page_numbers(" ".join(current_left).strip())
            r = clean_page_numbers(" ".join(current_right).strip())
            if not is_meaningless_dash_row(l, r):
                data_pairs.append([l, r])

    return data_pairs

def save_final(output_path, data_rows, law_name, method_name=None, add_header=False):
    if not data_rows:
        return False

    # 중복된 "현행" + "개정안" row 제거 로직
    cleaned_rows = []
    seen = set()
    for row in data_rows:
        if isinstance(row, list) and len(row) >= 2:
            key = (row[0], row[1])
            if key not in seen:
                cleaned_rows.append(row)
                seen.add(key)
        elif isinstance(row, str):
            cleaned_rows.append([row.strip(), ""])

    # 첫 행에만 법령명 포함, 중복 방지
    final_rows = [["신ㆍ구조문대비표", law_name]]
    for row in cleaned_rows:
        # "신ㆍ구조문대비표" 행 제거 (2번째 이상 등장 시)
        if normalize_text(row[0]) == normalize_text("신ㆍ구조문대비표"):
            continue
        final_rows.append([row[0].strip(), row[1].strip()])

    df_main = pd.DataFrame(final_rows)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_main.to_excel(writer, index=False, header=False, sheet_name="신구대비표")
        if method_name:
            pd.DataFrame([["추출 방식", method_name]]).to_excel(
                writer, index=False, header=False, sheet_name="정보"
            )
    return True


results = []

def extract_law_table_auto(pdf_path, output_path):
    base = os.path.basename(pdf_path)
    law_name = extract_law_name(pdf_path)

    rows = extract_table_style(pdf_path)
    if rows and len(rows) > 2:
        print(f"✅ [표 기반] 추출 성공: {base}")
        if save_final(output_path, rows, law_name):
            results.append((base, "표 기반", law_name))
            return
    rows = extract_text_by_clause_blocks(pdf_path)
    if rows and len(rows) > 2:
        print(f"✅ [조문블록 fallback] 추출 성공: {base}")
        if save_final(output_path, rows, law_name, method_name="조문블록 fallback", add_header=True):
            results.append((base, "조문블록 fallback", law_name))
            return
    print(f"❌ 최종 추출 실패: {base}")
    results.append((base, "실패", law_name))

def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            name_only = os.path.splitext(filename)[0]
            output_path = os.path.join(output_folder, f"{name_only}_신구대비표.xlsx")
            extract_law_table_auto(pdf_path, output_path)
    summary = Counter(method for _, method, _ in results)
    print("\n📊 처리 통계 요약")
    for method in ["표 기반", "조문블록 fallback", "실패"]:
        print(f"{method:>15}: {summary.get(method, 0)}건")
    failed = [name for name, method, _ in results if method == "실패"]
    if failed:
        print("\n❗ 실패한 파일 목록:")
        for name in failed:
            print(f"- {name}")

if __name__ == "__main__":
    input_folder = r"D:\\1.씨지인사이드\\1. 제안 업무\\15. IBK 퍼스트랩\\pdftable"
    output_folder = r"D:\\1.씨지인사이드\\1. 제안 업무\\15. IBK 퍼스트랩\\pdftable"
    process_folder(input_folder, output_folder)
