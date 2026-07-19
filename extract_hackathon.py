import PyPDF2, os
pdf_path = r"C:\Users\RUKAYYAH IBRAHIM\Downloads\QwenCloud AI Hackathon.pdf"
out_path = r"C:\Users\RUKAYYAH IBRAHIM\video-agent-suite\hackathon_docs\QwenCloud_Hackathon.txt"
with open(pdf_path, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    text = ""
    for i, page in enumerate(reader.pages):
        text += f"\n--- Page {i+1} ---\n"
        text += page.extract_text() or "(empty)"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(text)
print(f"OK: {len(reader.pages)} pages, {len(text)} chars")
