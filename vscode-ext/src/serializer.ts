/**
 * Nobook Notebook Serializer
 *
 * Converts between .py files with # @block= markers and VS Code notebook format.
 */

import * as vscode from 'vscode';
import { parseString, uniqueName, Block, ParsedFile } from './parser';

/**
 * Metadata structure stored in each notebook cell
 */
interface NobookCellMetadata {
  block?: string;
}

export class NobookSerializer implements vscode.NotebookSerializer {
  async deserialize(content: Uint8Array): Promise<vscode.NotebookData> {
    const text = new TextDecoder().decode(content);
    const parsed = parseString(text);

    const cells: vscode.NotebookCellData[] = [];

    // Skip preamble for now - it's preserved but not shown as a cell
    // We could add it as a read-only markdown cell if needed

    for (const block of parsed.blocks) {
      const cell = new vscode.NotebookCellData(
        vscode.NotebookCellKind.Code,
        block.lines.join('\n'),
        'python'
      );

      // Store block name in metadata
      const metadata: NobookCellMetadata = { block: block.name };
      cell.metadata = metadata;

      cells.push(cell);
    }

    return new vscode.NotebookData(cells);
  }

  async serialize(data: vscode.NotebookData): Promise<Uint8Array> {
    const used = new Set<string>();
    let output = '';

    // Get default block name prefix from config
    const config = vscode.workspace.getConfiguration('nobook');
    const defaultBlockPrefix = config.get<string>('defaultBlockName', 'cell');

    for (let i = 0; i < data.cells.length; i++) {
      const cell = data.cells[i];
      const cellMetadata = cell.metadata as NobookCellMetadata | undefined;

      // Get or generate block name
      let blockName = cellMetadata?.block;
      if (!blockName) {
        const base = `${defaultBlockPrefix}_${i}`;
        blockName = uniqueName(base, used);
      } else if (used.has(blockName)) {
        // Handle duplicate names
        blockName = uniqueName(blockName, used);
      }

      used.add(blockName);

      // Write block marker and code
      output += `# @block=${blockName}\n`;
      output += cell.value;

      // Add newline if cell doesn't end with one
      if (!cell.value.endsWith('\n')) {
        output += '\n';
      }
    }

    return new TextEncoder().encode(output);
  }
}
