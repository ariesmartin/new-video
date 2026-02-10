import { Node, mergeAttributes } from '@tiptap/core';

export interface DialogueAttributes {
  character: string;
  emotion?: string;
  action?: string;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    insertDialogue: (attributes: DialogueAttributes) => ReturnType;
  }
}

export const DialogueNode = Node.create<DialogueAttributes>({
  name: 'dialogue',

  group: 'block',
  content: 'text*',
  inline: false,

  parseHTML() {
    return [
      {
        tag: 'div[data-dialogue]',
      },
    ];
  },

  renderHTML({ HTMLAttributes, node }) {
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-dialogue': '',
        class: 'novel-dialogue',
      }),
      ['div', { class: 'dialogue-character' }, node.attrs.character],
      node.attrs.emotion ? ['span', { class: 'dialogue-emotion' }, `(${node.attrs.emotion})`] : '',
      ['div', { class: 'dialogue-content' }, 0],
      node.attrs.action ? ['div', { class: 'dialogue-action' }, node.attrs.action] : '',
    ];
  },

  addAttributes() {
    return {
      character: {
        default: '',
        parseHTML: (element) => element.querySelector('.dialogue-character')?.textContent || '',
      },
      emotion: {
        default: '',
      },
      action: {
        default: '',
      },
    };
  },

  addCommands() {
    return {
      insertDialogue: (attributes: DialogueAttributes) => ({ chain }: { chain: any }) => {
        return chain()
          .insertContent({
            type: this.name,
            attrs: attributes,
          })
          .focus()
          .run();
      },
    } as any;
  },
});
