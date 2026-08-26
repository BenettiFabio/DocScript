from pathlib import Path
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field
import re
from typing import Optional

from src.utils import (
    is_external_link,
    calculate_hash,
    write_json,
)

##########
# CLASSI #
##########


@dataclass
class Link:
    text: str
    target: str
    resolved_path: Optional[str] = None


@dataclass
class Asset:
    type: str
    path: str
    label: Optional[str] = None


@dataclass
class Section:
    level: int
    title: str
    content: str = ""
    children: list["Section"] = field(default_factory=list)


@dataclass
class Document:
    id: str
    name: str
    path: Path
    relative_path: Path
    content: str
    topic_path: list[str]  # Gerarchia derivata dal nome del file e/o path.
    links: list[Link] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    # Sezioni root del documento.
    sections: list[Section] = field(default_factory=list)
    hash: str = ""


@dataclass
class Chunk:
    id: str
    document_id: str
    source_path: str
    content: str
    heading_path: list[str] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    chunk_index: int = 0
    hash: str = ""


##########
# DEFINE #
##########
AI_INDEX_VERSION = 1

MAX_CHUNK_SIZE = 3000
MIN_CHUNK_SIZE = 200
CHUNK_OVERLAP = 200

IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK_PATTERN = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def fill_ai_dir(
    matchingFiles: list[str],
    vaultDirPath: Path,
    configPath: Path,
    documentPath: Path,
    chunkPath: Path,
    manifestPath: Path,
) -> None:

    # Convert all path strings to Path and sort them
    files = sorted(Path(file) for file in matchingFiles)

    # --------------------------------------------------
    # Parse all documents
    # --------------------------------------------------
    print("[AI] Parsing documents...")
    documents = parse_documents(files=files, vault_path=vaultDirPath)

    # --------------------------------------------------
    # Create all chunks
    # --------------------------------------------------
    print("[AI] Creating chunks...")
    chunks = chunk_documents(documents=documents)
    print(f"[AI] Chunk created: {len(chunks)}")

    # --------------------------------------------------
    # Write AI configuration
    # --------------------------------------------------
    print("[AI] Writing: .ai/config.json")
    write_config(dst=configPath)

    # --------------------------------------------------
    # Write document index
    # --------------------------------------------------
    print("[AI] Writing: .ai/documents.json")
    write_documents(documents=documents, dst=documentPath)

    # --------------------------------------------------
    # Write chunks
    # --------------------------------------------------
    print("[AI] Writing: .ai/chunks.jsonl")
    write_chunks(chunks=chunks, dst=chunkPath)

    # --------------------------------------------------
    # Write manifest
    # --------------------------------------------------
    print("[AI] Writing: .ai/manifest.json")
    write_manifest(documents=documents, chunks=chunks, dst=manifestPath)


def write_config(dst: Path) -> None:
    """
    Write the configuration used to generate the AI index.
    This file makes the indexing process reproducible.
    """

    config = {
        "version": 1,
        "chunking": {
            "strategy": "markdown_hierarchical",
            "unit": "characters",
            "max_chunk_size": MAX_CHUNK_SIZE,
            "min_chunk_size": MIN_CHUNK_SIZE,
            "overlap": CHUNK_OVERLAP,
        },
        "parsing": {
            "markdown_headings": True,
            "markdown_links": True,
            "assets": True,
            "ocr": False,
            "pdf_content_extraction": False,
        },
        "embedding": {
            "provider": None,
            "model": None,
        },
    }

    write_json(data=config, dst=dst)


def write_documents(documents: list[Document], dst: Path) -> None:
    """
    Write the parsed document catalog.
    The original Markdown content is not duplicated here.
    """

    serialized_documents = []
    for document in documents:
        document_data = {
            "id": document.id,
            "name": document.name,
            "path": str(document.relative_path),
            "topic_path": document.topic_path,
            "hash": document.hash,
            "links": [
                {
                    "text": link.text,
                    "target": link.target,
                    "resolved_path": link.resolved_path,
                }
                for link in document.links
            ],
            "assets": [
                {
                    "type": asset.type,
                    "path": asset.path,
                    "label": asset.label,
                }
                for asset in document.assets
            ],
            "sections": [serialize_section(section) for section in document.sections],
        }

        serialized_documents.append(document_data)

    output = {
        "version": 1,
        "documents": serialized_documents,
    }

    write_json(data=output, dst=dst)


