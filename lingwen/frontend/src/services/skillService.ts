/** Skill template API service. */

import api from './api';
import type {
  ApiResponse,
  SkillCreate,
  SkillTemplate,
  SkillUpdate,
} from '../types';

export async function getAll(): Promise<SkillTemplate[]> {
  const resp = await api.get<ApiResponse<SkillTemplate[]>>('/api/skills/');
  return resp.data.data!;
}

export async function getOne(id: number): Promise<SkillTemplate> {
  const resp = await api.get<ApiResponse<SkillTemplate>>(`/api/skills/${id}`);
  return resp.data.data!;
}

export async function create(data: SkillCreate): Promise<SkillTemplate> {
  const resp = await api.post<ApiResponse<SkillTemplate>>('/api/skills/', data);
  return resp.data.data!;
}

export async function update(
  id: number,
  data: SkillUpdate,
): Promise<SkillTemplate> {
  const resp = await api.put<ApiResponse<SkillTemplate>>(
    `/api/skills/${id}`,
    data,
  );
  return resp.data.data!;
}

export async function remove(id: number): Promise<void> {
  await api.delete(`/api/skills/${id}`);
}
