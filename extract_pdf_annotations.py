import fitz  # PyMuPDF
import argparse
import os
from pathlib import Path

def find_latest_pdf_in_downloads():
    """
    Finds the most recently modified PDF file in the user's Downloads directory.
    
    Returns:
        Path object to the latest PDF, or None if not found.
    """
    # Use pathlib to create a cross-platform path to the Downloads folder
    downloads_dir = Path.home() / "Downloads"

    if not downloads_dir.is_dir():
        print(f"Error: Downloads directory not found at '{downloads_dir}'")
        return None

    # Find all PDF files in the directory
    # The glob pattern '*.pdf' is generally case-insensitive on Windows, but might be
    # case-sensitive on Linux/macOS. For broader compatibility, you could use '*.[pP][dD][fF]'.
    pdf_files = list(downloads_dir.glob('*.pdf'))

    if not pdf_files:
        print(f"No PDF files found in '{downloads_dir}'")
        return None

    # Find the latest file based on modification time
    try:
        latest_file = max(pdf_files, key=os.path.getmtime)
        print(f"Found latest PDF: {latest_file.name}")
        return latest_file
    except Exception as e:
        print(f"Error finding the latest file: {e}")
        return None


def extract_full_annotations(pdf_path):
    """
    Precisely extracts highlighted text AND any associated comments/pop-up notes
    from a PDF file.
    """
    try:
        # Convert path to string, as fitz.open() works best with strings
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        print(f"Error opening PDF file '{pdf_path}': {e}")
        return

    print(f"--- Full Annotations (Text + Comments) for {pdf_path.name} ---")

    # Iterate through each page of the document
    for page_num, page in enumerate(doc.pages()):
        # We will store results in a list of dictionaries to keep data paired
        page_results = []
        other_annots = []

        # Get all words on the page with their coordinates for precise matching
        words_on_page = page.get_text("words")
        
        annotations = list(page.annots())
        if not annotations:
            continue

        print(f"\n[Page {page_num + 1}]")

        for annot in annotations:
            # --- 1. Handle Highlight Annotations and their Comments ---
            if annot.type[0] == 8:  # 8 = Highlight
                highlighted_words = []
                
                highlight_quads = [fitz.Quad(annot.vertices[i:i+4]) for i in range(0, len(annot.vertices), 4)]
                
                for word_coords in words_on_page:
                    word_rect = fitz.Rect(word_coords[:4])
                    word_text = word_coords[4]
                    
                    for quad in highlight_quads:
                        # Check if the word's rectangle intersects with the highlight's quad
                        if quad.rect.intersects(word_rect):
                            highlighted_words.append(word_text)
                            break
                
                # Get the associated comment text and author from the annotation's info
                comment_text = annot.info.get("content", "")
                author = annot.info.get("title", "Unknown Author")
                
                if highlighted_words:
                    full_text = " ".join(highlighted_words)
                    page_results.append({
                        "text": full_text,
                        "comment": comment_text,
                        "author": author
                    })

            # --- 2. Handle Other Annotation Types ---
            elif annot.type[0] == 14: # 14 = Ink (Graphical Markup)
                other_annots.append("Graphical Markup (Ink Drawing) found.")
            
        # --- 3. Print the results for the page in a structured way ---
        if page_results:
            print("  --- Highlights & Comments ---")
            # Use a set to track printed text and avoid duplicates from overlapping annots
            printed_texts = set()
            for result in page_results:
                if result["text"] not in printed_texts:
                    print(f'  - Highlighted: "{result["text"]}"')
                    if result["comment"]:
                        print(f'    └── Comment (by {result["author"]}): "{result["comment"]}"')
                    printed_texts.add(result["text"])
        
        if other_annots:
            print("  --- Other Markups ---")
            for note in sorted(list(set(other_annots))):
                print(f"  - {note}")


def main():
    """
    Main function to handle command-line arguments and run the extraction.
    """
    parser = argparse.ArgumentParser(
        description="Extract highlights and comments from a PDF file. "
                    "By default, it processes the most recent PDF in your ~/Downloads folder."
    )
    # Add an argument for the PDF path.
    # 'nargs="?"' makes it optional.
    # 'default=None' means if it's not provided, the value will be None.
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default=None,
        help="Path to the PDF file. If omitted, the latest PDF in ~/Downloads will be used."
    )

    args = parser.parse_args()

    target_pdf_path = None

    if args.pdf_path:
        # User provided a specific path
        target_pdf_path = Path(args.pdf_path)
    else:
        # No path provided, use the default behavior
        print("No PDF path provided. Searching for the latest PDF in ~/Downloads...")
        target_pdf_path = find_latest_pdf_in_downloads()

    if target_pdf_path:
        if target_pdf_path.is_file():
            extract_full_annotations(target_pdf_path)
        else:
            print(f"Error: File not found at '{target_pdf_path}'")
    else:
        # This message is printed if the default search fails
        print("Could not determine a PDF file to process. Exiting.")

# --- SCRIPT ENTRY POINT ---
if __name__ == "__main__":
    main()