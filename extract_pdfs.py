"""Extract text from all 4 hackathon PDFs."""
import PyPDF2
import os

pdfs = [
    r"C:\Users\RUKAYYAH IBRAHIM\Downloads\Agent Skills_Day_3.pdf",
    r"C:\Users\RUKAYYAH IBRAHIM\Downloads\Day_5_v3 (1).pdf",
    r"C:\Users\RUKAYYAH IBRAHIM\Downloads\Vibe Coding Agent Security and Evaluation_Day_4.pdf",
    r"C:\Users\RUKAYYAH IBRAHIM\Downloads\Agent Tools & Interoperability_Day_2.pdf",
]

output_dir = r"C:\Users\RUKAYYAH IBRAHIM\video-agent-suite\hackathon_docs"
os.makedirs(output_dir, exist_ok=True)

for pdf_path in pdfs:
    name = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = os.path.join(output_dir, f"{name}.txt")

    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for i, page in enumerate(reader.pages):
                text += f"\n--- Page {i+1} ---\n"
                text += page.extract_text() or "(empty page)"

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"OK: {name} ({len(reader.pages)} pages, {len(text)} chars)")
    except Exception as e:
        print(f"FAIL: {name} - {e}")