def write_chunks(chunks: list[Chunk], dst: Path) -> None:
    """
    Write all chunks using JSON Lines format.
    Each line is a complete JSON object representing one chunk.
    """

    dst.parent.mkdir(parents=True, exist_ok=True)

    with dst.open(
        "w",
        encoding="utf-8",
    ) as file:
        for chunk in chunks:
            chunk_data = {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "source_path": chunk.source_path,
                "content": chunk.content,
                "heading_path": chunk.heading_path,
                "links": [
                    {
                        "text": link.text,
                        "target": link.target,
                        "resolved_path": link.resolved_path,
                    }
                    for link in chunk.links
                ],
                "assets": [
                    {
                        "type": asset.type,
                        "path": asset.path,
                        "label": asset.label,
                    }
                    for asset in chunk.assets
                ],
                "chunk_index": chunk.chunk_index,
                "hash": chunk.hash,
            }

            json.dump(
                chunk_data,
                file,
                ensure_ascii=False,
            )

            file.write("\n")


def write_manifest(documents: list[Document], chunks: list[Chunk], dst: Path) -> None:
    """
    Write general information about the current AI index.
    """

    total_characters = sum(len(chunk.content) for chunk in chunks)

    manifest = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "prepared",
        "statistics": {
            "documents": len(documents),
            "chunks": len(chunks),
            "characters": total_characters,
        },
        "embedding": {
            "status": "not_generated",
            "provider": None,
            "model": None,
        },
    }

    write_json(data=manifest, dst=dst)


def serialize_section(section: Section) -> dict:
    """
    Convert a Section tree into a JSON-serializable dictionary.
    """

    return {
        "level": section.level,
        "title": section.title,
        "content": section.content,
        "children": [serialize_section(child) for child in section.children],
    }


# ==========================================================
# PARSING DOCUMENTS
# ==========================================================
def parse_documents(
    files: list[Path],
    vault_path: Path,
) -> list[Document]:
    """
    Parse all valid Markdown files.
    Each file is read exactly once and converted into a Document object.
    """

    documents: list[Document] = []
    vault_path = vault_path.resolve()

    for file_path in files:
        document = parse_document(file_path=file_path, vault_path=vault_path)
        documents.append(document)

    return documents


def parse_document(
    file_path: Path,
    vault_path: Path,
) -> Document:
    """
    Parse one Markdown document.
    """

    file_path = file_path.resolve()
    try:
        content = file_path.read_text(encoding="utf-8")

    except UnicodeDecodeError:
        # Fallback utile per file Markdown non UTF-8.
        content = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    relative_path = file_path.relative_to(vault_path)

    document_id = create_document_id(relative_path)

    topic_path = extract_topic_path(relative_path)

    links, assets = parse_links_and_assets(
        content=content,
        source_file=file_path,
        vault_path=vault_path,
    )

    sections = parse_markdown_sections(content)

    document_hash = calculate_hash(content)

    return Document(
        id=document_id,
        name=file_path.name,
        path=file_path,
        relative_path=relative_path,
        content=content,
        topic_path=topic_path,
        links=links,
        assets=assets,
        sections=sections,
        hash=document_hash,
    )


def create_document_id(
    relative_path: Path,
) -> str:
    """
    Create a stable ID from the relative path.
    Example:
        arg/main.arg.sub.md
    becomes:
        arg.arg.sub
    The 'main.' prefix is removed.
    """

    path_without_suffix = relative_path.with_suffix("")

    # todo : fai in modo che tolga "main." in modo dinamico
    parts = list(path_without_suffix.parts)
    filename = parts[-1]
    if filename.startswith("main."):
        filename = filename[5:]

    filename_parts = [part for part in filename.split(".") if part]

    id_parts = [*parts[:-1], *filename_parts]

    return ".".join(id_parts)


def extract_topic_path(
    relative_path: Path,
) -> list[str]:
    """
    Extract a generic hierarchy from folders + filename.
    Example:
        vault/
            develop/
                cpp/
                    main.develop.cpp.class.md
    becomes:
        [
            "develop",
            "cpp",
            "class"
        ]
    """

    # parts = list(relative_path.parts)
    folders = list(relative_path.parent.parts)
    filename = relative_path.stem

    # todo : fai in modo che tolga "main." in modo dinamico
    if filename.startswith("main."):
        filename = filename[5:]

    filename_parts = [part for part in filename.split(".") if part]

    # Evita duplicati consecutivi.
    result: list[str] = []

    for part in [*folders, *filename_parts]:
        if not result or result[-1] != part:
            result.append(part)

    return result


