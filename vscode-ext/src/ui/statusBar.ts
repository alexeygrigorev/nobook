/**
 * Cell status bar - displays block names on notebook cells
 */

import * as vscode from 'vscode';
import { NobookCellMetadata } from '../serializer';

/**
 * Register cell status bar item provider
 */
export function registerStatusBar(context: vscode.ExtensionContext): void {
  // Create a status bar item provider for notebook cells
  const provider = vscode.notebooks.registerNotebookCellStatusBarItemProvider(
    'nobook-notebook',
    {
      provideCellStatusBarItems: (
        cell: vscode.NotebookCell
      ): vscode.NotebookCellStatusBarItem[] => {
        const metadata = cell.metadata as NobookCellMetadata | undefined;
        const blockName = metadata?.block;

        if (!blockName) {
          return [];
        }

        const item = new vscode.NotebookCellStatusBarItem(
          `$(tag) ${blockName}`,
          vscode.NotebookCellStatusBarAlignment.Right
        );

        // Add a command to edit the block name (for future enhancement)
        // item.command = {
        //   command: 'nobook.renameBlock',
        //   arguments: [cell],
        //   title: 'Rename block'
        // };

        return [item];
      },
    }
  );

  context.subscriptions.push(provider);
}
