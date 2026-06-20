import { useState, useEffect, useCallback } from 'react';
import { Box, Button, Grid2, Snackbar, Alert } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import SkillCard from '../../components/admin/SkillCard';
import SkillEditor from '../../components/admin/SkillEditor';
import * as skillService from '../../services/skillService';
import type { SkillTemplate, SkillCreate } from '../../types';

export default function SkillPage() {
  const [skills, setSkills] = useState<SkillTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<SkillTemplate | null>(null);
  const [snack, setSnack] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    try {
      const list = await skillService.getAll();
      setSkills(list);
    } catch {
      setSnack({ open: true, message: '加载失败', severity: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void fetchSkills(); }, [fetchSkills]);

  const handleSave = async (data: SkillCreate) => {
    if (editing) {
      await skillService.update(editing.id, data);
    } else {
      await skillService.create(data);
    }
    setEditing(null);
    await fetchSkills();
  };

  if (loading) return <LoadingSpinner />;

  return (
    <Box>
      <PageHeader
        title="Skill 模板"
        actions={
          <Button
            variant="contained"
            size="small"
            startIcon={<AddIcon />}
            onClick={() => { setEditing(null); setEditorOpen(true); }}
          >
            新建 Skill
          </Button>
        }
      />
      <Grid2 container spacing={2}>
        {skills.map((skill) => (
          <Grid2 size={{ xs: 12, sm: 6, md: 4 }} key={skill.id}>
            <SkillCard
              skill={skill}
              onEdit={(s) => { setEditing(s); setEditorOpen(true); }}
            />
          </Grid2>
        ))}
      </Grid2>

      <SkillEditor
        open={editorOpen}
        initial={editing}
        onClose={() => { setEditorOpen(false); setEditing(null); }}
        onSave={handleSave}
      />

      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack((s) => ({ ...s, open: false }))}>
        <Alert severity={snack.severity} onClose={() => setSnack((s) => ({ ...s, open: false }))}>{snack.message}</Alert>
      </Snackbar>
    </Box>
  );
}
