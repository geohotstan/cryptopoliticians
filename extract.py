import fitz
import pathlib
import pymupdf

fname ="/Users/zibo/fun/money/bitcoin-politicians/data/house_of_representatives/reports/2024/Altekar_Girish/3-24-2024_10056916.pdf"
# doc = fitz.open() # open a document
# for page in doc:
#     tabs = page.find_tables()
#     for tab in tabs:
#         print(tab.to_pandas())

# with pymupdf.open(fname) as doc:  # open document
#     text = chr(12).join([page.get_text() for page in doc])
# # write as a binary file to support non-ASCII characters
# pathlib.Path(fname + ".txt").write_bytes(text.encode())

doc = fitz.open(fname)
text = ""
for page_num in range(doc.page_count):
    page = doc.load_page(page_num)
    text += page.get_text()

print(text)
# import openai