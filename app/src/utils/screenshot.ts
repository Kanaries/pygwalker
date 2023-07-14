import * as htmlToImage from 'html-to-image';

export async function domToPng(dom: HTMLElement): Promise<string> {
    const dataUrl = await htmlToImage.toPng(dom, {width: dom.scrollWidth, height: dom.scrollHeight});
    return dataUrl;
}
