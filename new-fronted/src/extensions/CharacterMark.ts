import { Mark, mergeAttributes } from '@tiptap/core';

export interface CharacterMarkAttributes {
  name: string;
  id?: string;
}

export const CharacterMark = Mark.create<CharacterMarkAttributes>({
  name: 'character',

  parseHTML() {
    return [
      {
        tag: 'span[data-character]',
      },
    ];
  },

  renderHTML({ HTMLAttributes, mark }) {
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-character': mark.attrs.name,
        'data-character-id': mark.attrs.id,
        class: 'novel-character-mark',
      }),
      0,
    ];
  },

  addAttributes() {
    return {
      name: {
        default: '',
      },
      id: {
        default: '',
      },
    };
  },
});
