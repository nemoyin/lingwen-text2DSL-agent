import React from 'react';
import UserMessage from './UserMessage';
import AssistantMessage from './AssistantMessage';
import ThinkingIndicator from './ThinkingIndicator';
import ErrorMessage from './ErrorMessage';
import type { QueryResponse } from '../../types';

interface Message {
  type: 'user' | 'assistant';
  content: string;
  result?: QueryResponse;
  error?: string;
}

interface Props {
  messages: Message[];
  loading: boolean;
  error: string | null;
}

export default function MessageList({ messages, loading, error }: Props) {
  return (
    <>
      {messages.map((msg, idx) => {
        if (msg.type === 'user') {
          return <UserMessage key={idx} question={msg.content} />;
        }
        if (msg.error) {
          return <ErrorMessage key={idx} message={msg.error} />;
        }
        if (msg.result) {
          return <AssistantMessage key={idx} result={msg.result} />;
        }
        return null;
      })}
      {loading && <ThinkingIndicator />}
      {error && !loading && <ErrorMessage message={error} />}
    </>
  );
}
