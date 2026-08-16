#!/usr/bin/env python3
"""
lint_wiki.py — LLM-Wiki 健康度檢查

Usage:
  python3 lint_wiki.py

Output: JSON health report for Claude to display as a dashboard.

Checks:
  1. Missing source metadata  → hallucination risk
  2. High inbound-link pages  → priority spot-check candidates
  3. Stale pages              → updated > 90 days
  4. Orphan pages             → no inbound links from within wiki
  5. Broken wikilinks         → links pointing to non-existent pages
  6. Index consistency        → files vs ChromaDB/sync_state.json drift
     (missing_from_index: real file never indexed; ghost_in_index: index
     entry whose file no longer exists — see sync_wiki_index.py to fix)
"""

import re
import json
import datetime
import subprocess
from pathlib import Path

VAULT_ROOT  = Path("/Users/jeffliu/Documents/A05_Obsidian Vault")
WIKI_DIR    = VAULT_ROOT / "300 LLM-Wiki"
LOG_FILE    = WIKI_DIR / "001_log.md"
INDEX_FILE  = WIKI_DIR / "000_index.md"

# Files excluded from problem checks (not counted as "pages to audit")
SKIP_FILES  = {"000_index.md", "001_log.md", "002_system_instruction.md", "003_Dashboard.md", "004_Synthesis_Map.md"}
# Files that ARE scanned as link sources when building inbound counts
# (000_index.md is the MoC — its links must count, or all MoC-only pages look like orphans)
LINK_SOURCE_EXTRAS = {"000_index.md"}
STALE_DAYS  = 90
HIGH_LINK_THRESHOLD = 5


def get_wiki_pages() -> list:
    return [
        f for f in WIKI_DIR.glob("*.md")
        if f.name not in SKIP_FILES
    ]


def parse_yaml_frontmatter(content: str) -> dict:
    """Extract key-value pairs from YAML frontmatter (simple regex, no deps)."""
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    yaml_block = m.group(1)
    result = {}
    for line in yaml_block.splitlines():
        kv = re.match(r'^(\w[\w_]*):\s*(.+)', line)
        if kv:
            result[kv.group(1).strip()] = kv.group(2).strip().strip('"\'')
    return result


def strip_code_spans(content: str) -> str:
    """Remove fenced (```...```) and inline (`...`) code spans.

    [[wikilink]] syntax written inside backticks is a syntax example, not a
    real link (Obsidian doesn't render it as one either), so it must not be
    scanned for wikilinks.
    """
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    content = re.sub(r'`[^`\n]*`', '', content)
    return content


def extract_wikilinks(content: str) -> list:
    """Extract [[wikilink]] targets, ignoring anchors and aliases.

    Handles Markdown table escape: [[Page Title\\|Alias]] -> 'Page Title'
    (the backslash before | is a table cell escape, not part of the link target)
    """
    content = strip_code_spans(content)
    raw = re.findall(r'\[\[([^\]|#\n]+?)(?:[|#][^\]]*)?\]\]', content)
    return [link.strip().rstrip('\\') for link in raw if link.strip()]


def build_link_maps(pages: list) -> tuple:
    """
    Returns:
      outbound: {filename: [link_name, ...]}
      inbound:  {filename: count_of_pages_linking_to_it}

    Note: LINK_SOURCE_EXTRAS (e.g. 000_index.md) are scanned for outbound links
    so that MoC-linked pages are not incorrectly flagged as orphans.
    """
    name_to_file = {f.stem: f for f in pages}
    outbound = {}
    inbound  = {f.name: 0 for f in pages}

    # Scan normal pages
    scan_targets = list(pages)
    # Also scan extra link sources (000_index.md etc.) for inbound counting only
    for extra_name in LINK_SOURCE_EXTRAS:
        extra_path = WIKI_DIR / extra_name
        if extra_path.exists():
            scan_targets.append(extra_path)

    for page in scan_targets:
        content = page.read_text(encoding="utf-8")
        links   = extract_wikilinks(content)
        if page.name not in SKIP_FILES:
            outbound[page.name] = links
        for link in links:
            target = name_to_file.get(link)
            if target:
                inbound[target.name] = inbound.get(target.name, 0) + 1

    return outbound, inbound


