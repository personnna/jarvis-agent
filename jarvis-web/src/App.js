import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';
import Dashboard from './Dashboard';

const SERVER_URL = 'wss://jarvis-ai.xyz/ws';
const HTTP_URL = 'https://jarvis-ai.xyz';

function ArcReactor({ isListening, isProcessing, isConnected }) {
  return (
    <div className={`arc-reactor ${isListening ? 'listening' : ''} ${isProcessing ? 'processing' : ''}`}>
      <div className="arc-outer">
        <div className="arc-mid">
          <div className="arc-inner">
            <div className={`arc-core ${isConnected ? 'online' : 'offline'}`} />
          </div>
        </div>
      </div>
      {[...Array(8)].map((_, i) => (
        <div key={i} className="arc-ray" style={{ transform: `rotate(${i * 45}deg)` }} />
      ))}
    </div>
  );
}

function MicIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="2" width="6" height="11" rx="3"/>
      <path d="M5 10a7 7 0 0 0 14 0"/>
      <line x1="12" y1="19" x2="12" y2="22"/>
      <line x1="9" y1="22" x2="15" y2="22"/>
    </svg>
  );
}

function WaveIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <path d="M2 12h2M6 8v8M10 5v14M14 8v8M18 6v12M22 12h-2"/>
    </svg>
  );
}

function AgentBadge({ intent }) {
  const agents = {
    create_jira_ticket: { label: 'Jira', color: '#0052CC' },
    list_jira_tickets: { label: 'Jira', color: '#0052CC' },
    read_emails: { label: 'Gmail', color: '#EA4335' },
    send_email: { label: 'Gmail', color: '#EA4335' },
    meeting_summary: { label: 'Meeting', color: '#F59E0B' },
    research: { label: 'Research', color: '#8B5CF6' },
    get_calendar: { label: 'Calendar', color: '#0F9D58' },
    create_calendar_event: { label: 'Calendar', color: '#0F9D58' },
    general_chat: { label: 'JARVIS', color: '#4A9EE0' },
  };
  const agent = agents[intent];
  if (!agent) return null;
  return (
    <span className="agent-badge" style={{ background: agent.color + '22', color: agent.color, border: `1px solid ${agent.color}44` }}>
      {agent.label}
    </span>
  );
}

function MessageBubble({ message }) {
  return (
    <div className={`message ${message.isUser ? 'user' : 'jarvis'}`}>
      {!message.isUser && (
        <div className="message-meta">
          <span className="sender">JARVIS</span>
          {message.isProactive && <span className="proactive-badge">🔔 Alert</span>}
          {message.intent && !message.isProactive && <AgentBadge intent={message.intent} />}
        </div>
      )}
      <div className={`bubble ${message.isUser ? 'bubble-user' : 'bubble-jarvis'} ${message.isProactive ? 'bubble-proactive' : ''}`}>
        {message.isUser ? message.text : <ReactMarkdown>{message.text}</ReactMarkdown>}
      </div>
    </div>
  );
}

