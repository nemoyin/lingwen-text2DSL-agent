/** Few-shot example types — mirror backend app/schemas/few_shot.py */

export interface FewShotExample {
  id: number;
  datasource_id: number;
  question: string;
  sql: string;
  description: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export interface FewShotCreate {
  datasource_id: number;
  question: string;
  sql: string;
  description?: string;
  tags?: string;
}

export type FewShotUpdate = Partial<FewShotCreate>;
