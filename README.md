# Delta(Δ) + Law : 법률 개정안 실시간 추적 시스템

법률안 및 시행령/행정규칙 개정안의 실시간 추적을 위한 시스템입니다.

## 🎯 프로젝트 목표

### Mark 1: 신구조문대비표 추출 및 변경사항 분석
- **주요 목표**: PDF 형태의 신구조문대비표에서 조문 변경사항을 자동으로 추출하고 분석
- **핵심 기능**:
  - PyMuPDF, pdfplumber를 활용한 표 추출
  - 조/항/호/목 단위의 변경사항 추적
  - 변경/신설/삭제/이동 유형 자동 분류

### 향후 계획
- 실시간 법률안 추적 시스템 구축
- 웹 기반 대시보드 개발
- API 서비스 제공

## 📁 프로젝트 구조

```
cg_DeltaLaw/
├── data/                   # 데이터 저장소
│   ├── raw/                # 원본 PDF 파일들
│   └── processed/          # 처리된 결과물
├── scripts/                # 핵심 스크립트
│   ├── extract_table.py    # 표 추출 모듈
│   ├── diff_parser.py      # 조문 변경 분석
│   └── utils.py            # 공통 유틸리티
├── origin/                 # 원본 개발 코드
│   ├── 법률명까지신구조문대비표.py
│   └── 변경신설삭제이동.py
├── notebooks/              # Jupyter 노트북
└── requirements.txt        # 의존성 패키지
```

## 🛠️ 기술 스택

### Mark 1 핵심 기술
- **PDF 처리**: PyMuPDF, pdfplumber
- **데이터 처리**: pandas, numpy
- **텍스트 분석**: re (정규표현식)
- **파일 처리**: openpyxl (Excel 출력)

### 개발 환경
- **언어**: Python 3.x
- **패키지 관리**: pip
- **개발 도구**: Jupyter Notebook

## 🚀 사용 방법

### 1. 환경 설정
```bash
pip install -r requirements.txt
```

### 2. 신구조문대비표 추출
```python
from scripts.extract_table import extract_law_table_auto

# PDF 파일에서 표 추출
extract_law_table_auto("input.pdf", "output.xlsx")
```

### 3. 변경사항 분석
```python
from scripts.diff_parser import analyze_changes

# 추출된 표에서 변경사항 분석
analyze_changes("extracted_table.xlsx")
```

## 📊 주요 기능

### 표 추출 기능
- **표 기반 추출**: PDF 내 표 구조를 인식하여 신구조문대비표 추출
- **조문블록 추출**: 표 인식 실패 시 조문 단위로 텍스트 블록 추출
- **자동 법령명 인식**: PDF 첫 페이지에서 법령명 자동 추출

### 변경사항 분석
- **조/항/호/목 단위 분석**: 세부 조문 구조별 변경사항 추적
- **변경 유형 분류**: 변경/신설/삭제/이동/현행과 같음 자동 판정
- **중복 제거**: 동일한 변경사항의 중복 처리

## 📈 처리 통계

시스템은 다음과 같은 통계를 제공합니다:
- 표 기반 추출 성공률
- 조문블록 fallback 사용률
- 전체 처리 실패율
- 변경 유형별 분포

## 🔧 개발 가이드

### 새로운 기능 추가
1. `scripts/` 폴더에 새로운 모듈 추가
2. `utils.py`에 공통 함수 정의
3. 테스트를 위한 노트북 생성

### 데이터 형식
- **입력**: PDF 파일 (신구조문대비표 포함)
- **출력**: Excel 파일 (추출된 표 + 변경사항 분석)

## 📝 라이선스

이 프로젝트는 내부 개발용으로 제작되었습니다.

## 🤝 기여

프로젝트 개선을 위한 제안사항은 이슈로 등록해 주세요.

---

**Delta(Δ) + Law** - 법률 개정의 변화를 실시간으로 추적합니다. 
