import type { IVisSpec } from '@kanaries/graphic-walker/dist/interfaces'

export function encodeSpec(value: IVisSpec[]): string {
    const list = [] as typeof value;
    for (const vis of value) {
        const res = { ...vis };
        const filters = [] as typeof res.encodings.filters[number][];
        for (const filter of vis.encodings.filters) {
            if (filter.rule?.type === 'one of') {
                filters.push({
                    ...filter,
                    rule: {
                        ...filter.rule,
                        // @ts-ignore
                        value: [...filter.rule.value],
                    },
                });
            } else {
                filters.push(filter);
            }
        }
        res.encodings = {
            ...res.encodings,
            filters,
        };
        list.push(res);
    }
    return JSON.stringify(list);
}

export function decodeSpec(value: string): IVisSpec[] {
    const list = JSON.parse(value);
    const result = [] as IVisSpec[];
    for (const vis of list) {
        const res = { ...vis };
        const filters = [] as typeof res.encodings.filters[number][];
        for (const filter of vis.encodings.filters) {
            if (filter.rule?.type === 'one of') {
                filters.push({
                    ...filter,
                    rule: {
                        ...filter.rule,
                        // @ts-ignore
                        value: new Set(filter.rule.value),
                    },
                });
            } else {
                filters.push(filter);
            }
        }
        res.encodings = {
            ...res.encodings,
            filters,
        };
        result.push(res);
    }
    return result;
}
