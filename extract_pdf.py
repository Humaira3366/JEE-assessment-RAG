import pymupdf
from pathlib import Path

dataset_path = Path(__file__).parent

pdf_files = sorted(dataset_path.glob("*.pdf"))

print(f"Found {len(pdf_files)} PDF files:\n")

for i, pdf in enumerate(pdf_files, start=1):
    print(f"{i}. {pdf.name}")

# Choose which PDF to process
choice = int(input("\nEnter PDF number to process: "))

pdf_path = pdf_files[choice - 1]

print(f"\nProcessing: {pdf_path.name}")

doc = pymupdf.open(pdf_path)

print(f"Number of pages: {len(doc)}")

for page_number, page in enumerate(doc, start=1):

    text = page.get_text()

    print("\n" + "=" * 70)
    print(f"PAGE {page_number}")
    print("=" * 70)

    print(text[:3000])

doc.close()

print("\n✅ PDF extraction completed.")