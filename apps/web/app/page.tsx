'use client';

import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm your AI Knowledge Navigator. I can help you search through your documents and answer questions based on your knowledge base. What would you like to know?",
      isUser: false,
      timestamp: new Date()
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: currentInput }),
      });

      let aiResponse = '';
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.sources && data.sources.length > 0) {
          // Check if we have grouped sources
          if (data.grouped_sources) {
            const totalDocs = data.sources.length;
            aiResponse = `I found ${totalDocs} relevant documents for your query, organized by category:\n\n`;
            
            // Display grouped sources
            Object.entries(data.grouped_sources).forEach(([category, group]: [string, any]) => {
              aiResponse += `## 📁 ${category} (${group.count} documents)\n\n`;
              group.documents.forEach((source: any, index: number) => {
                const linkText = source.url ? `[${source.title}](${source.url})` : source.title;
                aiResponse += `• **${linkText}**\n  ${source.snippet.substring(0, 150)}...\n\n`;
              });
            });
          } else {
            // Fallback to simple list if no grouping
            aiResponse = `I found ${data.sources.length} relevant documents for your query:\n\n`;
            data.sources.forEach((source: any, index: number) => {
              const linkText = source.url ? `[${source.title}](${source.url})` : source.title;
              aiResponse += `${index + 1}. **${linkText}**\n${source.snippet}...\n\n`;
            });
          }
        } else {
          aiResponse = "I couldn't find any relevant documents for your query. The knowledge base might be empty or your query doesn't match the available content.";
        }
      } else {
        aiResponse = "I encountered an error while searching. Please make sure the backend service is running.";
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: aiResponse,
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I'm sorry, I couldn't connect to the search service. Please check that the backend is running on http://localhost:8000",
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">IKB Navigator</h1>
            <p className="text-sm text-gray-600">AI-Powered Knowledge Assistant</p>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 max-w-2xl ${
              message.isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.isUser
                  ? 'bg-blue-500'
                  : 'bg-gradient-to-r from-purple-500 to-pink-500'
              }`}
            >
              {message.isUser ? (
                <div className="w-4 h-4 bg-white rounded-full" />
              ) : (
                <Sparkles className="w-4 h-4 text-white" />
              )}
            </div>
            
            <div
              className={`rounded-2xl px-4 py-3 shadow-sm ${
                message.isUser
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-900'
              }`}
            >
              <div className="whitespace-pre-wrap">
                {message.content.split('\n').map((line, index) => (
                  <div key={index}>
                    {line.includes('**') || line.includes('[') || line.startsWith('##') || line.startsWith('•') ? (
                      <div dangerouslySetInnerHTML={{
                        __html: line
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$1</a>')
                          .replace(/^## (.*)$/g, '<h3 class="text-lg font-semibold text-gray-800 mt-4 mb-2">$1</h3>')
                          .replace(/^• (.*)$/g, '<div class="ml-4 mb-1">• $1</div>')
                      }} />
                    ) : (
                      line
                    )}
                    {index < message.content.split('\n').length - 1 && <br />}
                  </div>
                ))}
              </div>
              <div className={`text-xs mt-2 opacity-70 ${
                message.isUser ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {message.timestamp.toLocaleTimeString('en-US', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </div>
            </div>
          </div>
        ))}

        {/* Loading */}
        {isLoading && (
          <div className="flex gap-3 max-w-2xl mr-auto">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}} />
                </div>
                <span className="text-gray-600 text-sm">Searching...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t bg-white p-4">
        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything about your knowledge base..."
              className="flex-1 px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 transition-all flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
