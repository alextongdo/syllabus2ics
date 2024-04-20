import fitz # PyMyPDF
from syllabus2ics.pymupdf_rag import to_markdown

def extract_text_from_pdf(file_bytes, markdown=False):
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        if markdown:
            text = to_markdown(doc)
        else:
            text = chr(12).join([page.get_text() for page in doc])
    return text

if __name__ == '__main__':
    # You have to read the pdf bytes first
    with open("input.pdf", "rb") as f:
        bytes = f.read()

    # Then you can extract text
    bruh = extract_text_from_pdf(bytes, markdown=True)
    print(bruh)
