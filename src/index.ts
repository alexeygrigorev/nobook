import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
} from '@jupyterlab/application';
import { ILauncher } from '@jupyterlab/launcher';
import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { Cell } from '@jupyterlab/cells';
import { LabIcon } from '@jupyterlab/ui-components';

const COMMAND_NEW = 'nobook:create-new';
const COMMAND_OPEN = 'nobook:open-as-notebook';

const nobookIcon = new LabIcon({
  name: 'nobook:icon',
  svgstr: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
    <rect x="3" y="2" width="18" height="20" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <text x="12" y="15" text-anchor="middle" font-size="8" font-family="monospace" fill="currentColor">.py</text>
  </svg>`,
});

function uniqueName(base: string, used: Set<string>): string {
  if (!used.has(base)) {
    return base;
  }
  // First duplicate gets -copy
  const copyName = `${base}-copy`;
  if (!used.has(copyName)) {
    return copyName;
  }
  // Further duplicates get -copy-1, -copy-2, etc.
  let i = 1;
  while (used.has(`${copyName}-${i}`)) {
    i++;
  }
  return `${copyName}-${i}`;
}

function ensureUniqueBlockNames(notebook: { widgets: readonly Cell[] }): void {
  const used = new Set<string>();

  notebook.widgets.forEach((cell: Cell, index: number) => {
    if (cell.model.type !== 'code') {
      return;
    }
    let meta = cell.model.getMetadata('nobook') as
      | { block?: string }
      | undefined;
    let name = meta?.block;

    if (!name) {
      name = uniqueName(`cell-${index}`, used);
      cell.model.setMetadata('nobook', { ...meta, block: name });
    } else if (used.has(name)) {
      const newName = uniqueName(name, used);
      cell.model.setMetadata('nobook', { ...meta, block: newName });
      name = newName;
    }
    used.add(name);
  });
}

function updateCellLabels(panel: NotebookPanel): void {
  const notebook = panel.content;
  ensureUniqueBlockNames(notebook);
  notebook.widgets.forEach((cell: Cell) => {
    const meta = cell.model.getMetadata('nobook') as
      | { block?: string }
      | undefined;
    const blockName = meta?.block ?? '';

    let label = cell.node.querySelector('.nobook-block-label') as HTMLElement | null;

    if (blockName) {
      if (!label) {
        label = document.createElement('div');
        label.className = 'nobook-block-label';

        const input = document.createElement('input');
        input.className = 'nobook-block-input';
        input.type = 'text';
        input.spellcheck = false;
        label.appendChild(input);

        const commitForCell = cell;
        const commit = (): void => {
          const curMeta = commitForCell.model.getMetadata('nobook') as
            | { block?: string }
            | undefined;
          const newName = input.value.trim();
          if (newName && newName !== curMeta?.block) {
            commitForCell.model.setMetadata('nobook', { ...curMeta, block: newName });
          }
        };
        input.addEventListener('blur', commit);
        input.addEventListener('keydown', (e: KeyboardEvent) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
          }
          e.stopPropagation();
        });

        cell.node.insertBefore(label, cell.node.firstChild);
      }
      const input = label.querySelector('input') as HTMLInputElement;
      if (input && document.activeElement !== input) {
        input.value = blockName;
      }
    } else if (label) {
      label.remove();
    }
  });
}

function attachCellLabels(panel: NotebookPanel): void {
  const notebook = panel.content;

  // Update when cells change
  if (notebook.model) {
    notebook.model.cells.changed.connect(() => {
      requestAnimationFrame(() => updateCellLabels(panel));
    });
  }

  // Also update on active cell change (catches metadata edits)
  notebook.activeCellChanged.connect(() => updateCellLabels(panel));
}

const launcherPlugin: JupyterFrontEndPlugin<void> = {
  id: 'nobook-labextension:launcher',
  autoStart: true,
  requires: [IDefaultFileBrowser],
  optional: [ILauncher],
  activate: (
    app: JupyterFrontEnd,
    browser: IDefaultFileBrowser,
    launcher: ILauncher | null,
  ) => {
    const { commands } = app;

    commands.addCommand(COMMAND_NEW, {
      label: 'Nobook',
      caption: 'Create a new .py notebook',
      icon: nobookIcon,
      execute: async () => {
        const cwd = browser.model.path;
        const model = await commands.execute('docmanager:new-untitled', {
          path: cwd,
          type: 'notebook',
        });
        if (model !== undefined) {
          await commands.execute('docmanager:open', {
            path: model.path,
            factory: 'Notebook',
            kernel: { name: 'python3' },
          });
        }
      },
    });

    commands.addCommand(COMMAND_OPEN, {
      label: 'Open as Nobook',
      caption: 'Open .py file in notebook editor',
      icon: nobookIcon,
      isVisible: () => {
        const item = browser.selectedItems().next();
        return !item.done && item.value.path.endsWith('.py');
      },
      execute: () => {
        const item = browser.selectedItems().next();
        if (!item.done) {
          commands.execute('docmanager:open', {
            path: item.value.path,
            factory: 'Notebook',
            kernel: { name: 'python3' },
          });
        }
      },
    });

    app.contextMenu.addItem({
      command: COMMAND_OPEN,
      selector: '.jp-DirListing-item',
      rank: 3,
    });

    if (launcher) {
      launcher.add({
        command: COMMAND_NEW,
        category: 'Notebook',
        rank: 1,
      });
    }

    console.log('nobook-labextension:launcher activated');
  },
};

const cellLabelPlugin: JupyterFrontEndPlugin<void> = {
  id: 'nobook-labextension:cell-labels',
  autoStart: true,
  requires: [INotebookTracker],
  activate: (app: JupyterFrontEnd, tracker: INotebookTracker) => {
    tracker.widgetAdded.connect((_sender: INotebookTracker, panel: NotebookPanel) => {
      panel.context.ready.then(() => {
        attachCellLabels(panel);
        updateCellLabels(panel);
      });
    });

    console.log('nobook-labextension:cell-labels activated');
  },
};

export default [launcherPlugin, cellLabelPlugin];
