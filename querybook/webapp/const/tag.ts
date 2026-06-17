export interface ITagMeta {
    type?: string;
    admin?: boolean;
    color?: string;
    icon?: string;
    tooltip?: string;
    rank?: number;
    hidden?: boolean;
    catalog_type?: string;
}
export interface ITag {
    id: number;
    name: string;
    created_at: number;
    updated_at: number;
    meta?: ITagMeta;
}