def parse_links_and_assets(
    content: str,
    source_file: Path,
    vault_path: Path,
) -> tuple[list[Link], list[Asset]]:
    """
    Extract:
    - Markdown links to other .md files
    - Images
    - PDFs
    - Other linked assets
    No OCR or binary parsing is performed.
    """

    links: list[Link] = []
    assets: list[Asset] = []

    # ------------------------------------------------------
    # IMAGES
    # ------------------------------------------------------

    for match in IMAGE_PATTERN.finditer(content):

        alt = match.group(1).strip()
        target = clean_markdown_target(match.group(2))

        assets.append(
            Asset(
                type="image",
                path=target,
                label=alt or None,
            )
        )

    # ------------------------------------------------------
    # NORMAL LINKS
    # ------------------------------------------------------

    for match in LINK_PATTERN.finditer(content):
        label = match.group(1).strip()
        raw_target = match.group(2).strip()
        target = clean_markdown_target(raw_target)

        # Separa eventuale anchor.
        target_without_anchor = target.split("#", 1)[0]

        # --------------------------------------------------
        # MARKDOWN DOCUMENT
        # --------------------------------------------------

        if target_without_anchor.lower().endswith(".md"):
            resolved_path = resolve_link_path(
                target_without_anchor,
                source_file,
                vault_path,
            )

            links.append(Link(text=label, target=target, resolved_path=resolved_path))

            continue

        # --------------------------------------------------
        # PDF
        # --------------------------------------------------

        if target_without_anchor.lower().endswith(".pdf"):
            assets.append(Asset(type="pdf", path=target, label=label or None))

            continue

        # --------------------------------------------------
        # EXTERNAL / OTHER FILE
        # --------------------------------------------------

        if is_external_link(target):
            assets.append(
                Asset(
                    type="external",
                    path=target,
                    label=label or None,
                )
            )

        else:
            suffix = Path(target_without_anchor).suffix.lower()

            asset_type = suffix[1:] if suffix else "file"

            assets.append(
                Asset(
                    type=asset_type,
                    path=target,
                    label=label or None,
                )
            )

    return links, assets


def clean_markdown_target(
    target: str,
) -> str:
    """
    Remove optional Markdown title:
        file.md "Title"
    This implementation intentionally keeps the first token.
    """

    target = target.strip()

    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()

    # Gestione semplice del titolo Markdown opzionale.
    if " " in target:
        first_part = target.split(" ", 1)[0]
        return first_part.strip()

    return target


def resolve_link_path(
    target: str,
    source_file: Path,
    vault_path: Path,
) -> Optional[str]:
    """
    Resolve a Markdown link if it points to a local file.

    The function only stores the resolved path when it exists
    inside the vault.
    """

    if is_external_link(target):
        return None

    try:

        if target.startswith("/"):

            candidate = vault_path / target.lstrip("/")

        else:

            candidate = source_file.parent / target

        candidate = candidate.resolve()

        # Security / consistency check:
        # only accept files inside the vault.
        candidate.relative_to(vault_path)

        if candidate.exists():

            return str(candidate)

    except (
        ValueError,
        OSError,
    ):
        return None

    return None


def parse_markdown_sections(
    content: str,
) -> list[Section]:
    """
    Parse Markdown headings into a tree.
    Important:
    The content of each Section contains only its direct text.
    Subsections are stored in children.
    """

    matches = list(HEADING_PATTERN.finditer(content))

    # Documento senza heading.
    if not matches:
        stripped = content.strip()

        if not stripped:
            return []

        return [
            Section(
                level=0,
                title="",
                content=stripped,
            )
        ]

    root_sections: list[Section] = []

    # Stack:
    #
    # [
    #   Section(H1),
    #   Section(H2),
    #   Section(H3),
    # ]
    #
    stack: list[Section] = []

    # ------------------------------------------------------
    # TEXT BEFORE FIRST HEADING
    # ------------------------------------------------------

    prefix = content[0 : matches[0].start()].strip()

    if prefix:
        root_sections.append(
            Section(
                level=0,
                title="",
                content=prefix,
            )
        )

    # ------------------------------------------------------
    # HEADINGS
    # ------------------------------------------------------

    for index, match in enumerate(matches):
        level = len(match.group(1))

        title = match.group(2).strip().rstrip("#").strip()

        content_start = match.end()

        if index + 1 < len(matches):
            next_heading = matches[index + 1]

            content_end = next_heading.start()

        else:
            content_end = len(content)

        direct_content = content[content_start:content_end].strip()

        section = Section(
            level=level,
            title=title,
            content=direct_content,
        )

        # Remove sections at the same or deeper level.
        while stack and stack[-1].level >= level:
            stack.pop()

        # Add as child or root.
        if stack:
            stack[-1].children.append(section)

        else:
            root_sections.append(section)

        stack.append(section)

    return root_sections


