/**
 * Nobook parser types
 * Matches the Python implementation in nobook/parser.py
 */

export interface Block {
  /** Block name from # @block=name marker */
  name: string;
  /** Lines of code in this block (excluding the marker line) */
  lines: string[];
  /** 0-indexed line number where # @block= marker appears */
  startLine: number;
}

export interface ParsedFile {
  /** Lines before the first # @block= marker */
  preamble: string[];
  /** All blocks found in the file */
  blocks: Block[];
  /** All lines from the original file */
  rawLines: string[];
  /** Map of block name -> Block for quick lookup */
  blockMap: Map<string, Block>;
}

export class ParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ParseError';
  }
}
