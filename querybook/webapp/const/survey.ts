export interface ISurvey {
    id: number;
    created_at: number;
    updated_at: number;

    surface: SurveySurfaceType;
    surface_metadata: Record<string, any>;
    rating: number;
    comment: string;

    uid: number;
}

export interface ICreateSurveyFormData {
    surface: SurveySurfaceType;
    surface_metadata: Record<string, any>;
    rating: number;
    comment?: string | null;
}

export interface IUpdateSurveyFormData {
    rating?: number;
    comment?: string | null;
}

export enum SurveySurfaceType {
    TABLE_SEARCH = 'table_search',
    TABLE_TRUST = 'table_view',
    TEXT_TO_SQL = 'text_to_sql',
    QUERY_AUTHORING = 'query_authoring',
}

export const SurveyTypeToQuestion: Record<SurveySurfaceType, string> = {
    [SurveySurfaceType.TABLE_SEARCH]:
        'How effective was this search in finding the right table?',
    [SurveySurfaceType.TABLE_TRUST]:
        'How confident are you in the reliability of {table_name}?',
    [SurveySurfaceType.TEXT_TO_SQL]:
        'How useful was the AI Assistant in accomplishing your task?',
    [SurveySurfaceType.QUERY_AUTHORING]:
        'How would you describe your overall experience using Querybook?',
};
