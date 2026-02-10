import { Node, mergeAttributes } from '@tiptap/core';

export interface SceneAttributes {
  sceneNumber?: number;
  location?: string;
  time?: string;
  mood?: string;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    insertScene: (attributes: SceneAttributes) => ReturnType;
    setSceneAttributes: (attributes: Partial<SceneAttributes>) => ReturnType;
  }
}

export const SceneNode = Node.create<SceneAttributes>({
  name: 'scene',

  group: 'block',
  content: 'inline*',

  parseHTML() {
    return [
      {
        tag: 'div[data-scene]',
      },
    ];
  },

  renderHTML({ HTMLAttributes, node }) {
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-scene': '',
        'data-scene-number': node.attrs.sceneNumber,
        class: 'novel-scene',
      }),
      ['div', { class: 'scene-header' },
        ['span', { class: 'scene-number' }, `场景 ${node.attrs.sceneNumber}`],
        ['span', { class: 'scene-location' }, node.attrs.location],
        ['span', { class: 'scene-time' }, node.attrs.time],
      ],
      ['div', { class: 'scene-content' }, 0],
    ];
  },

  addAttributes() {
    return {
      sceneNumber: {
        default: 1,
        parseHTML: (element) => element.getAttribute('data-scene-number'),
        renderHTML: (attributes) => ({
          'data-scene-number': attributes.sceneNumber,
        }),
      },
      location: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-location'),
      },
      time: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-time'),
      },
      mood: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-mood'),
      },
    };
  },

  addCommands() {
    return {
      insertScene: (attributes: SceneAttributes) => ({ chain }: { chain: any }) => {
        return chain()
          .insertContent({
            type: this.name,
            attrs: attributes,
          })
          .focus()
          .run();
      },
      setSceneAttributes: (attributes: Partial<SceneAttributes>) => ({ chain }: { chain: any }) => {
        return chain()
          .updateAttributes(this.name, attributes)
          .run();
      },
    } as any;
  },

  addKeyboardShortcuts() {
    return {
      'Mod-Shift-S': () => {
        const sceneNodes = this.editor.$nodes('scene');
        const cmd = this.editor.commands as unknown as { insertScene: (attrs: SceneAttributes) => boolean };
        return cmd.insertScene({
          sceneNumber: (sceneNodes?.length || 0) + 1,
        });
      },
    };
  },
});
