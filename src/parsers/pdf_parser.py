from pathlib import Path
import os
import tempfile

from .base import BaseParser


class PDFParser(BaseParser):
    content_type = "application/pdf"

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def parse(self, path: Path) -> str:
        """
        Parse PDF using MinerU and convert to markdown.
        MinerU automatically handles OCR, table recognition, and formula extraction.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Try to import MinerU modules with better error handling
        try:
            from mineru.cli.common import do_parse
            from mineru.utils.enum_class import MakeMode
        except ImportError as e:
            error_msg = str(e)
            if "doclayout_yolo" in error_msg or "No module named 'doclayout_yolo'" in error_msg:
                raise ImportError(
                    "MinerU pipeline dependencies are missing. Please install with:\n"
                    "  pip install 'mineru[pipeline]'\n"
                    "Or install the missing dependency:\n"
                    "  pip install doclayout-yolo\n"
                    f"Original error: {error_msg}"
                ) from e
            else:
                raise ImportError(
                    f"MinerU is not installed or has missing dependencies. "
                    f"Please install it with: pip install 'mineru[pipeline]'\n"
                    f"Original error: {error_msg}"
                ) from e

        # Read the PDF file as bytes
        logger.info(f"[PDF解析] 开始读取PDF文件: {path.name}")
        try:
            with open(path, "rb") as f:
                pdf_bytes = f.read()
            logger.info(f"[PDF解析] PDF文件读取完成，大小: {len(pdf_bytes) / 1024 / 1024:.2f} MB")
        except Exception as e:
            logger.error(f"[PDF解析] 读取PDF文件失败: {str(e)}")
            raise

        # Create temporary directory for MinerU output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)

            # Get the PDF file name without extension
            pdf_file_name = path.stem

            # Parse PDF using MinerU
            logger.info(f"[PDF解析] 开始使用MinerU解析PDF...")
            try:
                do_parse(
                    output_dir=output_dir,
                    pdf_file_names=[pdf_file_name],
                    pdf_bytes_list=[pdf_bytes],
                    p_lang_list=["en"],  # Language for OCR (can be extended to support multiple languages)
                    backend="pipeline",
                    parse_method="auto",  # Auto-detect whether to use OCR or text extraction
                    formula_enable=True,  # Enable formula recognition
                    table_enable=True,  # Enable table recognition
                    f_draw_layout_bbox=False,  # Disable visualization generation for faster processing
                    f_draw_span_bbox=False,
                    f_dump_md=True,  # Output Markdown
                    f_dump_middle_json=False,  # Don't need intermediate JSON
                    f_dump_model_output=False,  # Don't need model output
                    f_make_md_mode=MakeMode.MM_MD  # Markdown generation mode
                )
                logger.info(f"[PDF解析] MinerU解析完成")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[PDF解析] MinerU解析失败: {error_msg}")
                if "doclayout_yolo" in error_msg or "No module named 'doclayout_yolo'" in error_msg:
                    raise ImportError(
                        "MinerU pipeline dependencies are missing. Please install with:\n"
                        "  pip install 'mineru[pipeline]'\n"
                        "Or install the missing dependency:\n"
                        "  pip install doclayout-yolo\n"
                        f"Original error: {error_msg}"
                    ) from e
                raise

            # Read the generated markdown file
            md_file_path = os.path.join(output_dir, f"{pdf_file_name}.md")
            if os.path.exists(md_file_path):
                logger.info(f"[PDF解析] 找到生成的Markdown文件: {md_file_path}")
                with open(md_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                logger.info(f"[PDF解析] Markdown内容读取完成，长度: {len(content)} 字符")
                return content
            else:
                # If markdown file doesn't exist, try to find it with different naming
                # MinerU might use different naming conventions
                logger.warning(f"[PDF解析] 未找到预期的Markdown文件，尝试查找其他.md文件...")
                for file in os.listdir(output_dir):
                    if file.endswith(".md"):
                        md_file_path = os.path.join(output_dir, file)
                        logger.info(f"[PDF解析] 找到Markdown文件: {file}")
                        with open(md_file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        logger.info(f"[PDF解析] Markdown内容读取完成，长度: {len(content)} 字符")
                        return content
                logger.warning(f"[PDF解析] 未找到任何Markdown文件，返回空内容")
                return ""

