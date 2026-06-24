export interface Paper {
  id: string;
  external_id?: string;
  title: string;
  authors: string[];
  abstract?: string;
  published_at?: string;
  embedding?: number[];
}
