/**
 * Nobook VS Code Extension
 *
 * Main extension entry point
 */

import * as vscode from 'vscode';
import { NobookSerializer } from './serializer';
import { registerCommands, registerStatusBar } from './ui';

const NOTEBOOK_TYPE = 'nobook-notebook';

export function activate(context: vscode.ExtensionContext) {
  console.log('Nobook extension is now active!');

  // Register the notebook serializer
  const serializer = new NobookSerializer();
  const serializerDisposable = vscode.notebooks.registerNotebookSerializer(
    NOTEBOOK_TYPE,
    serializer,
    {
      transientOutputs: false,
      transientMetadata: {},
    }
  );

  // Register commands
  registerCommands(context);

  // Register status bar provider
  registerStatusBar(context);

  context.subscriptions.push(serializerDisposable);

  console.log('Nobook extension activated successfully!');
}

export function deactivate() {
  console.log('Nobook extension deactivated');
}
