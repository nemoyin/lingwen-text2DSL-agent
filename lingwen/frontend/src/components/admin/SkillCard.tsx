import { Card, CardContent, Typography, Chip, IconButton, Box } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import type { SkillTemplate } from '../../types';

interface Props {
  skill: SkillTemplate;
  onEdit: (skill: SkillTemplate) => void;
}

export default function SkillCard({ skill, onEdit }: Props) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Typography variant="subtitle1" fontWeight={500}>
            {skill.name}
          </Typography>
          <Box display="flex" gap={0.5} alignItems="center">
            <Chip
              size="small"
              label={skill.is_active ? '激活' : '未激活'}
              color={skill.is_active ? 'success' : 'default'}
              variant="outlined"
            />
            <IconButton size="small" onClick={() => onEdit(skill)}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>
        {skill.description && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {skill.description}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
