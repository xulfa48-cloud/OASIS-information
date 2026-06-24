// Shared TypeScript types for services
export interface ID {
  id: string;
}

export interface PaperDTO {
  id: string;
  title: string;
  authors: string[];
  abstract?: string;
}
