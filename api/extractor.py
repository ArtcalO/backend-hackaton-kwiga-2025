#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import argparse
from typing import List, Optional, Union
import logging

try:
    import PyPDF2
    import pdfplumber
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    print("Warning: PDF libraries not installed. Install with: pip install PyPDF2 pdfplumber")

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("Warning: OCR libraries not installed. Install with: pip install pytesseract pillow opencv-python")

try:
    import fitz 
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

class TextExtractor:
    """Main class for extracting text from PDFs and images"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize the text extractor
        
        Args:
            tesseract_path: Path to tesseract executable (optional)
        """
        self.setup_logging()
        
        if tesseract_path and HAS_OCR:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Supported file extensions
        self.pdf_extensions = {'.pdf'}
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif'}
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def is_pdf(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a PDF"""
        return Path(file_path).suffix.lower() in self.pdf_extensions
    
    def is_image(self, file_path: Union[str, Path]) -> bool:
        """Check if file is an image"""
        return Path(file_path).suffix.lower() in self.image_extensions
    
    def extract_text_from_pdf_pypdf2(self, pdf_path: Union[str, Path]) -> str:
        """Extract text from PDF using PyPDF2"""
        if not HAS_PDF:
            raise ImportError("PyPDF2 not installed")
        
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page.extract_text()
                    
        except Exception as e:
            self.logger.error(f"Error with PyPDF2: {e}")
            raise
            
        return text
    
    def extract_text_from_pdf_pdfplumber(self, pdf_path: Union[str, Path]) -> str:
        """Extract text from PDF using pdfplumber (better for tables)"""
        if not HAS_PDF:
            raise ImportError("pdfplumber not installed")
        
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text += f"\n--- Page {page_num + 1} ---\n"
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                    
                    # Extract tables if present
                    tables = page.extract_tables()
                    for table in tables:
                        text += "\n--- Table ---\n"
                        for row in table:
                            if row:
                                text += " | ".join(str(cell) if cell else "" for cell in row) + "\n"
                        
        except Exception as e:
            self.logger.error(f"Error with pdfplumber: {e}")
            raise
            
        return text
    
    def extract_text_from_pdf_pymupdf(self, pdf_path: Union[str, Path]) -> str:
        """Extract text from PDF using PyMuPDF (fastest)"""
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF not installed")
        
        text = ""
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.get_text()
                
            doc.close()
            
        except Exception as e:
            self.logger.error(f"Error with PyMuPDF: {e}")
            raise
            
        return text
    
    def extract_text_from_pdf(self, pdf_path: Union[str, Path], method: str = "auto") -> str:
        """
        Extract text from PDF using specified method
        
        Args:
            pdf_path: Path to PDF file
            method: Extraction method ('auto', 'pypdf2', 'pdfplumber', 'pymupdf')
        """
        if not HAS_PDF:
            raise ImportError("No PDF libraries installed. Install with: pip install PyPDF2 pdfplumber PyMuPDF")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"File not found: {pdf_path}")
        
        self.logger.info(f"Extracting text from PDF: {pdf_path}")
        
        if method == "auto":
            # Try methods in order of preference
            if HAS_PYMUPDF:
                method = "pymupdf"
            elif HAS_PDF:
                method = "pdfplumber"
            else:
                method = "pypdf2"
        
        if method == "pypdf2":
            return self.extract_text_from_pdf_pypdf2(pdf_path)
        elif method == "pdfplumber":
            return self.extract_text_from_pdf_pdfplumber(pdf_path)
        elif method == "pymupdf":
            return self.extract_text_from_pdf_pymupdf(pdf_path)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def preprocess_image(self, image_path: Union[str, Path]) -> np.ndarray:
        """Preprocess image for better OCR results"""
        if not HAS_OCR:
            raise ImportError("OpenCV not installed")
        
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply threshold to get better contrast
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def extract_text_from_image(self, image_path: Union[str, Path], 
                              preprocess: bool = True, 
                              lang: str = 'eng',
                              config: str = None) -> str:
        """
        Extract text from image using OCR
        
        Args:
            image_path: Path to image file
            preprocess: Whether to preprocess image for better OCR
            lang: Language for OCR (e.g., 'eng', 'fra', 'deu')
            config: Custom tesseract configuration
        """
        if not HAS_OCR:
            raise ImportError("OCR libraries not installed. Install with: pip install pytesseract pillow opencv-python")
        
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"File not found: {image_path}")
        
        self.logger.info(f"Extracting text from image: {image_path}")
        
        try:
            if preprocess:
                # Use OpenCV for preprocessing
                processed_img = self.preprocess_image(image_path)
                image = Image.fromarray(processed_img)
            else:
                # Use PIL directly
                image = Image.open(image_path)
            
            # Default config for better accuracy
            if config is None:
                config = '--oem 3 --psm 6'
            
            # Extract text
            text = pytesseract.image_to_string(image, lang=lang, config=config)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from image: {e}")
            raise
    
    def extract_text_from_file(self, file_path: Union[str, Path], **kwargs) -> str:
        """
        Extract text from file (auto-detect PDF or image)
        
        Args:
            file_path: Path to file
            **kwargs: Additional arguments for specific extractors
        """
        file_path = Path(file_path)
        
        if self.is_pdf(file_path):
            return self.extract_text_from_pdf(file_path, **kwargs)
        elif self.is_image(file_path):
            return self.extract_text_from_image(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    def extract_text_from_directory(self, directory_path: Union[str, Path], 
                                   output_dir: Optional[Union[str, Path]] = None,
                                   recursive: bool = False) -> dict:
        """
        Extract text from all supported files in directory
        
        Args:
            directory_path: Path to directory
            output_dir: Directory to save extracted text files
            recursive: Whether to process subdirectories
        
        Returns:
            Dictionary mapping file paths to extracted text
        """
        directory_path = Path(directory_path)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # Get all supported files
        pattern = "**/*" if recursive else "*"
        all_files = directory_path.glob(pattern)
        
        for file_path in all_files:
            if file_path.is_file() and (self.is_pdf(file_path) or self.is_image(file_path)):
                try:
                    self.logger.info(f"Processing: {file_path}")
                    text = self.extract_text_from_file(file_path)
                    results[str(file_path)] = text
                    
                    # Save to output directory if specified
                    if output_dir:
                        output_file = output_dir / f"{file_path.stem}_extracted.txt"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(f"Extracted from: {file_path}\n")
                            f.write("=" * 50 + "\n\n")
                            f.write(text)
                        self.logger.info(f"Saved to: {output_file}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path}: {e}")
                    results[str(file_path)] = f"ERROR: {e}"
        
        return results

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description="Extract text from PDF files and images")
    parser.add_argument("input", help="Input file or directory path")
    parser.add_argument("-o", "--output", help="Output file or directory")
    parser.add_argument("-m", "--method", choices=["auto", "pypdf2", "pdfplumber", "pymupdf"], 
                       default="auto", help="PDF extraction method")
    parser.add_argument("-l", "--lang", default="eng", help="OCR language (e.g., eng, fra, deu)")
    parser.add_argument("-p", "--preprocess", action="store_true", 
                       help="Preprocess images for better OCR")
    parser.add_argument("-r", "--recursive", action="store_true", 
                       help="Process directories recursively")
    parser.add_argument("--tesseract-path", help="Path to tesseract executable")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize extractor
    extractor = TextExtractor(tesseract_path=args.tesseract_path)
    
    input_path = Path(args.input)
    
    try:
        if input_path.is_file():
            # Process single file
            if extractor.is_pdf(input_path):
                text = extractor.extract_text_from_pdf(input_path, method=args.method)
            elif extractor.is_image(input_path):
                text = extractor.extract_text_from_image(input_path, 
                                                        preprocess=args.preprocess, 
                                                        lang=args.lang)
            else:
                print(f"Unsupported file type: {input_path.suffix}")
                sys.exit(1)
            
            # Output
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Text saved to: {args.output}")
            else:
                print("Extracted Text:")
                print("=" * 50)
                print(text)
                
        elif input_path.is_dir():
            # Process directory
            results = extractor.extract_text_from_directory(input_path, 
                                                          output_dir=args.output, 
                                                          recursive=args.recursive)
            
            print(f"Processed {len(results)} files")
            for file_path, result in results.items():
                if result.startswith("ERROR:"):
                    print(f"❌ {file_path}: {result}")
                else:
                    print(f"✅ {file_path}: {len(result)} characters extracted")
        
        else:
            print(f"Path not found: {input_path}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Example usage when run as script
    if len(sys.argv) == 1:
        print("Text Extractor - Extract text from PDFs and images")
        print("\nExample usage:")
        print("python text_extractor.py document.pdf")
        print("python text_extractor.py image.png -p")
        print("python text_extractor.py /path/to/files -o /path/to/output -r")
        print("\nFor help: python text_extractor.py -h")
    else:
        main()