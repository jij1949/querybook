import { tags as t } from '@lezer/highlight';
import { darcula } from '@uiw/codemirror-theme-darcula';
import { duotoneDark, duotoneLight } from '@uiw/codemirror-theme-duotone';
import { githubDark, githubLight } from '@uiw/codemirror-theme-github';
import { monokaiInit } from '@uiw/codemirror-theme-monokai';
import { nord } from '@uiw/codemirror-theme-nord';
import { quietlight } from '@uiw/codemirror-theme-quietlight';
import { solarizedDark, solarizedLight } from '@uiw/codemirror-theme-solarized';
import { tokyoNightStorm } from '@uiw/codemirror-theme-tokyo-night-storm';
import { vscodeDark, vscodeLight } from '@uiw/codemirror-theme-vscode';
import { xcodeLightInit } from '@uiw/codemirror-theme-xcode';

export const getTheme = (themeName) => {
    switch (themeName) {
        case 'darcula':
            return darcula;
        case 'duotone-dark':
            return duotoneDark;
        case 'duotone-light':
            return duotoneLight;
        case 'github-light':
            return githubLight;
        case 'github-dark':
            return githubDark;
        case 'nord':
            return nord;
        case 'quietlight':
            return quietlight;
        case 'solarized-light':
            return solarizedLight;
        case 'solarized-dark':
            return solarizedDark;
        case 'tokyo-night-storm':
            return tokyoNightStorm;
        case 'vscode-light':
            return vscodeLight;
        case 'vscode-dark':
            return vscodeDark;
        case 'dark':
        case 'monokai':
            return CustomMonokaiDarkTheme;
        case 'light':
        case 'xcode':
        default:
            return CustomXcodeTheme;
    }
};

export const CustomMonokaiDarkTheme = monokaiInit({
    settings: {
        gutterBackground: '#3b393a',
    },
    styles: [
        { tag: [t.name], color: 'var(--text-dark)' },
        { tag: [t.constant(t.name), t.standard(t.name)], color: '#FD971F' },
    ],
});

export const CustomXcodeTheme = xcodeLightInit({
    settings: {
        background: '#fafafa',
        gutterBackground: '#f2f2f2;',
    },
    styles: [
        { tag: [t.special(t.propertyName)], color: '#005cc5' },
        { tag: [t.constant(t.name), t.standard(t.name)], color: '#D23423' },
        { tag: [t.number], color: '#098658' },
    ],
});
