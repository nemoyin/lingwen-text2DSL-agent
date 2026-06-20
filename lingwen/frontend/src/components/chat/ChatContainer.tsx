import React from 'react';

interface Props {
  children: React.ReactNode;
}

export default function ChatContainer({ children }: Props) {
  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '16px 0' }}>
      {children}
    </div>
  );
}
