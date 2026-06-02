jest.mock('const/queryResultLimit', () => ({
    StatementExecutionDefaultResultSize: 1000,
}));

import {
    mapMetaToChartOptions,
    validateChartMeta,
} from 'lib/chart/chart-meta-processing';

const makeChartMeta = () => ({
    title: '',
    data: {
        source_type: 'cell_above',
        transformations: {
            format: {},
        },
    },
    chart: {
        type: 'line',
        x_axis: {
            col_idx: 0,
            label: '',
        },
        y_axis: {
            label: '',
        },
    },
});

describe('chart-meta-processing', () => {
    it('accepts valid chart meta without optional visual or series config', () => {
        expect(() => validateChartMeta(makeChartMeta() as any)).not.toThrow();

        const chartOptions = mapMetaToChartOptions(
            makeChartMeta() as any,
            'default',
            'category',
            'linear'
        ) as any;

        expect(chartOptions.plugins.legend.position).toBe('top');
        expect(chartOptions.plugins.legend.display).toBe(true);
        expect(chartOptions.maintainAspectRatio).toBeUndefined();
    });

    it('rejects chart meta without a valid chart type', () => {
        const meta: any = makeChartMeta();
        delete meta.chart.type;

        expect(() => validateChartMeta(meta as any)).toThrow(
            'Invalid chart configuration: chart.type must be one of'
        );
    });

    it('rejects cell source chart meta without a source id', () => {
        const meta: any = makeChartMeta();
        meta.data.source_type = 'cell';

        expect(() => validateChartMeta(meta as any)).toThrow(
            'Invalid chart configuration: data.source_ids[0] must be a number'
        );
    });
});