def check_missing_source(pages: list) -> list:
    """Pages with no source_url, source_ref, source_raw_path, or source_type.

    MOC (Map of Content) pages are exempt: they are navigation/aggregation
    pages over already-sourced pages, not content with a single external
    source of their own.
    """
    missing = []
    for page in pages:
        content = page.read_text(encoding="utf-8")
        meta = parse_yaml_frontmatter(content)
        if meta.get("type") == "moc":
            continue
        has_source = any(
            k in meta for k in ("source_url", "source_ref", "source_raw_path", "source_type")
        )
        if not has_source:
            missing.append(page.name)
    return missing


def check_stale(pages: list) -> list:
    """Pages where updated > STALE_DAYS days ago."""
    today  = datetime.date.today()
    stale  = []
    for page in pages:
        content = page.read_text(encoding="utf-8")
        meta    = parse_yaml_frontmatter(content)
        updated_str = meta.get("updated", "")
        if not updated_str:
            continue
        try:
            updated_date = datetime.date.fromisoformat(updated_str[:10])
            days_old = (today - updated_date).days
            if days_old > STALE_DAYS:
                stale.append({"file": page.name, "updated": updated_str[:10], "days_old": days_old})
        except ValueError:
            pass
    return stale


def check_orphans(pages: list, inbound: dict) -> list:
    """Pages with zero inbound links from within the wiki."""
    return [p.name for p in pages if inbound.get(p.name, 0) == 0]


def get_vault_stems() -> set:
    """All .md file stems in the vault (via fast find) + YAML aliases from wiki pages only.

    Strategy:
    - Stems: use subprocess find on full vault (fast, no file reading, avoids APFS rglob hang)
    - Aliases: only read wiki pages (182 files, already loaded) — not all 2000+ vault files
    """
    EXCLUDE = [
        "*/node_modules/*", "*/.git/*", "*/.obsidian/plugins/*",
        "*/.ai_index/*", "*/raw/*", "*/.agent-config/*",
        "*/.playwright-mcp/*", "*/.smart-env/*", "*/.trash/*", "*/downloads/*",
    ]
    cmd = ["find", str(VAULT_ROOT), "-name", "*.md"]
    for pat in EXCLUDE:
        cmd += ["-not", "-path", pat]

    stems: set = set()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        for line in result.stdout.splitlines():
            line = line.strip()
            if line:
                stems.add(Path(line).stem)
    except Exception:
        # Fallback: at least cover the wiki dir
        for f in WIKI_DIR.glob("*.md"):
            stems.add(f.stem)

    # Aliases: only scan wiki dir (small, already read for other checks)
    for f in WIKI_DIR.glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            meta = parse_yaml_frontmatter(content)
            for key in ("aliases", "Aliases"):
                val = meta.get(key, "")
                if not val:
                    continue
                val = val.strip("[]")
                for alias in val.split(","):
                    a = alias.strip().strip('"\'')
                    if a:
                        stems.add(a)
        except Exception:
            pass

    return stems


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf", ".mp4", ".mov"}

def check_broken_links(pages: list, outbound: dict, vault_stems: set) -> list:
    """Wikilinks pointing to pages that don't exist anywhere in the vault.

    Skips:
    - Cross-vault links (containing '/') — Obsidian resolves by path
    - Image/media embeds — not .md pages, always exist as files
    """
    broken = []
    for page in pages:
        for link in outbound.get(page.name, []):
            if '/' in link:
                continue
            if Path(link).suffix.lower() in IMAGE_EXTS:
                continue
            if link not in vault_stems:
                broken.append({"from": page.name, "link": link})
    return broken


