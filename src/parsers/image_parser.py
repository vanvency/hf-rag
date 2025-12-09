from pathlib import Path
import os
import tempfile

from .base import BaseParser


class ImageParser(BaseParser):
    content_type = "image/ocr"
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def parse(self, path: Path) -> str:
        """
        Parse image using MinerU OCR.
        """
        try:
            # Try importing from mineru package first
            try:
                from mineru.magic_pdf.data.data_reader_writer import FileBasedDataWriter
                from mineru.magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
                from mineru.magic_pdf.data.read_api import read_local_images
            except ImportError:
                # Fallback to direct magic_pdf imports
                from magic_pdf.data.data_reader_writer import FileBasedDataWriter
                from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
                from magic_pdf.data.read_api import read_local_images
        except ImportError as e:
            raise ImportError(
                "MinerU is not installed. Please install it with: pip install mineru"
            ) from e

        # Create temporary directories for MinerU output
        with tempfile.TemporaryDirectory() as temp_dir:
            local_image_dir = os.path.join(temp_dir, "images")
            local_md_dir = os.path.join(temp_dir, "md")
            os.makedirs(local_image_dir, exist_ok=True)
            os.makedirs(local_md_dir, exist_ok=True)
            
            image_writer = FileBasedDataWriter(local_image_dir)
            md_writer = FileBasedDataWriter(local_md_dir)
            
            # Read the image
            input_file_name = path.stem
            ds = read_local_images(str(path))[0]
            
            # Perform OCR and get markdown output
            ds.apply(doc_analyze, ocr=True).pipe_ocr_mode(image_writer).dump_md(
                md_writer, f"{input_file_name}.md", os.path.basename(local_image_dir)
            )
            
            # Read the generated markdown file
            md_file_path = os.path.join(local_md_dir, f"{input_file_name}.md")
            if os.path.exists(md_file_path):
                with open(md_file_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                return ""

