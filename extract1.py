import pymupdf
from pathlib import Path

dataset_path = Path(__file__).parent
pdf_files = sorted(dataset_path.glob("*.pdf"))

print(f"Found {len(pdf_files)} PDF files:\n")

for i, pdf in enumerate(pdf_files, start=1):
    print(f"{i}. {pdf.name}")

choice = int(input("\nEnter PDF number to process: "))

pdf_path = pdf_files[choice - 1]

print(f"\nProcessing: {pdf_path.name}")

doc = pymupdf.open(pdf_path)

print(f"Number of pages: {len(doc)}")

# Save extracted text instead of only printing it
output_file = dataset_path / "raw_extracted.txt"

with open(output_file, "w", encoding="utf-8") as f:

    for page_number, page in enumerate(doc, start=1):

        text = page.get_text("text")

        f.write("\n" + "=" * 70 + "\n")
        f.write(f"PAGE {page_number}\n")
        f.write("=" * 70 + "\n")
        f.write(text)

doc.close()

print(f"\n✅ Extraction completed!")
print(f"📄 Saved to: {output_file}")