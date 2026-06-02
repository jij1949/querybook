import {
    ChartOptions,
    LinearScaleOptions,
    LineControllerDatasetOptions,
    ScaleOptions,
    TimeScaleOptions,
} from 'chart.js';

import { backgroundColor, fillColor, fontColor } from 'const/chartColors';
import { IDataChartCellMeta } from 'const/datadoc';
import {
    ChartDataAggType,
    ChartScaleFormat,
    chartScaleToChartJSScale,
    ChartScaleType,
    ChartSize,
    ChartValueDisplayType,
    ChartValueSourceType,
    chartTypes,
    IChartAxisMeta,
    IChartFormValues,
    ChartDataSourceType,
} from 'const/dataDocChart';
import { StatementExecutionDefaultResultSize } from 'const/queryResultLimit';
import type { DeepPartial } from 'lib/typescript';
import { formatNumber } from 'lib/utils/number';

function filterSeries<T, K extends keyof T>(
    series: Record<number, T>,
    filterBy: K
) {
    const obj: Record<number, T[K]> = {};
    for (const key in series) {
        if (series[key][filterBy] != null) {
            obj[key] = series[key][filterBy];
        }
    }
    return obj;
}

function rgb(rgbArr: number[]) {
    const prefix = rgbArr.length <= 3 ? 'rgb' : 'rgba';
    const content = rgbArr.map(String).join(', ');
    return `${prefix}(${content})`;
}

const validChartTypes = new Set(Object.keys(chartTypes));
const validSourceTypes: ChartDataSourceType[] = [
    'cell_above',
    'cell',
    'execution',
    'custom',
];

function isRecord(value: unknown): value is Record<string, unknown> {
    return value != null && typeof value === 'object' && !Array.isArray(value);
}

function assertValidChartConfig(
    isValid: unknown,
    errorMessage: string
): asserts isValid {
    if (!isValid) {
        throw new Error(`Invalid chart configuration: ${errorMessage}`);
    }
}

export function validateChartMeta(meta: IDataChartCellMeta) {
    const chartMeta = meta as any;

    assertValidChartConfig(isRecord(chartMeta), 'meta must be an object');
    assertValidChartConfig(isRecord(chartMeta.data), 'data must be an object');

    const sourceType = chartMeta.data.source_type;
    assertValidChartConfig(
        typeof sourceType === 'string' &&
            validSourceTypes.includes(sourceType as ChartDataSourceType),
        `data.source_type must be one of ${validSourceTypes.join(', ')}`
    );

    if (sourceType === 'cell' || sourceType === 'execution') {
        assertValidChartConfig(
            Array.isArray(chartMeta.data.source_ids) &&
                typeof chartMeta.data.source_ids[0] === 'number',
            'data.source_ids[0] must be a number for cell and execution sources'
        );
    }

    assertValidChartConfig(
        isRecord(chartMeta.data.transformations),
        'data.transformations must be an object'
    );
    assertValidChartConfig(
        isRecord(chartMeta.data.transformations.format),
        'data.transformations.format must be an object'
    );

    assertValidChartConfig(
        isRecord(chartMeta.chart),
        'chart must be an object'
    );
    assertValidChartConfig(
        typeof chartMeta.chart.type === 'string' &&
            validChartTypes.has(chartMeta.chart.type),
        `chart.type must be one of ${Array.from(validChartTypes).join(', ')}`
    );
    assertValidChartConfig(
        isRecord(chartMeta.chart.x_axis),
        'chart.x_axis must be an object'
    );

    const xAxisColIndex = chartMeta.chart.x_axis.col_idx;
    assertValidChartConfig(
        typeof xAxisColIndex === 'number' &&
            Number.isInteger(xAxisColIndex) &&
            xAxisColIndex >= 0,
        'chart.x_axis.col_idx must be a non-negative integer'
    );
    assertValidChartConfig(
        isRecord(chartMeta.chart.y_axis),
        'chart.y_axis must be an object'
    );

    for (const [key, seriesMeta] of Object.entries(
        chartMeta.chart.y_axis.series ?? {}
    )) {
        if ((seriesMeta as any).color != null) {
            assertValidChartConfig(
                typeof (seriesMeta as any).color === 'number' &&
                    (seriesMeta as any).color >= 0,
                `chart.y_axis.series[${key}].color must be a non-negative number (palette index)`
            );
        }
    }
}

