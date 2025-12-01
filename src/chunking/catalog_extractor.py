import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class CatalogItem:
    """Represents a catalog entry with hierarchy"""
    level: int  # Header level (1-6)
    title: str
    start_line: int
    end_line: Optional[int] = None
    parent: Optional['CatalogItem'] = None
    children: List['CatalogItem'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

    def get_full_path(self) -> str:
        """Get full hierarchical path"""
        path = [self.title]
        parent = self.parent
        while parent:
            path.insert(0, parent.title)
            parent = parent.parent
        return " > ".join(path)


class CatalogExtractor:
    """Extract catalog structure from markdown text"""

    def __init__(self):
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def extract(self, markdown: str) -> Tuple[List[CatalogItem], str]:
        """
        Extract catalog from markdown and return catalog items and cleaned markdown.
        Returns: (catalog_items, markdown_with_anchors)
        """
        lines = markdown.split('\n')
        catalog_items: List[CatalogItem] = []
        stack: List[CatalogItem] = []  # Stack to track parent hierarchy
        markdown_with_anchors = []
        current_line = 0

        for i, line in enumerate(lines):
            match = self.header_pattern.match(line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                
                # Pop stack until we find the appropriate parent
                while stack and stack[-1].level >= level:
                    stack.pop()
                
                # Create catalog item
                parent = stack[-1] if stack else None
                catalog_item = CatalogItem(
                    level=level,
                    title=title,
                    start_line=current_line,
                    parent=parent
                )
                
                # Close previous item at same or higher level
                if stack:
                    for item in reversed(stack):
                        if item.level < level:
                            if item.end_line is None:
                                item.end_line = current_line - 1
                            break
                
                catalog_items.append(catalog_item)
                if parent:
                    parent.children.append(catalog_item)
                stack.append(catalog_item)
                
                # Add anchor to markdown
                anchor = self._create_anchor(title, level)
                markdown_with_anchors.append(f"{line}\n<!-- catalog:{catalog_item.get_full_path()} -->")
            else:
                markdown_with_anchors.append(line)
            
            current_line += 1

        # Close remaining items
        for item in stack:
            if item.end_line is None:
                item.end_line = current_line - 1

        return catalog_items, '\n'.join(markdown_with_anchors)

    def _create_anchor(self, title: str, level: int) -> str:
        """Create an anchor ID from title"""
        anchor = re.sub(r'[^\w\s-]', '', title.lower())
        anchor = re.sub(r'[-\s]+', '-', anchor)
        return f"h{level}-{anchor}"

    def get_sections_by_catalog(self, markdown: str, catalog_items: List[CatalogItem]) -> List[Tuple[CatalogItem, str]]:
        """Get content sections for each catalog item"""
        lines = markdown.split('\n')
        sections = []
        
        for item in catalog_items:
            if item.end_line is not None:
                section_lines = lines[item.start_line:item.end_line + 1]
                section_content = '\n'.join(section_lines)
                sections.append((item, section_content))
        
        return sections

