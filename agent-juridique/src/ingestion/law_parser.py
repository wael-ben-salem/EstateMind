import re
import uuid
import json
import os
import sys
import io
import fitz  # PyMuPDF
import gc
import re
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import DocumentStream

# Fix path to allow imports from config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
try:
    from config.settings import QDRANT_URL, QDRANT_API_KEY, COHERE_API_KEY
except ImportError:
    QDRANT_URL = QDRANT_API_KEY = COHERE_API_KEY = None

class LawParser:
    def __init__(self, law_name="Unnamed Law"):
        self.law_name = law_name
        self.hierarchy = {"lvl1": "Général", "lvl2": "", "lvl3": ""}
        self.all_chunks = []
        self.current_chunk_text = []
        self.current_id = "Preamble"

    def _get_parsing_strategy(self, file_content: bytes):
        """Determine parsing strategy based on PDF content (encrypted, has text, etc.).
        
        Args:
            file_content: Raw bytes of the PDF file
            
        Returns:
            DocumentConverter with appropriate pipeline options
        """
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            
            # FIX: Utilisation de is_encrypted pour éviter le bug fz_has_permission
            is_locked = doc.is_encrypted
            
            # Vérification du texte (sur 3 pages max pour la rapidité)
            text_sample = ""
            for i in range(min(3, len(doc))):
                text_sample += doc[i].get_text().strip()
            
            # On considère qu'il n'y a pas de texte si l'échantillon est quasi vide
            has_text = len(text_sample) > 20 
            
            pipeline_options = PdfPipelineOptions()
            # Conseil : Gardez les tableaux pour le juridique, c'est souvent important
            pipeline_options.do_table_structure = True 
            
            if is_locked and not has_text:
                pipeline_options.do_ocr = True
                pipeline_options.ocr_options.force_full_page_ocr = True
            elif not has_text:
                pipeline_options.do_ocr = True
            else:
                pipeline_options.do_ocr = False

            doc.close()
            
            return DocumentConverter(
                format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
            )
        except Exception as e:
            return DocumentConverter() # Fallback standard

    def export_markdown(self, file_content: bytes, filename: str = "document.pdf"):
        """Extract markdown from PDF/image file content.
        
        Args:
            file_content: Raw bytes of the PDF or image file
            filename: Original filename (used for logging)
            
        Returns:
            Cleaned markdown string
        """
        converter = self._get_parsing_strategy(file_content)
        
        # Create DocumentStream from bytes
        source = DocumentStream(name=filename, stream=io.BytesIO(file_content))
        result = converter.convert(source)
        res = result.document.export_to_markdown()
        
        # Nettoyage des lignes
        cleaned_lines = []
        for line in res.split('\n'):
            cleaned_line = self._clean_line(line)
            if cleaned_line and cleaned_line.strip(): 
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
        
    

    def _is_summary_line(self, line):
        return "...." in line or "—" * 5 in line

    def _is_table_line(self, line):
        return "|" in line

    def _contains_image(self, line):
        return re.search(r'!\[.*\]\(data:image/[^)]+\)', line) is not None
    
    
    def _compact_table_separators(self, line):
        # If the line is a separator (only contains pipes, dashes, colons, or spaces)
        if re.match(r'^[\s|:-]+$', line):
            # Collapse multiple dashes to exactly three per cell
            return re.sub(r'-+', '---', line)
        # If it's a data line, just trim the internal padding
        return "| " + " | ".join(cell.strip() for cell in line.split("|") if cell.strip()) + " |"
    def _extract_universal_id(self, line):
        """Extracts Article IDs, Roman numerals, or Numerical IDs."""
        clean = re.sub(r'[#*]', '', line).strip()
        # Pattern for Article X or Art. X
        art_match = re.match(r'^(Article|Art\.)\s+(premier|\d+(?:\s*[a-z]+)?)', clean, re.I)
        if art_match:
            val = art_match.group(2).lower()
            return "1" if val == "premier" else val
        # Pattern for Roman (I.) or Numerical (1.1.)
        num_match = re.match(r'^([IVX]+|\d+(?:\.\d+)*)\.?\s+', clean, re.I)
        if num_match:
            return num_match.group(1).strip('.')
        return None

    def process_pdf(self, pdf_path, batch_size=10):
        converter = self._get_parsing_strategy(pdf_path)
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        output_file = "test_output.jsonl"
        
        with open(output_file, "w", encoding="utf-8") as f:
            pass

        print(f"📚 Total pages: {total_pages}. Batching by {batch_size}...")

        # FIX: Changed 5 to total_pages to process the whole document
        for start in range(0, total_pages, batch_size):
            end = min(start + batch_size, total_pages)
            print(f"⏳ Batch: Pages {start+1} to {end}...")

            batch_doc = fitz.open()
            batch_doc.insert_pdf(doc, from_page=start, to_page=end-1)
            pdf_bytes = batch_doc.tobytes()
            batch_doc.close()

            try:
                source = DocumentStream(name=f"b_{start}.pdf", stream=io.BytesIO(pdf_bytes))
                result = converter.convert(source)
                
                md_text = result.document.export_to_markdown()
                with open(f"debug_batch.md", "a", encoding="utf-8") as debug_file:
                    debug_file.write(md_text)
                    
                self._parse_lines(md_text.split('\n'))
                
                if self.all_chunks:
                    with open(output_file, "a", encoding="utf-8") as f:
                        for chunk in self.all_chunks:
                            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                    print(f"💾 Saved {len(self.all_chunks)} sections to disk.")
                    self.all_chunks = [] 

                if hasattr(result, 'input') and hasattr(result.input, '_backend'):
                    result.input._backend.unload()
                del result
                del md_text
                gc.collect()

            except Exception as e:
                print(f"❌ Batch Error at page {start}: {e}")

        if self.current_chunk_text:
            last_payload = self._create_payload(self.current_chunk_text, self.current_id)
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(last_payload, ensure_ascii=False) + "\n")

        doc.close()
        return output_file


    
    def _clean_line(self, line):
        # 1. DELETE THE LITERAL "/tatweel" STRING
        # This catches "/tatweel", "/tatweel/tatweel", etc.
        clean_line = re.sub(r'/?tatweel(/tatweel)*', '', line)

        # 2. DELETE ACTUAL ARABIC TATWEEL UNICODE
        clean_line = re.sub(r'\u0640', '', clean_line)

        # 3. DELETE IMAGE TAGS
        # We use [\s\S]*? to catch them even if there are weird hidden characters inside
        clean_line = re.sub(r'[\s\S]*?<!-- image -->[\s\S]*?', '', clean_line, flags=re.IGNORECASE)
        clean_line = re.sub(r'primerie Officielle de la République Tunisien', '', clean_line)
        # 4. FINAL STRIP
        clean_line = clean_line.strip()
        
        if self._is_table_line(clean_line):
            # 1. Compact it
            compacted = self._compact_table_separators(clean_line)
            
            # 2. Safety check: If it's literally just a pipe with nothing else, skip it.
            # But if it has the dashes (---), we MUST keep it.
            if compacted.strip() == "|" or not compacted.strip("|- "):
                if "---" not in compacted: # <--- This protects your separator!
                    return ""  # Return empty string to skip this line
            
            clean_line = compacted
        
        return clean_line




    def _parse_lines(self, lines):
        for line in lines:
            
            
            clean_line = self._clean_line(line)
            
            # Skip empty lines (returned from _clean_line when line should be ignored)
            if not clean_line:
                continue
                
            new_id = self._extract_universal_id(clean_line)
            
            
            if new_id:
                if self.current_chunk_text:
                    self.all_chunks.append(self._create_payload(self.current_chunk_text, self.current_id))
                
                self.current_chunk_text = [clean_line]
                self.current_id = new_id
                continue

            # Detect Major Hierarchy
            if re.match(r'^(#+\s*|TITRE|CHAPITRE|SECTION|LIVRE)', clean_line, re.I):
                content = clean_line.lstrip('# ').strip()
                if any(x in clean_line.upper() for x in ["TITRE", "LIVRE"]) or clean_line.startswith('# '):
                    self.hierarchy["lvl1"] = content
                    self.hierarchy["lvl2"], self.hierarchy["lvl3"] = "", ""
                else:
                    self.hierarchy["lvl2"] = content
                continue

            if self.current_chunk_text:
                self.current_chunk_text.append(clean_line)
            else:
                self.current_chunk_text = [clean_line]

    def _create_payload(self, text_list, section_id):
        # 1. Build the path
        parts = [self.hierarchy["lvl1"]]
        if self.hierarchy["lvl2"]:
            parts.append(self.hierarchy["lvl2"])
        if self.hierarchy["lvl3"]:
            parts.append(self.hierarchy["lvl3"])

        # 2. Append ID label
        if section_id not in ["General", "Preamble"]:
            # Check if the first line contains "Article" to decide the label
            label = f"Article {section_id}" if "Article" in text_list[0] else f"Section {section_id}"
            if label not in parts[-1]:
                parts.append(label)

        full_breadcrumb = " > ".join(parts)

        return {
            "id": section_id,
            "breadcrumb": full_breadcrumb,
            "text": "\n".join(text_list),
            "source": self.law_name
        }

if __name__ == "__main__":
    TEST_PDF = "data\\juridique_files\\code_des_droits_reels_tunisie.pdf" 
    
    if os.path.exists(TEST_PDF):
        # Use a batch size of 2 for safety as we discussed
        parser = LawParser("Droits de reels Tunisie")
        jsonl_file_path = parser.process_pdf(TEST_PDF, batch_size=2)
        
        print(f"🔄 Converting JSONL to final JSON...")
        final_data = []
        with open(jsonl_file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    final_data.append(json.loads(line))
        
        with open("test_output.json", "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        
        print(f"✅ DONE! Total Sections: {len(final_data)}")
    else:
        print(f"❌ File not found: {TEST_PDF}")