export function getDataTransformationOptions(meta: IDataChartCellMeta) {
    validateChartMeta(meta);

    const { transformations } = meta.data;
    const aggregate = Boolean(transformations.aggregate);
    const aggSeries = filterSeries(meta.chart.y_axis.series ?? {}, 'agg_type');

    let aggType: ChartDataAggType = 'sum';
    let formatAggCol: number;
    let formatSeriesCol: number;
    let formatValueCols: number[] = [];

    if (aggregate) {
        formatAggCol = transformations.format.agg_col;
        if (formatAggCol < 0) {
            // legacy code can make it -1
            formatAggCol = undefined;
        }
        formatSeriesCol = transformations.format.series_col;
        formatValueCols = transformations.format.value_cols ?? [];

        const aggTypeArr = Object.values(aggSeries);
        if (aggTypeArr.length) {
            aggType = aggTypeArr.every((type) => aggTypeArr[0] === type)
                ? aggTypeArr[0]
                : undefined;
        }
    }

    return {
        formatAggCol,
        formatSeriesCol,
        formatValueCols,
        aggregate,

        switch: Boolean(transformations.switch),
        aggSeries,
        aggType,
        sortIndex: meta.chart.x_axis.sort?.idx,
        sortAsc: meta.chart.x_axis.sort?.asc ?? true,
        xAxisIdx: meta.chart.x_axis.col_idx,
    };
}

export function getAxisOptions(axisMeta: IChartAxisMeta) {
    return {
        label: axisMeta?.label ?? '',
        scale: axisMeta?.scale,
        min: axisMeta?.min,
        max: axisMeta?.max,
        format: axisMeta?.format ?? null,
    };
}

export function mapMetaToFormVals(
    meta: IDataChartCellMeta,
    cellAboveId: number
): IChartFormValues {
    validateChartMeta(meta);

    const cellId =
        meta.data.source_type === 'cell_above'
            ? cellAboveId
            : meta.data.source_type === 'cell'
            ? meta.data.source_ids[0]
            : undefined;

    const executionId =
        meta.data.source_type === 'execution'
            ? meta.data.source_ids[0]
            : undefined;
    const hiddenSeries = Object.entries(meta.chart.y_axis.series ?? {})
        .filter(([_, val]) => val.hidden)
        .map(([idx, _]) => Number(idx));

    return {
        // data source
        sourceType: meta.data.source_type,
        cellId,
        executionId,
        limit: meta.data.limit ?? StatementExecutionDefaultResultSize,

        // data transformation
        ...getDataTransformationOptions(meta),

        // axes
        xAxis: getAxisOptions(meta.chart.x_axis),
        xIndex: meta.chart.x_axis.col_idx,
        sortIndex: meta.chart.x_axis.sort?.idx,
        sortAsc: meta.chart.x_axis.sort?.asc ?? true,

        yAxis: getAxisOptions(meta.chart.y_axis),
        stack: Boolean(meta.chart.y_axis.stack),

        zIndex: meta.chart.z_axis?.col_idx,

        hiddenSeries,
        coloredSeries: filterSeries(meta.chart.y_axis.series ?? {}, 'color'),
        // chart
        chartType: meta.chart.type,

        // labels
        title: meta.title || '',
        legendPosition: meta.visual?.legend_position ?? 'top',
        legendDisplay: meta.visual?.legend_display ?? true,
        connectMissing: meta.visual?.connect_missing ?? false,
        size: meta.visual?.size ?? ChartSize.AUTO,

        valueDisplay:
            meta.visual?.values?.display ?? ChartValueDisplayType.FALSE,
        valuePosition: meta.visual?.values?.position ?? 'center',
        valueAlignment: meta.visual?.values?.alignment ?? 'center',
        valueSource: meta.visual?.values?.source ?? ChartValueSourceType.VALUE,
    };
}

