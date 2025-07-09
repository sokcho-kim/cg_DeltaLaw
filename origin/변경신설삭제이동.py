import pandas as pd
import re
import os

# 🔧 placeholder 판정 함수
def is_placeholder(token):
    return (
        re.fullmatch(r'[\-\_\.\,\s]+', token) or  # placeholder + 구두점 + space
        re.fullmatch(r'[①-⑩]', token) or        # 항 번호
        re.fullmatch(r'\d+\.', token) or         # 호 번호
        re.fullmatch(r'[가-하]', token)           # 목 번호
    )

# 🔧 조문 병합 함수
def merge_rows(df, col):
    merged_texts = []
    temp_text = ""
    for _, row in df.iterrows():
        line = str(row[col]).strip()
        if re.match(r'^제\d+조', line) or re.match(r'^\d+\.', line) or re.match(r'^[①-⑩]', line):
            if temp_text:
                merged_texts.append(temp_text.strip())
                temp_text = line
            else:
                temp_text = line
        else:
            temp_text += " " + line
    if temp_text:
        merged_texts.append(temp_text.strip())
    return merged_texts

# 🔧 폴더 내 모든 파일 처리 함수
def process_files_in_folder(folder_path):
    all_results = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.xlsx') and not filename.startswith('~$'):
            file_path = os.path.join(folder_path, filename)
            print(f"🔍 Processing: {file_path}")

            try:
                df = pd.read_excel(file_path, header=1)
                current_col = '현 행'
                revised_col = '개 정 안'

                current_merged = merge_rows(df, current_col)
                revised_merged = merge_rows(df, revised_col)

                for cur, rev in zip(current_merged, revised_merged):
                    rev_strip = rev.strip()
                    lines = rev_strip.splitlines()
                    content_tokens = [t for t in re.split(r'\s+', rev_strip) if t]

                    # 🔧 변경유형 판정 우선순위 (최종)
                    if re.search(r'\(현행과 같음\)', rev_strip) or re.search(r'\(생략\)', rev_strip):
                        result = "현행"
                    elif (
                        len(content_tokens) == 1 and
                        re.match(r'^제\d+조', content_tokens[0])
                    ):
                        result = "변경"
                    elif (
                        len(content_tokens) > 1 and
                        re.match(r'^제\d+조', content_tokens[0]) and
                        all(is_placeholder(t) for t in content_tokens[1:])
                    ):
                        result = "현행"
                    elif (
                        all(is_placeholder(t) for t in content_tokens)
                    ):
                        result = "현행"
                    elif (
                        any(re.search(r'[가-힣a-zA-Z0-9]', t) for t in content_tokens if not is_placeholder(t))
                    ):
                        result = "변경"
                    else:
                        result = "현행"

                    print(f"✅ {filename} | 변경유형: {result}")

                    all_results.append({
                        "파일명": filename,
                        "현행": cur,
                        "개정안": rev,
                        "변경유형": result
                    })

            except Exception as e:
                print(f"[Error] 파일 처리 실패 ({filename}): {e}")

    # 🔧 결과 DataFrame 저장
    df_out = pd.DataFrame(all_results)
    output_path = os.path.join(folder_path, 'output_llm_change_type_only_all.xlsx')
    df_out.to_excel(output_path, index=False)
    print(f"✅ 모든 파일 처리 완료. 결과 저장: {output_path}")

if __name__ == "__main__":
    folder_path = r"D:\1.씨지인사이드\1. 제안 업무\15. IBK 퍼스트랩\pdftable\추출본"
    process_files_in_folder(folder_path)
