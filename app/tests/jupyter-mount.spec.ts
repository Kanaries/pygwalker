import { expect, test } from '@playwright/test';
import { smokeProps } from './fixtures/props';

// Exercise the exported mount with the real app and Graphic Walker. Only kernel I/O is stubbed.
test('isolates host CSS and updates the editor and portals without losing charts', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/');
    const before = await page.evaluate(() => {
        document.body.insertAdjacentHTML('afterbegin', '<section id="host-probe"><h1>Notebook</h1><ul><li>Markdown</li></ul><button>Host toolbar</button></section>');
        const snapshot = () => ['body', '#host-probe h1', '#host-probe ul', '#host-probe button'].map(selector => {
            const css = getComputedStyle(document.querySelector(selector)!);
            return [css.margin, css.padding, css.lineHeight, css.boxSizing, css.fontSize, css.borderWidth];
        });
        (window as any).hostSnapshot = snapshot;
        return snapshot();
    });
    await page.evaluate(async props => {
        const { default: app } = await import('/pyg_dev_app/src/index.tsx');
        const container = document.createElement('div');
        container.id = 'extension';
        document.body.append(container);
        (window as any).mount = await app.mountPygWalker(container, props, {
            sendMsg: async () => ({ code: 0, data: {}, message: 'success' }),
            sendMsgAsync: () => {},
            registerEndpoint: () => {},
        });
    }, smokeProps);
    const extension = page.locator('#extension');
    await expect(extension.getByText('Smoke chart').first()).toBeVisible();
    await expect(extension.locator('canvas').last()).toBeVisible();
    expect(await page.evaluate(() => (window as any).hostSnapshot())).toEqual(before);
    expect(await extension.evaluate(el => !!el.shadowRoot)).toBe(true);

    await extension.getByRole('tab', { name: '+ New', exact: true }).click();
    await expect(extension.getByRole('tab', { name: 'Chart 2', exact: true })).toBeVisible();
    await extension.getByRole('tab', { name: 'Smoke chart', exact: true }).click();

    for (const [appearance, background, foreground, primary] of [
        ['dark', '0 0% 6.7%', '0 0% 87%', '207 90% 54%'],
        ['light', '0 0% 100%', '0 0% 13%', '210 80% 46%'],
    ]) {
        await page.evaluate(({ appearance, background, foreground, primary }) => {
            (window as any).mount.setAppearance(appearance);
            (window as any).mount.setTheme({
                '--background': background,
                '--foreground': foreground,
                '--primary': primary,
                '--popover': background,
                '--popover-foreground': foreground,
            });
        }, { appearance, background, foreground, primary });
        const expected = await page.evaluate(background => {
            const probe = document.createElement('span');
            probe.style.background = `hsl(${background})`;
            document.body.append(probe);
            const color = getComputedStyle(probe).backgroundColor;
            probe.remove();
            return color;
        }, background);
        await expect(extension.locator('.App').first()).toHaveCSS('background-color', expected);
        await expect(extension.locator('.App').first()).toHaveCSS('--primary', primary);
        await expect(extension.getByText('Smoke chart').first()).toBeVisible();
        await expect(extension.locator('canvas').last()).toBeVisible();
        await expect(extension.getByRole('tab', { name: 'Chart 2', exact: true })).toBeVisible();

        // Graphic Walker's portal has its own shadow root and palette.
        await extension.locator('button[aria-haspopup="menu"]').first().click();
        const menu = page.getByRole('menu');
        await expect(menu).toBeVisible();
        await expect(menu).toHaveCSS('background-color', expected);
        await expect(menu).toHaveCSS('--primary', primary);
        await page.keyboard.press('Escape');
        await expect(menu).toHaveCount(0);

        // PyGWalker's own portal must stay inside the new shadow boundary.
        // Graphic Walker renders icon-only toolbar buttons without accessible names.
        await extension.locator('button').filter({
            has: page.locator('path[d^="M14.25 9.75"]'),
        }).click();
        const dialog = extension.getByRole('dialog');
        await expect(dialog).toBeVisible();
        await expect(dialog).toHaveCSS('background-color', expected);
        expect(await dialog.evaluate(el => el.getRootNode() === document.querySelector('#extension')!.shadowRoot)).toBe(true);
        await dialog.getByRole('button', { name: 'Cancel' }).click();
        await expect(dialog).toHaveCount(0);
        expect(await page.evaluate(() => (window as any).hostSnapshot())).toEqual(before);
    }
    await page.evaluate(() => (window as any).mount.unmount());
    await expect(extension.getByText('Smoke chart')).toHaveCount(0);
    await expect(extension).toHaveJSProperty('childElementCount', 0);
    expect(await page.evaluate(() => (window as any).hostSnapshot())).toEqual(before);
    expect(errors).toEqual([]);
});
