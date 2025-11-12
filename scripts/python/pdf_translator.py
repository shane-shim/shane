import PyPDF2
import pdfplumber
import os
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF using multiple methods
    """
    print(f"PDF 파일 읽는 중: {pdf_path}")
    
    text = ""
    
    # Method 1: Try pdfplumber first (better for complex layouts)
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                print(f"페이지 {i+1}/{len(pdf.pages)} 추출 중...")
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n--- 페이지 {i+1} ---\n\n"
                    text += page_text
        
        if text.strip():
            print("pdfplumber로 텍스트 추출 성공")
            return text
    except Exception as e:
        print(f"pdfplumber 오류: {e}")
    
    # Method 2: Try PyPDF2 as fallback
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for i in range(num_pages):
                print(f"페이지 {i+1}/{num_pages} 추출 중...")
                page = pdf_reader.pages[i]
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n--- 페이지 {i+1} ---\n\n"
                    text += page_text
        
        if text.strip():
            print("PyPDF2로 텍스트 추출 성공")
            return text
    except Exception as e:
        print(f"PyPDF2 오류: {e}")
    
    return text

def translate_section(text, section_name=""):
    """
    Translate a section of text - placeholder for translation logic
    """
    # 여기서는 텍스트를 그대로 반환하지만, 
    # 실제로는 번역 API나 모델을 사용할 수 있습니다
    print(f"'{section_name}' 섹션 번역 중...")
    return text

def save_translation(original_text, translated_text, output_path):
    """
    Save translation results
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== 원문 ===\n\n")
        f.write(original_text)
        f.write("\n\n=== 번역문 ===\n\n")
        f.write(translated_text)
    
    print(f"번역 결과 저장: {output_path}")

def main(pdf_path_arg):
    pdf_path = pdf_path_arg
    
    if not os.path.exists(pdf_path):
        print(f"파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("PDF에서 텍스트를 추출할 수 없습니다.")
        print("스캔된 이미지 PDF일 수 있습니다. OCR이 필요할 수 있습니다.")
        return
    
    # Save extracted text
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extracted_path = f"/Users/jaewansim/Documents/nerdlab/pattern_language_extracted_{timestamp}.txt"
    
    with open(extracted_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"\n추출된 텍스트 저장: {extracted_path}")
    print(f"추출된 텍스트 길이: {len(text):,}자")
    
    # Show first 1000 characters
    print("\n=== 추출된 텍스트 미리보기 (처음 1000자) ===")
    print(text[:1000])
    print("...")

if __name__ == "__main__":
    main()