function AgentSteps({ steps }) {
  if (!steps.length) return null;
  return (
    <div className="message jarvis">
      <div className="message-meta">
        <span className="sender">JARVIS</span>
        <span className="agent-badge" style={{background:'rgba(245,158,11,0.1)',color:'#F59E0B',border:'1px solid rgba(245,158,11,0.2)'}}>
          ⟳ Planning
        </span>
      </div>
      <div className="bubble bubble-jarvis" style={{padding:'10px 14px'}}>
        {steps.map((s, i) => (
          <div key={i} style={{display:'flex',gap:8,marginBottom:6,alignItems:'center',opacity: i === steps.length-1 ? 1 : 0.5}}>
            <span style={{fontSize:10,color:'#4A9EE0',minWidth:160,fontFamily:'monospace'}}>{s.agent}</span>
            <span style={{fontSize:11,color:'#778899'}}>{s.step}</span>
            {i === steps.length-1 && <span style={{marginLeft:'auto',fontSize:10,color:'#F59E0B'}}>⟳</span>}
            {i < steps.length-1 && <span style={{marginLeft:'auto',fontSize:10,color:'#22c55e'}}>✓</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    { id: 1, text: "JARVIS online. How can I help?", isUser: false, intent: 'general_chat' }
  ]);
  const [currentSteps, setCurrentSteps] = useState([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    connectWebSocket();
    fetch(`${HTTP_URL}/mode`)
      .then(r => r.json())
      .then(d => setIsDemoMode(d.mode === 'demo'))
      .catch(() => {});
    
    return () => {
      // закрываем соединение при размонтировании
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const connectWebSocket = () => {
    const ws = new WebSocket(SERVER_URL);
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      setTimeout(connectWebSocket, 3000);
    };
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'step') {
        setCurrentSteps(prev => [...prev, { agent: data.agent, step: data.step }]);
        return;
      }
      if (data.type === 'proactive') {
        setMessages(prev => [...prev, {
          id: Date.now(), text: data.message, isUser: false,
          intent: data.intent, isProactive: true
        }]);
        speak(data.message);
        return;
      }
      if (data.type !== 'connected') {
        setCurrentSteps([]);
        setMessages(prev => [...prev, {
          id: Date.now(), text: data.message, isUser: false, intent: data.intent
        }]);
        speak(data.message);
      }
      setIsProcessing(false);
    };
    wsRef.current = ws;
  };

  const toggleMode = async () => {
    const newMode = isDemoMode ? 'live' : 'demo';
    await fetch(`${HTTP_URL}/mode/${newMode}`, { method: 'POST' });
    setIsDemoMode(!isDemoMode);
    setMessages([{
      id: Date.now(),
      text: `Switched to ${newMode.toUpperCase()} mode.`,
      isUser: false,
      intent: 'general_chat'
    }]);
  };

const speak = (text) => {
  // некоторые браузеры требуют user gesture
  const synth = window.speechSynthesis;
  synth.cancel();
  const clean = text.replace(/[*#`_]/g, '').slice(0, 400);
  
  // разбиваем на части по 200 символов
  const chunks = [];
  for (let i = 0; i < clean.length; i += 200) {
    chunks.push(clean.slice(i, i + 200));
  }
  
  chunks.forEach((chunk, i) => {
    const utterance = new SpeechSynthesisUtterance(chunk);
    utterance.lang = 'en-GB';
    utterance.rate = 0.9;
    utterance.pitch = 0.8;
    const voices = synth.getVoices();
    const british = voices.find(v => v.lang === 'en-GB');
    if (british) utterance.voice = british;
    synth.speak(utterance);
  });
};

  const sendText = () => {
    if (!input.trim() || !wsRef.current) return;
    const text = input;
    setMessages(prev => [...prev, { id: Date.now(), text, isUser: true }]);
    setInput('');
    setIsProcessing(true);
    wsRef.current.send(JSON.stringify({ text }));
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
        await sendVoice(blob);
        stream.getTracks().forEach(t => t.stop());
      };
      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (e) {
      console.error('Mic error:', e);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    setIsProcessing(true);
  };

  const sendVoice = async (blob) => {
    const formData = new FormData();
    formData.append('file', blob, 'audio.wav');
    try {
      const res = await fetch(`${HTTP_URL}/voice`, { method: 'POST', body: formData });
      const data = await res.json();
      if (data.transcript) {
        setMessages(prev => [...prev, { id: Date.now(), text: data.transcript, isUser: true }]);
      }
      if (data.response) {
        setMessages(prev => [...prev, { id: Date.now(), text: data.response, isUser: false, intent: data.intent }]);
        speak(data.response);
      }
    } catch (e) {
      console.error('Voice error:', e);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <>
      {showDashboard ? (
        <Dashboard onBack={() => setShowDashboard(false)} />
      ) : (
    <div className="app">
      <div className="header">
        <div className="header-left">
          <h1 className="title">JARVIS</h1>
          <p className="subtitle">Just A Rather Very Intelligent System</p>
        </div>
        <div className="header-right">
          <button onClick={toggleMode} className={`mode-btn ${isDemoMode ? 'demo' : 'live'}`}>
            {isDemoMode ? '🎭 Demo' : '🔴 Live'}
          </button>
          <button onClick={() => setShowDashboard(true)} className="mode-btn" style={{borderColor:'rgba(74,158,224,0.3)', color:'#4A9EE0', background:'rgba(74,158,224,0.08)'}}>
            📊 Dashboard
          </button>
          <ArcReactor isListening={isRecording} isProcessing={isProcessing} isConnected={isConnected} />
        </div>
      </div>

      <div className="messages">
        {messages.map(msg => <MessageBubble key={msg.id} message={msg} />)}
        <AgentSteps steps={currentSteps} />
        {isProcessing && (
          <div className="message jarvis">
            <div className="message-meta">
              <span className="sender">JARVIS</span>
            </div>
            <div className="bubble bubble-jarvis processing">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <div className="status-text">
          {isRecording ? '● Recording' : isProcessing ? '⚡ Processing' : 'Hold to speak or type'}
        </div>
        <button
          className={`mic-btn ${isRecording ? 'recording' : ''}`}
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onTouchStart={(e) => { e.preventDefault(); startRecording(); }}
          onTouchEnd={(e) => { e.preventDefault(); stopRecording(); }}
        >
          {isRecording ? <WaveIcon /> : <MicIcon />}
        </button>
        <div className="text-input-row">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendText()}
            placeholder="Type a command..."
            className="text-input"
          />
          <button onClick={sendText} disabled={!input.trim()} className="send-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="12" y1="19" x2="12" y2="5"/>
              <polyline points="5 12 12 5 19 12"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
    )}
    </>
  );
}
