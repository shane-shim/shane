import sys
import os
from datetime import datetime

# Add the directory containing pdf_translator.py to the Python path
sys.path.append(os.path.dirname("/Users/jaewansim/Documents/nerdlab/pdf_translator.py"))

import pdf_translator

pdf_path = "/Users/jaewansim/Documents/nerdlab/패턴랭귀지_wiki.pdf"

# Call the main function with the PDF path
pdf_translator.main(pdf_path)