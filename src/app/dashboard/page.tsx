'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/button';
import {
  MessageSquare,
  Plus,
  Settings,
  Upload,
  Send,
  Paperclip,
  ChevronLeft,
  FileText,
  Moon,
  Sun,
  X,
  Menu,
  Sparkles,
  LogOut,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useTheme } from '@/components/theme-provider';
import { auth } from '@/lib/firebase';
import { signOut } from 'firebase/auth';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

// Normalize backend URL to avoid accidental double-slashes (env may include trailing '/').
const baseURL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/+$/g, '');

type MessageSource = {
  text: string;
  page: number;
};

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: MessageSource[];
  timestamp: Date;
};

type Chat = {
  id: string;
  title: string;
  messages: Message[];
  document?: string;
  docId?: string;
};

export default function DashboardPage() {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [chats, setChats] = useState<Chat[]>([
    {
      id: '1',
      title: 'Company Policy Q&A',
      document: 'company-policy.pdf',
      messages: [
        {
          id: '1',
          role: 'user',
          content: 'What is the vacation policy?',
          timestamp: new Date(),
        },
        {
          id: '2',
          role: 'assistant',
          content:
            'According to the company policy document, employees are entitled to 15 days of paid vacation per year. Vacation days must be requested at least 2 weeks in advance and are subject to manager approval.',
          sources: [{ text: 'Section 3.2', page: 12 }],
          timestamp: new Date(),
        },
      ],
    },
  ]);
  const [activeChat, setActiveChat] = useState<string>(chats[0]?.id || '');
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const currentChat = chats.find((chat) => chat.id === activeChat);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentChat?.messages]);

  const [selectedModel, setSelectedModel] = useState<'gpt' | 'llama'>('gpt');
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      setCurrentUser(user);
      if (user) {
        fetchCurrentModel(user);
      } else {
        router.replace('/login');
      }
      setCheckingAuth(false);
    });
    return () => unsubscribe();
  }, [router]);

  const fetchCurrentModel = async (user: any) => {
    try {
      const token = await user.getIdToken();
      const res = await fetch(`${baseURL}/current-model`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedModel(data.model);
      }
    } catch (err) {
      console.error('Failed to fetch current model:', err);
    }
  };

  const handleModelChange = async (model: 'gpt' | 'llama') => {
    if (!currentUser) {
      toast.error('You must be signed in to change models');
      return;
    }
    
    // Optimistic UI update
    const previousModel = selectedModel;
    setSelectedModel(model);

    try {
      const token = await currentUser.getIdToken();
      const res = await fetch(`${baseURL}/set-model`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ model })
      });
      
      if (res.ok) {
        toast.success(`Switched to ${model.toUpperCase()}`);
      } else {
        throw new Error('Server returned an error');
      }
    } catch (err) {
      // Revert on failure
      setSelectedModel(previousModel);
      toast.error('Failed to update model on server');
      console.error(err);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !currentChat || !currentUser) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setChats((prev) =>
      prev.map((chat) =>
        chat.id === activeChat
          ? { ...chat, messages: [...chat.messages, newMessage] }
          : chat
      )
    );

    setInputMessage('');
    setIsTyping(true);

    try {
      const token = await currentUser.getIdToken();
      const res = await fetch(`${baseURL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ 
          query: inputMessage,
          session_id: activeChat,
          doc_id: currentChat.docId
        })
      });

      if (res.ok) {
        const data = await res.json();
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.answer,
          sources: data.sources.map((s: any) => ({
             text: s.text,
             page: s.page
          })),
          timestamp: new Date(),
        };

        setChats((prev) =>
          prev.map((chat) =>
            chat.id === activeChat
              ? { ...chat, messages: [...chat.messages, aiResponse] }
              : chat
          )
        );
      } else {
        toast.error('Failed to get response');
      }
    } catch (err) {
      toast.error('Connection error');
      console.error(err);
    } finally {
      setIsTyping(false);
    }
  };


  const handleNewChat = () => {
    const newChat: Chat = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
    };
    setChats((prev) => [newChat, ...prev]);
    setActiveChat(newChat.id);
  };

  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !currentUser) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = await currentUser.getIdToken();
      const res = await fetch(`${baseURL}/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(`'${file.name}' processed successfully`);
        setShowUploadModal(false);
        
        if (currentChat) {
          setChats((prev) =>
            prev.map((chat) =>
              chat.id === activeChat
                ? { ...chat, document: file.name, title: file.name, docId: data.doc_id }
                : chat
            )
          );
        }
      } else {
        const errorData = await res.json();
        toast.error(errorData.detail || 'Upload failed');
      }
    } catch (err) {
      toast.error('Network error while uploading');
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleLogout = async () => {
    if (isLoggingOut) return;

    setIsLoggingOut(true);
    try {
      await signOut(auth);
      toast.success('Logged out successfully');
      router.push('/login');
    } catch (err) {
      toast.error('Failed to log out. Please try again.');
      console.error(err);
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    checkingAuth ? null : (
    <div className="h-screen flex bg-background overflow-hidden">
      {/* Sidebar */}
      <AnimatePresence>
        {!sidebarCollapsed && (
          <>
            {/* Mobile Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarCollapsed(true)}
              className="fixed inset-0 bg-background/80 z-30 lg:hidden"
            />
            
            {/* Sidebar */}
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="fixed lg:relative z-40 w-[280px] h-full border-r border-border bg-sidebar flex flex-col"
            >
              <div className="p-6 border-b border-border">
                <div className="flex items-center justify-between gap-2 mb-4">
                  <span className="text-lg font-medium tracking-tight">
                    Viora
                  </span>
                  <button
                    onClick={() => setSidebarCollapsed(true)}
                    className="lg:hidden p-1.5 hover:bg-accent rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <Button className="w-full" onClick={handleNewChat}>
                  <Plus className="w-4 h-4" />
                  New Chat
                </Button>
              </div>

              {/* Chat History */}
              <div className="flex-1 overflow-y-auto p-3 space-y-1">
                {chats.map((chat) => (
                  <button
                    key={chat.id}
                    onClick={() => {
                      setActiveChat(chat.id);
                      if (window.innerWidth < 1024) {
                        setSidebarCollapsed(true);
                      }
                    }}
                    className={cn(
                      'w-full text-left p-3 rounded-lg transition-colors',
                      'hover:bg-accent',
                      activeChat === chat.id && 'bg-accent'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <MessageSquare className="w-4 h-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                      <div className="flex-1 min-w-0">
                        <p className="truncate text-sm">{chat.title}</p>
                        {chat.document && (
                          <p className="text-xs text-muted-foreground truncate mt-1">
                            {chat.document}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Settings */}
              <div className="p-3">
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-accent transition-colors">
                  <Settings className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Settings</span>
                </button>
                <button
                  onClick={handleLogout}
                  disabled={isLoggingOut}
                  className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <LogOut className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">{isLoggingOut ? 'Logging out...' : 'Logout'}</span>
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="border-b border-border bg-background px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 min-w-0 flex-1">
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              {sidebarCollapsed ? (
                <Menu className="w-4 h-4" />
              ) : (
                <ChevronLeft className="w-4 h-4 hidden lg:block" />
              )}
            </button>

            <div className="flex items-center gap-3 min-w-0 flex-1">
              {currentChat?.document && (
                <>
                  <div className="w-8 h-8 rounded-lg bg-card border border-border flex items-center justify-center flex-shrink-0">
                    <FileText className="w-4 h-4 text-primary" />
                  </div>
                  <span className="text-sm font-medium truncate">{currentChat.document}</span>
                </>
              )}
              {!currentChat?.document && (
                <span className="text-sm text-muted-foreground truncate">No document uploaded</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowUploadModal(true)}
              className="hidden sm:flex"
            >
              <Upload className="w-4 h-4" />
            </Button>
            <button
              onClick={() => setShowUploadModal(true)}
              className="sm:hidden p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <Upload className="w-4 h-4" />
            </button>
            <button
              onClick={toggleTheme}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>
            <div className="w-8 h-8 rounded-full bg-card border border-border flex items-center justify-center text-xs font-medium">
              U
            </div>
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl mx-auto mb-6 flex justify-center">
            <div className="flex items-center gap-1 p-1 bg-muted rounded-xl border border-border">
              <button
                onClick={() => handleModelChange('gpt')}
                className={cn(
                  'px-4 py-1.5 text-xs font-medium rounded-lg transition-all',
                  selectedModel === 'gpt'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                GPT-4o
              </button>
              <button
                onClick={() => handleModelChange('llama')}
                className={cn(
                  'px-4 py-1.5 text-xs font-medium rounded-lg transition-all',
                  selectedModel === 'llama'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                Llama 3
              </button>
            </div>
          </div>

          {currentChat && currentChat.messages.length === 0 && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-md px-4">
                <div className="w-14 h-14 mx-auto mb-6 rounded-xl bg-card border border-border flex items-center justify-center">
                  <Sparkles className="w-7 h-7 text-primary" />
                </div>
                <h3 className="text-xl font-medium mb-2">Start a conversation</h3>
                <p className="text-sm text-muted-foreground mb-6">
                  Upload a document and ask questions to unlock AI-powered insights.
                </p>
                <Button onClick={() => setShowUploadModal(true)}>
                  <Upload className="w-4 h-4" />
                  Upload Document
                </Button>
              </div>
            </div>
          )}

          {currentChat && currentChat.messages.length > 0 && (
            <div className="max-w-3xl mx-auto space-y-6">
              <AnimatePresence>
                {currentChat.messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className={cn(
                      'flex gap-4',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {message.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 text-xs font-medium text-primary-foreground">
                        AI
                      </div>
                    )}

                    <div
                      className={cn(
                        'max-w-[80%] rounded-xl px-4 py-3',
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-card border border-border'
                      )}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                        {message.content}
                      </p>

                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-border">
                          <p className="text-[10px] font-bold mb-2 text-muted-foreground uppercase tracking-widest">
                            Sources:
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {message.sources.map((source, idx) => (
                              <div
                                key={idx}
                                className="px-2 py-1.5 rounded-lg bg-accent/30 border border-border text-[10px] text-muted-foreground flex items-center justify-center font-semibold"
                              >
                                <span className="text-foreground">Page {source.page}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {message.role === 'user' && (
                      <div className="w-8 h-8 rounded-full bg-card border border-border flex items-center justify-center flex-shrink-0 text-xs font-medium">
                        U
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>

              {isTyping && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-4"
                >
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-xs font-medium text-primary-foreground">
                    AI
                  </div>
                  <div className="bg-card border border-border rounded-xl px-4 py-3">
                    <div className="flex gap-1">
                      <motion.div
                        className="w-1.5 h-1.5 rounded-full bg-muted-foreground"
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                      />
                      <motion.div
                        className="w-1.5 h-1.5 rounded-full bg-muted-foreground"
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                      />
                      <motion.div
                        className="w-1.5 h-1.5 rounded-full bg-muted-foreground"
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                      />
                    </div>
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-background p-6">
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-3 items-center px-4 py-3 border rounded-xl bg-card">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-1.5 hover:bg-accent rounded-lg transition-colors flex-shrink-0"
              >
                <Paperclip className="w-4 h-4 text-muted-foreground" />
              </button>

              <input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Ask anything about your document..."
                className="flex-1 text-sm bg-transparent border-0 outline-none placeholder:text-muted-foreground"
              />
              
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isTyping}
                className="p-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex-shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-muted-foreground text-center mt-3">
              Viora AI can make mistakes. Verify important information.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <AnimatePresence>
        {showUploadModal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowUploadModal(false)}
              className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="fixed inset-0 flex items-center justify-center z-50 p-4"
            >
              <div className="bg-card border border-border rounded-2xl p-8 max-w-md w-full">
                <h3 className="text-xl font-medium mb-3">Upload Document</h3>
                <p className="text-sm text-muted-foreground mb-6">
                  Upload a PDF, Word document, or text file to start chatting with AI.
                </p>

                <div
                  onClick={() => !isUploading && fileInputRef.current?.click()}
                  className={cn(
                    "border-2 border-dashed border-border rounded-xl p-12 text-center transition-all cursor-pointer",
                    !isUploading && "hover:border-primary hover:bg-accent/50",
                    isUploading && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-card border border-border flex items-center justify-center">
                    {isUploading ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <Sparkles className="w-6 h-6 text-primary" />
                      </motion.div>
                    ) : (
                      <Upload className="w-6 h-6 text-primary" />
                    )}
                  </div>
                  <p className="text-sm font-medium mb-1">
                    {isUploading ? 'Processing document...' : 'Click to upload'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    PDF, DOCX, or TXT (Max 10MB)
                  </p>
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />

                <div className="flex gap-3 mt-6">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setShowUploadModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Choose File
                  </Button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
    )
  );
}
