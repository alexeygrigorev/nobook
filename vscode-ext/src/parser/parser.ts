/**
 * Parse .py files with @block markers into structured blocks.
 *
 * Ported from nobook/parser.py
 *
 * Format: A block starts at `# @block=name` and continues until
 * the next `# @block=...` line or end of file. No `# @end` needed.
 * Lines before the first block are the preamble (preserved but not executed).
 */

import { Block, ParsedFile, ParseError } from './types';

const BLOCK_START_RE = /^#\s*@block=(\S+)\s*$/;

export function parseString(text: string): ParsedFile {
  const rawLines = text.split('\n');
  const blocks: Block[] = [];
  const seenNames = new Set<string>();
  const preamble: string[] = [];

  let currentName: string | null = null;
  let currentLines: string[] = [];
  let currentStart = -1;

  for (let i = 0; i < rawLines.length; i++) {
    const line = rawLines[i];
    const match = line.match(BLOCK_START_RE);

    if (match) {
      // Close previous block if any
      if (currentName !== null) {
        blocks.push({
          name: currentName,
          lines: currentLines,
          startLine: currentStart,
        });
      }

      const name = match[1];
      if (seenNames.has(name)) {
        throw new ParseError(`Line ${i + 1}: duplicate block name '${name}'`);
      }
      seenNames.add(name);
      currentName = name;
      currentLines = [];
      currentStart = i;
    } else if (currentName !== null) {
      currentLines.push(line);
    } else {
      preamble.push(line);
    }
  }

  // Close final block
  if (currentName !== null) {
    blocks.push({
      name: currentName,
      lines: currentLines,
      startLine: currentStart,
    });
  }

  // Build block map
  const blockMap = new Map<string, Block>();
  for (const block of blocks) {
    blockMap.set(block.name, block);
  }

  return {
    preamble,
    blocks,
    rawLines,
    blockMap,
  };
}

export function parseFile(content: string): ParsedFile {
  return parseString(content);
}

/**
 * Generate unique block name based on existing names
 */
export function uniqueName(base: string, used: Set<string>): string {
  if (!used.has(base)) {
    return base;
  }
  let i = 1;
  while (used.has(`${base}-${i}`)) {
    i++;
  }
  return `${base}-${i}`;
}
