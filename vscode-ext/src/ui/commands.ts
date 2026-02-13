/**
 * Nobook commands
 */

import * as vscode from 'vscode';
import { parseString } from '../parser';

const NOBOOK_TYPE = 'nobook-notebook';

/**
 * Check if a file contains # @block= markers
 */
export function hasNobookMarkers(content: string): boolean {
  return /^#\s*@block=/.test(content);
}

/**
 * Open a .py file as a Nobook notebook
 */
export async function openAsNobook(uri: vscode.Uri): Promise<void> {
  try {
    // Read file content to check for markers
    const content = await vscode.workspace.fs.readFile(uri);
    const text = new TextDecoder().decode(content);

    // Check if file has nobook markers
    if (!hasNobookMarkers(text)) {
      const action = await vscode.window.showWarningMessage(
        'This file does not contain # @block= markers. Open as Nobook anyway?',
        'Open',
        'Cancel'
      );
      if (action !== 'Open') {
        return;
      }
    }

    // Close the text editor if open
    const tabs = vscode.window.tabGroups.all;
    for (const group of tabs) {
      for (const tab of group.tabs) {
        if (tab.input instanceof vscode.TabInputText && tab.input.uri.toString() === uri.toString()) {
          await vscode.window.tabGroups.close(tab);
          break;
        }
      }
    }

    // Open as notebook with nobook type
    await vscode.commands.executeCommand('vscode.openWith', uri, NOBOOK_TYPE);
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to open as Nobook: ${error}`);
  }
}

/**
 * Create a new Nobook notebook
 */
export async function createNewNobook(): Promise<void> {
  // Get the current workspace folder
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    vscode.window.showErrorMessage('No workspace folder open');
    return;
  }

  // Prompt for filename
  const filename = await vscode.window.showInputBox({
    prompt: 'Enter notebook filename',
    value: 'notebook.py',
    validateInput: (value) => {
      if (!value.endsWith('.py')) {
        return 'Filename must end with .py';
      }
      return null;
    },
  });

  if (!filename) {
    return;
  }

  const uri = vscode.Uri.joinPath(workspaceFolder.uri, filename);

  // Create template content
  const template = `# @block=setup
import numpy as np

# @block=example
x = np.array([1, 2, 3, 4, 5])
print(f"Mean: {x.mean():.2f}")
`;

  try {
    await vscode.workspace.fs.writeFile(uri, new TextEncoder().encode(template));
    await openAsNobook(uri);
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to create notebook: ${error}`);
  }
}

/**
 * Register all Nobook commands
 */
export function registerCommands(context: vscode.ExtensionContext): void {
  // Open as Nobook command
  const openCommand = vscode.commands.registerCommand(
    'nobook.openAsNobook',
    async (uri: vscode.Uri) => {
      // If called from context menu, uri is provided
      // If called from command palette, ask user to select file
      if (!uri) {
        const uris = await vscode.window.showOpenDialog({
          canSelectFiles: true,
          canSelectFolders: false,
          canSelectMany: false,
          filters: { Python: ['py'] },
        });
        if (!uris || uris.length === 0) {
          return;
        }
        uri = uris[0];
      }
      await openAsNobook(uri);
    }
  );

  // Create new notebook command
  const createCommand = vscode.commands.registerCommand(
    'nobook.createNew',
    createNewNobook
  );

  context.subscriptions.push(openCommand, createCommand);
}