# ==========================================================
# CHUNKING
# ==========================================================


def chunk_documents(documents: list[Document]) -> list[Chunk]:
    """
    Chunk all parsed documents.
    Strategy:
    1. Small document -> one chunk
    2. Large document -> hierarchical Markdown sections
    3. Large section -> child sections
    4. Still too large -> paragraphs
    5. Huge paragraph -> hard text split
    """

    all_chunks: list[Chunk] = []

    for document in documents:

        document_chunks = chunk_document(document)

        all_chunks.extend(document_chunks)

    return all_chunks


def chunk_document(document: Document) -> list[Chunk]:
    """
    Create chunks for a single document.
    """

    # ------------------------------------------------------
    # SMALL DOCUMENT
    # ------------------------------------------------------

    if len(document.content) <= MAX_CHUNK_SIZE:

        chunk = Chunk(
            id=f"{document.id}:0001",
            document_id=document.id,
            source_path=str(document.relative_path),
            content=document.content.strip(),
            heading_path=[],
            links=document.links,
            assets=document.assets,
            chunk_index=1,
        )

        chunk.hash = calculate_hash(chunk.content)

        return [chunk]

    # ------------------------------------------------------
    # LARGE DOCUMENT
    # ------------------------------------------------------
    raw_chunks: list[tuple[str, list[str]]] = []

    # Documento senza sezioni utilizzabili.
    if not document.sections:
        raw_chunks = split_text_by_paragraphs(text=document.content)

    else:
        for section in document.sections:
            raw_chunks.extend(
                chunk_section(
                    section=section,
                    heading_path=[],
                )
            )

    # ------------------------------------------------------
    # CREATE FINAL CHUNK OBJECTS
    # ------------------------------------------------------
    chunks: list[Chunk] = []

    for index, (content, heading_path) in enumerate(raw_chunks, start=1):
        content = content.strip()

        if not content:
            continue

        chunk = Chunk(
            id=f"{document.id}:{index:04d}",
            document_id=document.id,
            source_path=str(document.relative_path),
            content=content,
            heading_path=heading_path,
            links=find_relevant_links(content, document.links),
            assets=find_relevant_assets(content, document.assets),
            chunk_index=index,
        )

        chunk.hash = calculate_hash(chunk.content)
        chunks.append(chunk)

    # ------------------------------------------------------
    # FALLBACK
    # ------------------------------------------------------
    if not chunks:
        fallback = Chunk(
            id=f"{document.id}:0001",
            document_id=document.id,
            source_path=str(document.relative_path),
            content=document.content.strip(),
            heading_path=[],
            links=document.links,
            assets=document.assets,
            chunk_index=1,
        )

        fallback.hash = calculate_hash(fallback.content)
        chunks.append(fallback)

    return chunks


def chunk_section(
    section: Section, heading_path: list[str]
) -> list[tuple[str, list[str]]]:
    """
    Recursively chunk a Markdown section.
    """

    current_heading_path = list(heading_path)

    if section.title:
        current_heading_path.append(section.title)

    # ------------------------------------------------------
    # Build the complete section representation.
    #
    # This is used only to determine whether the whole
    # semantic section fits into a single chunk.
    # ------------------------------------------------------

    full_content = collect_section_content(section)

    # ------------------------------------------------------
    # SECTION FITS
    # ------------------------------------------------------
    if len(full_content) <= MAX_CHUNK_SIZE:
        return [
            (
                full_content,
                current_heading_path,
            )
        ]

    # ------------------------------------------------------
    # SECTION TOO LARGE BUT HAS CHILDREN
    # ------------------------------------------------------
    if section.children:
        result: list[tuple[str, list[str]]] = []

        # Direct content before children.
        if section.content.strip():
            direct_chunks = split_text_by_paragraphs(section.content)

            for content, _ in direct_chunks:
                result.append(
                    (
                        content,
                        current_heading_path,
                    )
                )

        # Recursively process children.
        for child in section.children:
            result.extend(
                chunk_section(section=child, heading_path=current_heading_path)
            )

        return merge_small_chunks(result)

    # ------------------------------------------------------
    # NO CHILDREN: SPLIT BY PARAGRAPHS
    # ------------------------------------------------------
    paragraph_chunks = split_text_by_paragraphs(full_content)

    return [(content, current_heading_path) for content, _ in paragraph_chunks]


