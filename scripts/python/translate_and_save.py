import os
from deep_translator import GoogleTranslator
from datetime import datetime

# Define paths
extracted_text_path = "/Users/jaewansim/Documents/nerdlab/pattern_language_extracted_20251015_190014.txt"
output_dir = "/Users/jaewansim/Documents/nerdlab"

# Read the extracted text
with open(extracted_text_path, 'r', encoding='utf-8') as f:
    text_to_translate = f.read()

print(f"텍스트 파일 읽기 완료. 번역할 텍스트 길이: {len(text_to_translate):,}자")

# Initialize translator
translator = GoogleTranslator(source='en', target='ko')

# Translate the text
# GoogleTranslator has a character limit per request, so split if necessary
# The documentation for deep_translator suggests it handles chunking internally for GoogleTranslator
# However, to be safe, I will manually chunk if the text is very long.
# Let's assume a safe chunk size of 4500 characters (Google Translate API limit is 5000 per request, but deep_translator might have its own internal handling)
chunk_size = 4500
translated_chunks = []

for i in range(0, len(text_to_translate), chunk_size):
    chunk = text_to_translate[i:i + chunk_size]
    print(f"번역 중... (청크 {i // chunk_size + 1}/{(len(text_to_translate) + chunk_size - 1) // chunk_size})")
    translated_chunk = translator.translate(chunk)
    translated_chunks.append(translated_chunk)

translated_text = "".join(translated_chunks)

print("번역 완료.")

# Save the translated text
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
translated_file_name = f"pattern_language_korean_translation_{timestamp}.txt"
translated_file_path = os.path.join(output_dir, translated_file_name)

with open(translated_file_path, 'w', encoding='utf-8') as f:
    f.write(translated_text)

print(f"번역된 텍스트 저장 완료: {translated_file_path}")