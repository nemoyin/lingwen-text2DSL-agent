import React from 'react';
import { Box, Typography, Button } from '@mui/material';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box textAlign="center" py={6}>
          <Typography variant="h6" gutterBottom>
            页面出现异常
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {this.state.error?.message || '未知错误'}
          </Typography>
          <Button
            variant="outlined"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            重试
          </Button>
        </Box>
      );
    }
    return this.props.children;
  }
}
