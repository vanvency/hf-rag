#!/usr/bin/env python
"""
导入文档脚本：删除数据库数据并重新导入 tests/docs 中的文件
完成解析、目录抽取、切片以及向量化任务
所有文件处理相关任务都有详细日志
"""
import sys
from pathlib import Path
from typing import List

from src.core.config import get_settings
from src.core.logging import configure_logging
from src.retrieval.search import VectorStore
from src.services.processor import DocumentProcessor


def get_doc_files(docs_dir: Path) -> List[Path]:
    """获取所有文档文件"""
    files = []
    for ext in ['.pdf', '.docx', '.doc', '.txt', '.md']:
        files.extend(docs_dir.glob(f'*{ext}'))
    # 过滤掉隐藏文件和临时文件
    files = [f for f in files if not f.name.startswith('.')]
    return sorted(files)


def main():
    """主函数：删除数据库并重新导入文档"""
    # 配置日志
    logger = configure_logging()
    
    logger.info("=" * 80)
    logger.info("开始文档导入流程")
    logger.info("=" * 80)
    
    # 获取配置
    settings = get_settings()
    logger.info(f"[配置] 向量存储路径: {settings.vector_store_path}")
    logger.info(f"[配置] Chunk大小: {settings.chunk_size}, 重叠: {settings.chunk_overlap}")
    logger.info(f"[配置] 嵌入模型: {settings.embedding_model}")
    
    # 初始化向量存储
    logger.info("[初始化] 初始化向量存储...")
    vector_store = VectorStore(settings.vector_store_path)
    
    # 获取当前统计信息
    docs_before, chunks_before = vector_store.stats()
    logger.info(f"[统计] 当前数据库状态 - 文档数: {docs_before}, Chunks数: {chunks_before}")
    
    # 清空数据库
    logger.info("")
    logger.info("-" * 80)
    logger.info("步骤 1: 清空数据库")
    logger.info("-" * 80)
    vector_store.clear()
    docs_after_clear, chunks_after_clear = vector_store.stats()
    logger.info(f"[验证] 清空后数据库状态 - 文档数: {docs_after_clear}, Chunks数: {chunks_after_clear}")
    assert docs_after_clear == 0 and chunks_after_clear == 0, "数据库清空失败"
    logger.info("[完成] 数据库已清空")
    
    # 获取文档目录
    docs_dir = Path("tests/docs")
    if not docs_dir.exists():
        logger.error(f"[错误] 文档目录不存在: {docs_dir}")
        sys.exit(1)
    
    logger.info("")
    logger.info("-" * 80)
    logger.info("步骤 2: 扫描文档文件")
    logger.info("-" * 80)
    doc_files = get_doc_files(docs_dir)
    logger.info(f"[扫描] 在 {docs_dir} 中找到 {len(doc_files)} 个文档文件")
    
    if not doc_files:
        logger.warning("[警告] 未找到任何文档文件，退出")
        sys.exit(0)
    
    # 列出所有文件
    for i, file_path in enumerate(doc_files, 1):
        logger.info(f"  [{i}] {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # 初始化文档处理器
    logger.info("")
    logger.info("-" * 80)
    logger.info("步骤 3: 初始化文档处理器")
    logger.info("-" * 80)
    processor = DocumentProcessor(
        settings=settings,
        vector_store=vector_store,
        logger=logger
    )
    logger.info("[完成] 文档处理器初始化完成")
    
    # 处理每个文档
    logger.info("")
    logger.info("-" * 80)
    logger.info("步骤 4: 处理文档（解析、目录抽取、切片、向量化）")
    logger.info("-" * 80)
    
    success_count = 0
    failed_count = 0
    failed_files = []
    
    for i, file_path in enumerate(doc_files, 1):
        logger.info("")
        logger.info(f"[处理 {i}/{len(doc_files)}] 开始处理: {file_path.name}")
        logger.info(f"  文件路径: {file_path}")
        logger.info(f"  文件大小: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        try:
            # 步骤 4.1: 解析文件
            logger.info(f"  [4.1 解析] 开始解析文件...")
            from src.parsers import get_parser
            parser, content_type = get_parser(file_path)
            logger.info(f"  [4.1 解析] 使用解析器: {parser.__class__.__name__}, 内容类型: {content_type}")
            
            text = parser.parse(file_path)
            if not text.strip():
                logger.warning(f"  [4.1 解析] 警告: 文件解析后内容为空")
                failed_count += 1
                failed_files.append((file_path.name, "解析后内容为空"))
                continue
            
            text_length = len(text)
            text_lines = text.count('\n')
            logger.info(f"  [4.1 解析] 解析完成 - 文本长度: {text_length} 字符, 行数: {text_lines}")
            
            # 步骤 4.2: 目录抽取和切片
            logger.info(f"  [4.2 目录抽取与切片] 开始目录抽取和切片...")
            catalog_items, chunks, chunk_metadata_list = processor.chunker.split(text)
            
            if not chunks:
                logger.warning(f"  [4.2 目录抽取与切片] 警告: 切片后未生成任何chunks")
                failed_count += 1
                failed_files.append((file_path.name, "切片后未生成chunks"))
                continue
            
            catalog_count = len(catalog_items)
            chunks_count = len(chunks)
            logger.info(f"  [4.2 目录抽取与切片] 完成 - 目录项数: {catalog_count}, Chunks数: {chunks_count}")
            
            # 显示目录结构（前10个）
            if catalog_items:
                logger.info(f"  [4.2 目录抽取与切片] 目录结构预览（前10个）:")
                for item in catalog_items[:10]:
                    indent = "  " * (item.level - 1)
                    logger.info(f"    {indent}- {item.title} (级别 {item.level})")
                if len(catalog_items) > 10:
                    logger.info(f"    ... 还有 {len(catalog_items) - 10} 个目录项")
            
            # 步骤 4.3: 向量化
            logger.info(f"  [4.3 向量化] 开始生成向量嵌入...")
            logger.info(f"  [4.3 向量化] 将为 {chunks_count} 个chunks生成向量")
            vectors = processor.embedder.embed(chunks)
            vector_dim = vectors.shape[1] if len(vectors.shape) > 1 else len(vectors[0])
            logger.info(f"  [4.3 向量化] 向量化完成 - 向量维度: {vector_dim}, 向量数量: {len(vectors)}")
            
            # 步骤 4.4: 保存解析后的markdown
            parsed_name = f"{file_path.stem}.md"
            parsed_path = Path("data/parse") / parsed_name
            parsed_path.parent.mkdir(parents=True, exist_ok=True)
            parsed_path.write_text(text, encoding="utf-8")
            logger.info(f"  [4.4 保存] 已保存解析后的markdown: {parsed_path}")
            
            # 步骤 4.5: 存储到数据库
            logger.info(f"  [4.5 入库] 开始将文档存储到数据库...")
            metadata = vector_store.add_document(
                filename=file_path.name,
                source_path=file_path,
                parsed_path=parsed_path,
                chunks=chunks,
                vectors=vectors,
                content_type=content_type,
                catalog_items=catalog_items,
                chunk_metadata_list=chunk_metadata_list,
            )
            logger.info(f"  [4.5 入库] 文档入库完成 - document_id: {metadata.document_id}")
            
            success_count += 1
            logger.info(f"[处理 {i}/{len(doc_files)}] ✓ 成功处理: {file_path.name}")
            
        except Exception as e:
            failed_count += 1
            failed_files.append((file_path.name, str(e)))
            logger.error(f"[处理 {i}/{len(doc_files)}] ✗ 处理失败: {file_path.name}", exc_info=True)
            logger.error(f"  错误信息: {str(e)}")
            continue
    
    # 最终统计
    logger.info("")
    logger.info("=" * 80)
    logger.info("文档导入流程完成")
    logger.info("=" * 80)
    
    final_docs, final_chunks = vector_store.stats()
    logger.info(f"[最终统计] 成功处理: {success_count} 个文件")
    logger.info(f"[最终统计] 处理失败: {failed_count} 个文件")
    logger.info(f"[最终统计] 数据库状态 - 文档数: {final_docs}, Chunks数: {final_chunks}")
    
    if failed_files:
        logger.warning("")
        logger.warning("[失败文件列表]")
        for filename, error in failed_files:
            logger.warning(f"  - {filename}: {error}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("所有任务已完成")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
