import { useState } from 'react';
import { IconButton, Tooltip, Box, Typography } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import SettingsVoiceIcon from '@mui/icons-material/SettingsVoice';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import StopIcon from '@mui/icons-material/Stop';

interface Props {
  onResult: (text: string) => void;
}

export function VoiceInput({ onResult }: Props) {
  const [listening, setListening] = useState(false);

  const startListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('您的浏览器不支持语音输入，请使用 Chrome 浏览器');
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = (e: any) => {
      const text = e.results[0][0].transcript;
      onResult(text);
      setListening(false);
    };
    recognition.onerror = (e: any) => {
      console.warn('Speech error:', e.error);
      setListening(false);
    };
    recognition.onend = () => setListening(false);
    setListening(true);
    recognition.start();
  };

  return (
    <Tooltip title={listening ? '正在聆听...' : '点击开始语音输入'}>
      <IconButton
        onClick={startListening}
        color={listening ? 'error' : 'default'}
        sx={{
          animation: listening ? 'pulse 1.5s infinite' : 'none',
          '@keyframes pulse': { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0.5 } },
        }}
      >
        {listening ? (
          <Box sx={{ position: 'relative' }}>
            <SettingsVoiceIcon fontSize="small" />
            <Box sx={{ position: 'absolute', top: -4, right: -4, width: 8, height: 8, borderRadius: '50%', bgcolor: 'error.main' }} />
          </Box>
        ) : (
          <MicIcon fontSize="small" />
        )}
      </IconButton>
    </Tooltip>
  );
}

export function SpeakButton({ text }: { text: string }) {
  const [speaking, setSpeaking] = useState(false);

  const handleToggle = () => {
    if (speaking) {
      speechSynthesis.cancel();
      setSpeaking(false);
    } else {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'zh-CN';
      u.rate = 1.0;
      u.onend = () => setSpeaking(false);
      u.onerror = () => setSpeaking(false);
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
      setSpeaking(true);
    }
  };

  return (
    <Tooltip title={speaking ? '停止朗读' : '朗读回答'}>
      <IconButton size="small" onClick={handleToggle} color={speaking ? 'primary' : 'default'}>
        {speaking ? <StopIcon fontSize="small" /> : <VolumeUpIcon fontSize="small" />}
      </IconButton>
    </Tooltip>
  );
}