def check_tier_distribution(pages: list) -> dict:
    """source_tier 分布（Mode A 適用；personal-reflection 跳過）。"""
    tiers = {"primary": [], "secondary": [], "tertiary": [], "unset": []}
    for page in pages:
        content = page.read_text(encoding="utf-8")
        meta = parse_yaml_frontmatter(content)
        if meta.get("source_type") == "personal-reflection":
            continue
        tier = meta.get("source_tier", "").strip()
        if tier in ("primary", "secondary", "tertiary"):
            tiers[tier].append(page.name)
        else:
            tiers["unset"].append(page.name)
    return tiers


def check_high_inbound(inbound: dict) -> list:
    """Pages with HIGH_LINK_THRESHOLD+ inbound links — priority spot-check."""
    return [
        {"file": fname, "inbound_count": count}
        for fname, count in sorted(inbound.items(), key=lambda x: -x[1])
        if count >= HIGH_LINK_THRESHOLD
    ]


def check_index_consistency(pages: list) -> dict:
    """Compare real files in 300 LLM-Wiki/ against sync_state.json.

    sync_state.json is written by ingest_unified.py's index_file() on every
    successful index call (ChromaDB write is best-effort, but sync_state is
    unconditional), so it's a dependency-free proxy for "has this file ever
    been indexed" — no chromadb import needed here.

    Two drift modes:
    - missing_from_index: real file on disk, never indexed (e.g. written via
      a skill/flow that doesn't call ingest_unified.py's indexing step)
    - ghost_in_index: index entry with no matching file (e.g. file renamed,
      merged into another card, or deleted without cleaning up the index)
    """
    state_file = WIKI_DIR / ".ai_index" / "sync_state.json"

    # Use all .md files in WIKI_DIR, not just `pages` (which excludes
    # SKIP_FILES like 002_system_instruction.md / 003_Dashboard.md — those
    # are still real files that can legitimately appear in sync_state.json).
    real_files = {f.name for f in WIKI_DIR.glob("*.md")}

    if not state_file.exists():
        return {"available": False, "reason": "sync_state.json not found",
                "missing_from_index": [], "ghost_in_index": []}

    try:
        sync_state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as e:
        return {"available": False, "reason": f"sync_state.json unreadable: {e}",
                "missing_from_index": [], "ghost_in_index": []}

    indexed_files = set(sync_state.keys())

    return {
        "available": True,
        "missing_from_index": sorted(real_files - indexed_files),
        "ghost_in_index": sorted(indexed_files - real_files),
    }


def main():
    pages = get_wiki_pages()
    if not pages:
        print(json.dumps({"error": "No wiki pages found in 300 LLM-Wiki/"}, ensure_ascii=False))
        return

    outbound, inbound = build_link_maps(pages)
    vault_stems = get_vault_stems()

    report = {
        "generated": datetime.date.today().isoformat(),
        "total_pages": len(pages),
        "missing_source": check_missing_source(pages),
        "high_inbound": check_high_inbound(inbound),
        "stale": check_stale(pages),
        "orphans": check_orphans(pages, inbound),
        "broken_links": check_broken_links(pages, outbound, vault_stems),
        "tier_distribution": check_tier_distribution(pages),
        "index_consistency": check_index_consistency(pages),
    }

    # Summary counts for quick scan
    report["summary"] = {
        "missing_source_count": len(report["missing_source"]),
        "high_inbound_count":   len(report["high_inbound"]),
        "stale_count":          len(report["stale"]),
        "orphan_count":         len(report["orphans"]),
        "broken_link_count":    len(report["broken_links"]),
        "tier_primary_count":   len(report["tier_distribution"]["primary"]),
        "tier_secondary_count": len(report["tier_distribution"]["secondary"]),
        "tier_tertiary_count":  len(report["tier_distribution"]["tertiary"]),
        "tier_unset_count":     len(report["tier_distribution"]["unset"]),
        "missing_from_index_count": len(report["index_consistency"]["missing_from_index"]),
        "ghost_in_index_count":     len(report["index_consistency"]["ghost_in_index"]),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
