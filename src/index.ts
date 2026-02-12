import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
} from '@jupyterlab/application';
import { ILauncher } from '@jupyterlab/launcher';
import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';
import { LabIcon } from '@jupyterlab/ui-components';

const COMMAND = 'nobook:create-new';

const nobookIcon = new LabIcon({
  name: 'nobook:icon',
  svgstr: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
    <rect x="3" y="2" width="18" height="20" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <text x="12" y="15" text-anchor="middle" font-size="8" font-family="monospace" fill="currentColor">.py</text>
  </svg>`,
});

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'nobook-labextension:plugin',
  autoStart: true,
  requires: [IDefaultFileBrowser],
  optional: [ILauncher],
  activate: (
    app: JupyterFrontEnd,
    browser: IDefaultFileBrowser,
    launcher: ILauncher | null,
  ) => {
    const { commands } = app;

    commands.addCommand(COMMAND, {
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

    if (launcher) {
      launcher.add({
        command: COMMAND,
        category: 'Notebook',
        rank: 1,
      });
    }

    console.log('nobook-labextension activated');
  },
};

export default plugin;
