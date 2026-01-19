import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Function to clean markdown formatting
const cleanText = (text) => {
  if (!text) return text;
  
  // Remove markdown formatting
  let cleaned = text
    // Remove bold **text**
    .replace(/\*\*(.*?)\*\*/g, '$1')
    // Remove italic *text* or _text_
    .replace(/[_*](.*?)[_*]/g, '$1')
    // Remove code `text`
    .replace(/`(.*?)`/g, '$1')
    // Remove headers (# Header)
    .replace(/^#+\s+/gm, '')
    // Remove ``` code blocks
    .replace(/```[\s\S]*?```/g, '')
    // Clean up multiple newlines
    .replace(/\n\s*\n\s*\n/g, '\n\n')
    .trim();
  
  return cleaned;
};

function App() {
  const [messages, setMessages] = useState([
    { id: 1, text: 'Hello! Ask me anything.', sender: 'bot', time: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    const currentTime = new Date();
    
    // Add user message
    setMessages(prev => [...prev, { 
      id: Date.now(),
      text: userMessage, 
      sender: 'user', 
      time: currentTime 
    }]);
    
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:8000/chat', {
        message: userMessage
      });

      // Clean the response text
      const cleanedResponse = cleanText(response.data.reply);

      // Add bot response
      setMessages(prev => [...prev, { 
        id: Date.now() + 1,
        text: cleanedResponse, 
        sender: 'bot', 
        time: new Date() 
      }]);

    } catch (error) {
      const errorMessage = cleanText('Error: Could not connect to server');
      setMessages(prev => [...prev, { 
        id: Date.now() + 1,
        text: errorMessage, 
        sender: 'bot', 
        time: new Date() 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([{ 
      id: 1, 
      text: 'Chat cleared. Ask me something!', 
      sender: 'bot', 
      time: new Date() 
    }]);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <h1>🤖 AI Chatbot</h1>
        <button onClick={clearChat} className="clear-btn">
          Clear Chat
        </button>
      </div>

      {/* Chat Messages */}
      <div className="chat-box">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.sender}`}>
            <div className="message-header">
              <span className="sender">{msg.sender === 'user' ? 'You' : 'AI'}</span>
              <span className="time">{formatTime(msg.time)}</span>
            </div>
            <div className="message-text">{msg.text}</div>
          </div>
        ))}
        
        {loading && (
          <div className="message bot">
            <div className="message-header">
              <span className="sender">AI</span>
              <span className="time">{formatTime(new Date())}</span>
            </div>
            <div className="typing">
              <span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={loading}
          className="message-input"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="send-btn"
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>

      {/* Footer */}
      <div className="footer">
        <span>Messages: {messages.length}</span>
        <span>AI with memory</span>
      </div>
    </div>
  );
}

export default App;