export function mapMetaToChartOptions(
    meta: IDataChartCellMeta,
    theme: string,
    xAxesScaleType: ChartScaleType,
    yAxesScaleType: ChartScaleType
): ChartOptions {
    validateChartMeta(meta);

    const visual = meta.visual ?? {};
    const visualValues = visual.values;
    const optionsObj: ChartOptions = {
        responsive: true,

        interaction: {
            mode: 'index',
            intersect: true,
        },
        plugins: {
            legend: {
                position: visual.legend_position ?? 'top',
                display: visual.legend_display ?? true,
            },
            title: {
                display: !!meta.title?.length,
                text: meta.title ?? '',
                font: {
                    family: 'Poppins',
                    weight: 'bold',
                    size: 16,
                },
            },
            tooltip: {
                position: 'nearest',
                backgroundColor: backgroundColor[theme],

                bodyColor: rgb(fontColor[theme]),
                titleColor: rgb(fontColor[theme]),
                bodySpacing: 8,
                multiKeyBackground: fillColor[theme],
                padding: 8,
                caretSize: 8,
                cornerRadius: 4,
                bodyFont: {
                    weight: '500',
                },
                titleMarginBottom: 8,
            },
            datalabels: {
                formatter: (value, context) => {
                    if (visualValues?.source === ChartValueSourceType.LABEL) {
                        return context.chart.data.datasets[context.datasetIndex]
                            .label;
                    }
                    return value?.y;
                },
                display:
                    visualValues?.display === ChartValueDisplayType.TRUE
                        ? true
                        : visualValues?.display === ChartValueDisplayType.AUTO
                        ? 'auto'
                        : false,
                anchor: visualValues?.position,
                align: visualValues?.alignment,
            },
        },
        animation: {
            duration: 0,
        },

        elements: {
            point: {
                radius: 0,
                hitRadius: 3,
                hoverRadius: 3,
                hoverBorderWidth: 5,
            },
        },
    };

    // If auto size, then let aspect ratio be auto maintained, otherwise
    // fit the content to the height, so no need to maintain ratio
    const chartSize = visual.size ?? ChartSize.AUTO;
    if (chartSize !== ChartSize.AUTO) {
        optionsObj.maintainAspectRatio = false;
    }

    if (visual.connect_missing != null) {
        (optionsObj as LineControllerDatasetOptions).spanGaps =
            visual.connect_missing;
    }

    // Tooltip
    if (meta.chart.type === 'pie' || meta.chart.type === 'doughnut') {
        optionsObj.plugins.tooltip.callbacks = {
            label: (context) => {
                const label = context.dataset.label;
                const currentValue = context.parsed;
                const percentage = (
                    ((context.element as any).circumference * 100) /
                    (2 * Math.PI)
                ).toFixed(1);
                return `${label}: ${formatNumber(
                    currentValue
                )} (${percentage}%)`;
            },
            title: (titleContext) => titleContext[0].label,
        };
    } else {
        const invertAxis = meta.chart.type === 'histogram';
        optionsObj.plugins.tooltip.callbacks = {
            label: (context) => {
                const label = context.dataset.label ?? '';
                const value = invertAxis ? context.parsed.x : context.parsed.y;
                return ` ${label}: ${formatNumber(value)}`;
            },
            title: (titleContext): string => {
                if (meta.chart.y_axis.stack) {
                    let totalValue = 0;
                    for (const metricContext of titleContext) {
                        totalValue += Number(
                            invertAxis
                                ? metricContext.parsed.x
                                : metricContext.parsed.y
                        );
                    }
                    if (!isNaN(totalValue)) {
                        return (
                            String(titleContext[0].label) +
                            ' Total: ' +
                            formatNumber(totalValue)
                        );
                    }
                }
                return String(titleContext[0].label);
            },
        };

        let xAxesOptions = computeScaleOptions(
            xAxesScaleType,
            meta.chart.x_axis,
            theme,
            meta.chart.y_axis.stack,
            true
        );
        let yAxesOptions = computeScaleOptions(
            yAxesScaleType,
            meta.chart.y_axis,
            theme,
            meta.chart.y_axis.stack
        );

        if (invertAxis) {
            optionsObj.indexAxis = 'y';
            [xAxesOptions, yAxesOptions] = [yAxesOptions, xAxesOptions];
        }

        optionsObj.scales = {
            x: xAxesOptions,
            y: yAxesOptions,
        };
    }

    if (meta.chart.type === 'scatter') {
        optionsObj.elements.point.radius = 4;
    }

    return optionsObj;
}

function computeScaleOptions(
    scaleType: ChartScaleType,
    axisMeta: IChartAxisMeta,
    theme: string,
    stack: boolean,
    isXAxis = false
): ScaleOptions {
    // Known bug: if scale type change from log to time, the graph crash
    // I think it is a chart js issue
    const axis: ScaleOptions = {
        grid: {
            display: true,
            color: rgb(fontColor[theme].concat([0.25])),
        },
        title: {
            display: !!axisMeta.label?.length,
            text: axisMeta.label ?? '',
        },
        stacked: stack,
    };

    if (scaleType != null) {
        axis.type = chartScaleToChartJSScale[scaleType];
    }

    if (scaleType === 'time') {
        (axis as DeepPartial<TimeScaleOptions>).time = {
            tooltipFormat: 'll HH:mm',
            displayFormats: {
                day: 'MM/DD',
                hour: 'MM/DD hA',
                minute: 'h:mm a',
            },
        };
    } else if (scaleType === 'date') {
        (axis as DeepPartial<TimeScaleOptions>).time = {
            tooltipFormat: 'YYYY-MM-DD',
            displayFormats: {
                day: 'YYYY-MM-DD',
            },
            minUnit: 'day',
        };
    } else if (scaleType === 'linear' || scaleType === 'logarithmic') {
        // for empty case, it might be null or ""
        if (axisMeta.max != null && typeof axisMeta.max === 'number') {
            axis.max = axisMeta.max;
        }
        if (axisMeta.min != null && typeof axisMeta.min === 'number') {
            axis.min = axisMeta.min;
        } else if (!isXAxis) {
            // for yAxis, make sure 0 is shown unless specificed
            (axis as LinearScaleOptions).beginAtZero = true;
        }

        if (axisMeta.format === ChartScaleFormat.DOLLAR) {
            axis.ticks = { format: { style: 'currency', currency: 'USD' } };
        } else if (axisMeta.format === ChartScaleFormat.PERCENTAGE) {
            axis.ticks = { format: { style: 'percent' } };
        } else {
            // Prevent ticks from erroring out if there is no data provided
            // See https://github.com/chartjs/Chart.js/issues/8092
            axis.ticks = { callback: (val) => val };
        }
    }

    return axis;
}
