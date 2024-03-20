import { VegaliteMapper } from '@kanaries/graphic-walker/lib/vl2gw';

export default function FormatSpec(spec: any[], fields: any[]) {
    return spec.map((item, index) => {
        if (["config", "encodings", "visId"].every(key => item.hasOwnProperty(key))) {
            return item;
        } else {
            const result = VegaliteMapper(item, fields, Math.random().toString(16).split(".").at(1)!, `Chart ${index+1}`);
            return result;
        }
    })
}
