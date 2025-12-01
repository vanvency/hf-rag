from typing import List, Tuple

from src.chunking.catalog_extractor import CatalogExtractor, CatalogItem


class CatalogBasedSplitter:
    """Split markdown based on catalog structure"""

    def __init__(self, min_chunk_size: int = 200, max_chunk_size: int = 2000):
        self.extractor = CatalogExtractor()
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def split(self, markdown: str) -> Tuple[List[CatalogItem], List[str], List[dict]]:
        """
        Split markdown into chunks based on catalog.
        Returns: (catalog_items, chunks, chunk_metadata_list)
        """
        catalog_items, processed_markdown = self.extractor.extract(markdown)
        lines = processed_markdown.split('\n')
        chunks: List[str] = []
        chunk_metadata_list: List[dict] = []

        # Group catalog items by their hierarchical sections
        for item in catalog_items:
            if item.end_line is None:
                continue
            
            # Get section content
            section_lines = lines[item.start_line:item.end_line + 1]
            section_content = '\n'.join(section_lines).strip()
            
            if not section_content:
                continue

            # If section is too large, split it further
            if len(section_content) > self.max_chunk_size:
                # Split by paragraphs or sentences within the section
                sub_chunks = self._split_large_section(section_content)
                for idx, sub_chunk in enumerate(sub_chunks):
                    chunks.append(sub_chunk)
                    chunk_metadata_list.append({
                        "catalog_path": item.get_full_path(),
                        "catalog_title": item.title,
                        "catalog_level": item.level,
                        "chunk_index": idx,
                        "is_subchunk": True,
                    })
            else:
                # Use entire section as chunk
                chunks.append(section_content)
                chunk_metadata_list.append({
                    "catalog_path": item.get_full_path(),
                    "catalog_title": item.title,
                    "catalog_level": item.level,
                    "chunk_index": 0,
                    "is_subchunk": False,
                })

        # If no catalog items found, fall back to simple splitting
        if not chunks:
            chunks = self._fallback_split(markdown)
            chunk_metadata_list = [{"catalog_path": "未分类", "catalog_title": "未分类", "catalog_level": 0} 
                                  for _ in chunks]

        return catalog_items, chunks, chunk_metadata_list

    def _split_large_section(self, content: str) -> List[str]:
        """Split a large section into smaller chunks"""
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)
            if current_size + para_size > self.max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for \n\n

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks if chunks else [content]

    def _fallback_split(self, content: str) -> List[str]:
        """Fallback splitting when no catalog is found"""
        # Simple paragraph-based splitting
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)
            if current_size + para_size > self.max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size + 2

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks if chunks else [content]

