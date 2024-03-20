import { VegaliteMapper } from '@kanaries/graphic-walker/lib/vl2gw';

export default function Transform(str: string) {
    const params = JSON.parse(str);
    return JSON.stringify(
        VegaliteMapper(...[params["vl"], params["allFields"], params["visId"], params["name"]])
    );
}
