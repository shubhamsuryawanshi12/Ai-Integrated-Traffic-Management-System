import React, { useState, useRef, useEffect } from 'react';

const API_URL = 'http://localhost:8000/api/v1/chatbot';

function Chatbot() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hi! I\'m the UrbanFlow AI Assistant. Ask me about traffic data, signal coordination, or system status. 🚦' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const sessionId = useRef(`session_${Date.now()}`);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    const sendMessage = async () => {
        const text = input.trim();
        if (!text || loading) return;

        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: text }]);
        setLoading(true);

        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_id: sessionId.current }),
            });
            const data = await res.json();

            if (data.error) {
                setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${data.error}` }]);
            } else {
                setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
            }
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Failed to connect to AI. Is the backend running?' }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const clearChat = () => {
        setMessages([{ role: 'assistant', content: 'Chat cleared! Ask me anything about UrbanFlow. 🚦' }]);
        fetch(`${API_URL}/history?session_id=${sessionId.current}`, { method: 'DELETE' }).catch(() => { });
    };

    // Quick suggestion buttons
    const suggestions = [
        "What's the current traffic status?",
        "How does the AI coordinate signals?",
        "Show me queue length analysis",
        "Explain the reward function",
    ];

    return (
        <>
            {/* Floating Chat Bubble */}
            <button
                id="chatbot-toggle"
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    position: 'fixed',
                    bottom: '24px',
                    right: '24px',
                    width: '60px',
                    height: '60px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '28px',
                    boxShadow: '0 4px 20px rgba(59, 130, 246, 0.5)',
                    zIndex: 9999,
                    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                    transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)',
                }}
                onMouseEnter={(e) => e.target.style.transform = isOpen ? 'rotate(90deg) scale(1.1)' : 'scale(1.1)'}
                onMouseLeave={(e) => e.target.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)'}
            >
                {isOpen ? '✕' : '💬'}
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div style={{
                    position: 'fixed',
                    bottom: '96px',
                    right: '24px',
                    width: '400px',
                    maxWidth: 'calc(100vw - 48px)',
                    height: '550px',
                    maxHeight: 'calc(100vh - 120px)',
                    backgroundColor: '#0f172a',
                    borderRadius: '16px',
                    border: '1px solid #334155',
                    boxShadow: '0 8px 40px rgba(0,0,0,0.5)',
                    display: 'flex',
                    flexDirection: 'column',
                    zIndex: 9998,
                    overflow: 'hidden',
                    animation: 'slideUp 0.3s ease-out',
                }}>
                    {/* Header */}
                    <div style={{
                        background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                        padding: '16px 20px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ fontSize: '24px' }}>🤖</span>
                            <div>
                                <div style={{ color: '#fff', fontWeight: 'bold', fontSize: '16px' }}>
                                    UrbanFlow AI
                                </div>
                                <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>
                                    Powered by Gemma 3
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={clearChat}
                            style={{
                                background: 'rgba(255,255,255,0.2)',
                                border: 'none',
                                color: '#fff',
                                padding: '6px 12px',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontSize: '12px',
                            }}
                        >
                            🗑️ Clear
                        </button>
                    </div>

                    {/* Messages */}
                    <div style={{
                        flex: 1,
                        overflowY: 'auto',
                        padding: '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px',
                    }}>
                        {messages.map((msg, idx) => (
                            <div key={idx} style={{
                                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                maxWidth: '85%',
                            }}>
                                <div style={{
                                    backgroundColor: msg.role === 'user' ? '#3b82f6' : '#1e293b',
                                    color: '#fff',
                                    padding: '10px 14px',
                                    borderRadius: msg.role === 'user'
                                        ? '14px 14px 4px 14px'
                                        : '14px 14px 14px 4px',
                                    fontSize: '14px',
                                    lineHeight: '1.5',
                                    border: msg.role === 'user' ? 'none' : '1px solid #334155',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word',
                                }}>
                                    {msg.content}
                                </div>
                            </div>
                        ))}

                        {loading && (
                            <div style={{ alignSelf: 'flex-start', maxWidth: '85%' }}>
                                <div style={{
                                    backgroundColor: '#1e293b',
                                    color: '#94a3b8',
                                    padding: '10px 14px',
                                    borderRadius: '14px 14px 14px 4px',
                                    fontSize: '14px',
                                    border: '1px solid #334155',
                                    display: 'flex',
                                    gap: '4px',
                                }}>
                                    <span className="dot-pulse">●</span>
                                    <span className="dot-pulse" style={{ animationDelay: '0.2s' }}>●</span>
                                    <span className="dot-pulse" style={{ animationDelay: '0.4s' }}>●</span>
                                </div>
                            </div>
                        )}

                        {/* Quick suggestions (only show when few messages) */}
                        {messages.length <= 1 && !loading && (
                            <div style={{
                                display: 'flex',
                                flexWrap: 'wrap',
                                gap: '8px',
                                marginTop: '8px',
                            }}>
                                {suggestions.map((s, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => { setInput(s); }}
                                        style={{
                                            background: 'rgba(59, 130, 246, 0.1)',
                                            border: '1px solid #334155',
                                            color: '#94a3b8',
                                            padding: '6px 12px',
                                            borderRadius: '20px',
                                            cursor: 'pointer',
                                            fontSize: '12px',
                                            transition: 'all 0.2s',
                                        }}
                                        onMouseEnter={(e) => {
                                            e.target.style.borderColor = '#3b82f6';
                                            e.target.style.color = '#3b82f6';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.target.style.borderColor = '#334155';
                                            e.target.style.color = '#94a3b8';
                                        }}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input */}
                    <div style={{
                        padding: '12px 16px',
                        borderTop: '1px solid #334155',
                        display: 'flex',
                        gap: '8px',
                        backgroundColor: '#0f172a',
                    }}>
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about traffic data..."
                            disabled={loading}
                            style={{
                                flex: 1,
                                backgroundColor: '#1e293b',
                                border: '1px solid #334155',
                                borderRadius: '10px',
                                padding: '10px 14px',
                                color: '#fff',
                                fontSize: '14px',
                                outline: 'none',
                            }}
                        />
                        <button
                            onClick={sendMessage}
                            disabled={loading || !input.trim()}
                            style={{
                                background: loading || !input.trim() ? '#334155' : 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                                border: 'none',
                                borderRadius: '10px',
                                padding: '10px 16px',
                                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                                color: '#fff',
                                fontSize: '16px',
                                transition: 'all 0.2s',
                            }}
                        >
                            ▶
                        </button>
                    </div>
                </div>
            )}

            {/* CSS Animations */}
            <style>{`
                @keyframes slideUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                @keyframes dotPulse {
                    0%, 80%, 100% { opacity: 0.3; }
                    40% { opacity: 1; }
                }
                .dot-pulse {
                    animation: dotPulse 1.4s infinite;
                }
            `}</style>
        </>
    );
}

export default Chatbot;
