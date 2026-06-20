/** Skill template types — mirror backend app/schemas/skill.py */

export interface SkillTemplate {
  id: number;
  name: string;
  description: string | null;
  prompt_template: string;
  is_active: boolean;
  created_at: string;
}

export interface SkillCreate {
  name: string;
  description?: string;
  prompt_template: string;
}

export type SkillUpdate = Partial<SkillCreate> & {
  is_active?: boolean;
};