def collect_section_content(section: Section) -> str:
    """
    Collect a section and all descendants as one text block.
    Used only to test whether the complete semantic section
    fits inside one chunk.
    """

    parts: list[str] = []
    if section.title:
        parts.append(section.title)

    if section.content.strip():
        parts.append(section.content.strip())

    for child in section.children:
        child_content = collect_section_content(child)

        if child_content:
            parts.append(child_content)

    return "\n\n".join(parts)


# ==========================================================
# PARAGRAPH SPLITTING
# ==========================================================


def split_text_by_paragraphs(text: str) -> list[tuple[str, list[str]]]:
    """
    Split text by paragraphs.
    Paragraphs are separated by one or more empty lines.
    """

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    if not paragraphs:
        return []

    chunks: list[tuple[str, list[str]]] = []

    current_parts: list[str] = []
    current_size = 0

    for paragraph in paragraphs:
        paragraph_size = len(paragraph)

        # Paragraph itself is larger than max size.
        if paragraph_size > MAX_CHUNK_SIZE:
            # Flush current chunk.
            if current_parts:
                chunks.append(("\n\n".join(current_parts), []))

                current_parts = []
                current_size = 0

            huge_parts = split_large_text(paragraph)

            for part in huge_parts:
                chunks.append((part, []))

            continue

        separator_size = 2 if current_parts else 0

        # Fits in current chunk.
        if current_size + separator_size + paragraph_size <= MAX_CHUNK_SIZE:
            current_parts.append(paragraph)

            current_size += separator_size + paragraph_size

        else:
            # Flush current chunk.
            if current_parts:
                chunks.append(("\n\n".join(current_parts), []))

            current_parts = [paragraph]
            current_size = paragraph_size

    # Flush remaining content.
    if current_parts:
        chunks.append(("\n\n".join(current_parts), []))

    return chunks


def split_large_text(
    text: str,
) -> list[str]:
    """
    Last-resort splitter.
    First tries sentence boundaries, then hard character limits.
    """

    # Basic sentence split.
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        if len(current) + len(sentence) + 1 <= MAX_CHUNK_SIZE:

            if current:
                current += " "

            current += sentence

        else:
            if current:
                chunks.append(current)

            # Sentence larger than max.
            if len(sentence) > MAX_CHUNK_SIZE:
                chunks.extend(hard_split_text(sentence))
                current = ""

            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def hard_split_text(text: str) -> list[str]:
    """
    Absolute fallback.
    Splits by MAX_CHUNK_SIZE characters with overlap.
    """

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_SIZE, len(text))

        chunks.append(text[start:end].strip())

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


# ==========================================================
# SMALL CHUNK MERGING
# ==========================================================


def merge_small_chunks(
    chunks: list[tuple[str, list[str]]],
) -> list[tuple[str, list[str]]]:
    """
    Merge consecutive small chunks only when they belong
    to the same heading path.

    This avoids producing many tiny chunks.
    """

    if not chunks:
        return []

    merged: list[tuple[str, list[str]]] = []

    current_content = chunks[0][0]
    current_path = chunks[0][1]

    for content, path in chunks[1:]:
        can_merge = (
            path == current_path
            and len(current_content) < MIN_CHUNK_SIZE
            and (len(current_content) + len(content) + 2 <= MAX_CHUNK_SIZE)
        )

        if can_merge:
            current_content = current_content + "\n\n" + content

        else:
            merged.append((current_content, current_path))

            current_content = content
            current_path = path

    merged.append((current_content, current_path))

    return merged


# ==========================================================
# CHUNK METADATA FILTERING
# ==========================================================
def find_relevant_links(content: str, links: list[Link]) -> list[Link]:
    """
    Return only links whose Markdown representation appears
    in the chunk content.
    Important:
    this is intentionally conservative.
    """

    relevant: list[Link] = []
    for link in links:
        markdown_link = f"[{link.text}]({link.target})"

        if markdown_link in content:
            relevant.append(link)

    return relevant


def find_relevant_assets(content: str, assets: list[Asset]) -> list[Asset]:
    """
    Return assets whose path appears inside the chunk.
    """

    relevant: list[Asset] = []
    for asset in assets:
        if asset.path in content:
            relevant.append(asset)

    return relevant
