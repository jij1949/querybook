import ds from 'lib/datasource';

export interface IPersonalizedSummaryDashboard {
    totalCostEstimate?: number;
    dagCostEstimate?: number;
    trinoCostEstimate?: number;
    numberDataDocs?: number;
    numberDags?: number;
    numberExtracts?: number;
    numberTeradataQueries?: number;
    numberTrinoQueries?: number;
}

export const ExpediaResource = {
    getPersonalizedCost: (username?: string) =>
        ds.fetch<IPersonalizedSummaryDashboard>(
            '/expedia/personalized-cost/',
            username ? { username } : {}
        ),
};
