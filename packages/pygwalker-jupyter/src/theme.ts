import type { IPygWalkerTheme } from './pygwalker-app';

const JUPYTER_THEME_TOKEN_MAP: ReadonlyArray<
  readonly [keyof IPygWalkerTheme, string]
> = [
  ['--background', '--jp-layout-color0'],
  ['--foreground', '--jp-ui-font-color1'],
  ['--card', '--jp-layout-color1'],
  ['--card-foreground', '--jp-ui-font-color1'],
  ['--popover', '--jp-layout-color1'],
  ['--popover-foreground', '--jp-ui-font-color1'],
  ['--primary', '--jp-brand-color1'],
  ['--primary-foreground', '--jp-ui-inverse-font-color1'],
  ['--secondary', '--jp-layout-color2'],
  ['--secondary-foreground', '--jp-ui-font-color1'],
  ['--muted', '--jp-layout-color1'],
  ['--muted-foreground', '--jp-ui-font-color2'],
  ['--accent', '--jp-layout-color2'],
  ['--accent-foreground', '--jp-ui-font-color1'],
  ['--destructive', '--jp-error-color1'],
  ['--destructive-foreground', '--jp-ui-inverse-font-color1'],
  ['--border', '--jp-border-color2'],
  ['--input', '--jp-border-color1'],
  ['--ring', '--jp-brand-color1']
];

const FOREGROUND_SURFACES: Record<string, string> = {
  '--card-foreground': '--jp-layout-color1',
  '--popover-foreground': '--jp-layout-color1',
  '--primary-foreground': '--jp-brand-color1',
  '--secondary-foreground': '--jp-layout-color2',
  '--muted-foreground': '--jp-layout-color1',
  '--accent-foreground': '--jp-layout-color2',
  '--destructive-foreground': '--jp-error-color1'
};

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

function rgbToHslToken(
  red: number,
  green: number,
  blue: number,
  alpha: number
): string {
  const r = red / 255;
  const g = green / 255;
  const b = blue / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const delta = max - min;
  let hue = 0;

  if (delta !== 0) {
    if (max === r) {
      hue = 60 * (((g - b) / delta) % 6);
    } else if (max === g) {
      hue = 60 * ((b - r) / delta + 2);
    } else {
      hue = 60 * ((r - g) / delta + 4);
    }
  }
  if (hue < 0) {
    hue += 360;
  }

  const lightness = (max + min) / 2;
  const saturation =
    delta === 0 ? 0 : delta / (1 - Math.abs(2 * lightness - 1));
  const alphaSuffix = alpha < 1 ? ` / ${round(alpha)}` : '';
  return `${round(hue)} ${round(saturation * 100)}% ${round(
    lightness * 100
  )}%${alphaSuffix}`;
}

/**
 * Resolve Jupyter's arbitrary CSS colors into the raw HSL channels used by
 * PyGWalker's shadcn and Graphic Walker styles (`hsl(var(--token))`).
 */
export function readJupyterTheme(): IPygWalkerTheme {
  const probe = document.createElement('span');
  probe.style.display = 'none';
  document.body.append(probe);

  const canvas = document.createElement('canvas');
  canvas.width = 1;
  canvas.height = 1;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  const rootStyle = getComputedStyle(document.documentElement);
  const theme: IPygWalkerTheme = {};

  try {
    if (!context) {
      return theme;
    }

    for (const [pygwalkerToken, jupyterToken] of JUPYTER_THEME_TOKEN_MAP) {
      if (!rootStyle.getPropertyValue(jupyterToken).trim()) {
        continue;
      }

      probe.style.color = `var(${jupyterToken})`;
      const resolvedColor = getComputedStyle(probe).color;
      context.clearRect(0, 0, 1, 1);
      // Graphic Walker's color parser drops alpha. Composite translucent host
      // colors onto their surface first so text keeps the host's contrast.
      const surface = FOREGROUND_SURFACES[pygwalkerToken] ?? '--jp-layout-color0';
      probe.style.color = `var(${surface}, white)`;
      context.fillStyle = getComputedStyle(probe).color;
      context.fillRect(0, 0, 1, 1);
      context.fillStyle = resolvedColor;
      context.fillRect(0, 0, 1, 1);
      const [red, green, blue, alpha] = context.getImageData(0, 0, 1, 1).data;
      theme[pygwalkerToken] = rgbToHslToken(
        red,
        green,
        blue,
        alpha / 255
      );
    }
  } finally {
    probe.remove();
  }

  return theme;
}
