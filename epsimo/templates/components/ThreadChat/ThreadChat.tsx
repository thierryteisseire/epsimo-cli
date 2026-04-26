"use client";

import React, { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';
import { Button } from '@/components/ui/Button/Button';
import styles from './ThreadChat.module.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ToolRequest, ToolResponse, ToolExecuting, ToolUsageContainer } from './components/ToolRenderers';

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system' | 'tool';
    type?: string;
    content: string | any;
    timestamp?: string;
    tool_calls?: any[];
    tool_call_id?: string;
    name?: string;
}

interface ThreadChatProps {
    threadId: string;
    onBack?: () => void;
    className?: string;
    showHeader?: boolean;
}

export default function ThreadChat({ threadId, onBack, className, showHeader = true }: ThreadChatProps) {
    const router = useRouter();
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentTool, setCurrentTool] = useState<string | null>(null);
    const [isUploadingFiles, setIsUploadingFiles] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const isProcessingRef = useRef(false);
    const hasFetchedRef = useRef(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // We need to track the current threadId to reset state when it changes
    const currentThreadIdRef = useRef(threadId);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const [thread, setThread] = useState<any>(null);

    // Reset state when threadId changes
    if (threadId !== currentThreadIdRef.current) {
        currentThreadIdRef.current = threadId;
        hasFetchedRef.current = false;
        setMessages([]);
        setThread(null);
    }

    useEffect(() => {
        const fetchThreadData = async () => {
            if (!threadId || hasFetchedRef.current) return;
            hasFetchedRef.current = true;
            setIsLoading(true);
            setError(null);
            try {
                // 1. Get thread details first to verify existence and get context
                console.log('Fetching thread details for:', threadId);
                const threadDetails = await (api.get as any)(`/threads/${threadId}`);
                console.log('Thread details received:', JSON.stringify(threadDetails).substring(0, 500));
                setThread(threadDetails);

                // 2. Try state first (often more reliable and contains latest messages)
                let data = null;
                console.log('Attempting to fetch thread state...');
                try {
                    data = await (api.get as any)(`/threads/${threadId}/state`);
                    console.log('State fetch success, keys:', Object.keys(data || {}));
                } catch (stateErr: any) {
                    console.warn('Thread state fetch failed, trying history backup...', stateErr);

                    // 3. Fallback to history if state fails
                    try {
                        data = await (api.get as any)(`/threads/${threadId}/history`);
                        console.log('History backup success');
                    } catch (historyErr: any) {
                        console.error('Both state and history fetch failed:', historyErr);

                        // Check for specific backend configuration errors
                        const isToolError =
                            stateErr?.message?.toLowerCase()?.includes('tool configuration') ||
                            stateErr?.message?.toLowerCase()?.includes('tool type') ||
                            historyErr?.message?.toLowerCase()?.includes('tool configuration') ||
                            historyErr?.message?.toLowerCase()?.includes('tool type');

                        if (isToolError) {
                            setError("This thread's assistant has an invalid tool configuration. Please edit the assistant in your Project view and click 'Save Changes' to refresh its configuration.");
                        } else {
                            setError("Could not load previous messages. You can still start a new conversation below.");
                        }

                        setMessages([]);
                        setIsLoading(false);
                        return;
                    }
                }

                console.log('Thread data received, processing messages...');
                let rawMessages: any[] = [];

                if (Array.isArray(data)) {
                    // 1. History format (List of snapshots)
                    if (data.length > 0) {
                        // Find the first snapshot that has messages in its values or at the root
                        for (const item of data) {
                            const candidate = item.values?.messages || item.messages || (Array.isArray(item.values) ? item.values : null);
                            if (Array.isArray(candidate) && candidate.length > 0) {
                                rawMessages = candidate;
                                break;
                            }
                        }
                        // If still empty and data itself is an array of messages
                        if (rawMessages.length === 0 && data[0].content && (data[0].role || data[0].type)) {
                            rawMessages = data;
                        }
                    }
                } else if (data && typeof data === 'object') {
                    // 2. State format (Single object)
                    const values = data.values || data.checkpoint?.values || data;
                    console.log('Using values for extraction:', JSON.stringify(values).substring(0, 500));

                    if (Array.isArray(values)) {
                        rawMessages = values;
                    } else if (values && typeof values === 'object') {
                        // Look for common message array keys
                        const messageKeys = ['messages', 'history', 'chat_history', 'msgs'];
                        for (const key of messageKeys) {
                            if (Array.isArray(values[key]) && values[key].length > 0) {
                                rawMessages = values[key];
                                console.log(`Found messages in values.${key}`);
                                break;
                            }
                        }

                        // Fallback: check if any key in values is an array (likely messages)
                        if (rawMessages.length === 0) {
                            const arrayKey = Object.keys(values).find(k => Array.isArray(values[k]) && values[k].length > 0);
                            if (arrayKey) {
                                console.log('State fallback: using array key:', arrayKey);
                                rawMessages = values[arrayKey];
                            }
                        }
                    }
                }

                console.log('Raw messages extracted, count:', rawMessages.length);
                if (Array.isArray(rawMessages)) {
                    setMessages(rawMessages.map((m: any) => {
                        let role = m.role || m.type;
                        if (role === 'human' || role === 'user') role = 'user';
                        if (role === 'ai' || role === 'assistant') role = 'assistant';
                        if (role === 'function' || role === 'tool') role = 'tool';

                        let content = m.content;
                        if (Array.isArray(content)) {
                            content = content
                                .map((block: any) => typeof block === 'string' ? block : (block.text || ''))
                                .join('\n');
                        } else if (content && typeof content === 'object' && role !== 'tool') {
                            // Only stringify if it's not a tool response, to preserve structure for ToolResponse component
                            content = content.text || JSON.stringify(content);
                        }
                        // If it's a tool response and an object, we keep it as is

                        return {
                            id: m.id || String(Math.random()),
                            role,
                            content,
                            tool_calls: m.tool_calls,
                            tool_call_id: m.tool_call_id,
                            name: m.name
                        } as Message;
                    }));
                } else {
                    setMessages([]);
                }
            } catch (err: any) {
                console.error('Critical error in fetchThreadData:', err);
                setError(err.message || 'Failed to initialize conversation');
            } finally {
                setIsLoading(false);
            }
        };

        fetchThreadData();

        // Add debugging info to console
        console.log('🔧 Tool Debugging Features Available:');
        console.log('=====================================');
        console.log('• Press Ctrl+Shift+D to toggle debug panel');
        console.log('• Run getToolDebugInfo() in console for debug summary');
        console.log('• Check window._toolDebug for real-time tool stats');
        console.log('• Check window._lastChunks for recent stream data');
        console.log('');

        // Add keyboard shortcut for debug panel (Ctrl+Shift+D)
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                const panel = document.getElementById('tool-debug-panel');
                if (panel) {
                    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';

                    // Log current debug state to console
                    if (typeof window !== 'undefined') {
                        console.log('🔧 Tool Debug State:', (window as any)._toolDebug);
                        console.log('📊 Last 5 Chunks:', (window as any)._lastChunks?.slice(-5));
                    }
                }
            }
        };

        document.addEventListener('keydown', handleKeyDown);

        return () => {
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, [threadId]);

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        // Optional: Add a toast notification here
    };

    useEffect(() => {
        scrollToBottom();

        // Update debug panel if it exists
        if (typeof window !== 'undefined' && (window as any)._toolDebug) {
            const debugInfo = (window as any)._toolDebug;
            const panel = document.getElementById('tool-debug-panel');
            if (panel) {
                const toolCallsEl = document.getElementById('tool-calls-count');
                const toolResponsesEl = document.getElementById('tool-responses-count');
                const aiMentionsEl = document.getElementById('ai-mentions-count');
                const chunkCountEl = document.getElementById('chunk-count');

                if (toolCallsEl) toolCallsEl.textContent = debugInfo.toolCallsFound.toString();
                if (toolResponsesEl) toolResponsesEl.textContent = debugInfo.toolResponsesFound.toString();
                if (aiMentionsEl) aiMentionsEl.textContent = debugInfo.aiMentionsTools.toString();
                if (chunkCountEl) chunkCountEl.textContent = ((window as any)._lastChunks?.length || 0).toString();
            }
        }
    }, [messages]);

    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!inputValue.trim() || isSending) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue.trim()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsSending(true);
        setError(null);

        // Stream monitoring variables
        let chunkCount = 0;
        let lastChunkTime = Date.now();
        let streamStarted = false;

        try {
            console.log('Sending message to thread:', threadId, 'Current thread context:', thread);

            let assistantMessageId = '';
            setCurrentTool(null);

            const mergeMessages = (current: Message[], incoming: any[]): Message[] => {
                const messageMap = new Map<string, Message>();
                current.forEach(m => messageMap.set(m.id, m));

                const normalizeMessage = (m: any) => {
                    let role = m.role || m.type || 'assistant';
                    // Handle server format: type: 'human'/'ai' -> role: 'user'/'assistant'
                    if (role === 'ai' || role === 'assistant') role = 'assistant';
                    if (role === 'human' || role === 'user') role = 'user';
                    if (role === 'function' || role === 'tool') role = 'tool';

                    let content = m.content;
                    if (Array.isArray(content)) {
                        content = content
                            .map((block: any) => typeof block === 'string' ? block : (block.text || ''))
                            .join('\n');
                    }

                    // Handle tool calls from server format
                    const tool_calls = m.tool_calls || m.additional_kwargs?.tool_calls || [];

                    return {
                        ...m,
                        role,
                        content: content || '',
                        tool_calls,
                        tool_call_id: m.tool_call_id, // Explicitly preserve tool_call_id
                        name: m.name, // Preserve tool name
                        // Use server ID or generate fallback
                        id: m.id || m.message_id || `msg-${Date.now()}-${Math.random()}`
                    };
                };

                incoming.forEach(incRaw => {
                    const inc = normalizeMessage(incRaw);
                    let id = inc.id || inc.message_id;

                    // Fallback ID for streaming assistant messages without explicit IDs
                    if (!id) {
                        if (inc.role === 'assistant') {
                            if (!assistantMessageId) {
                                assistantMessageId = (Date.now() + 1).toString();
                            }
                            id = assistantMessageId;
                        } else if (inc.role === 'tool') {
                            id = inc.tool_call_id || `tool-${Date.now()}`;
                        } else {
                            return;
                        }
                    }

                    // DE-DUPLICATION: If this is a user message, check if we already have it with a temp ID
                    if (inc.role === 'user') {
                        const existingTemp = Array.from(messageMap.values()).find(m =>
                            m.role === 'user' &&
                            m.content === inc.content &&
                            /^\d{13,}$/.test(m.id)
                        );
                        if (existingTemp) {
                            messageMap.delete(existingTemp.id);
                        }
                    }

                    const existing = messageMap.get(id);
                    if (existing) {
                        messageMap.set(id, {
                            ...existing,
                            ...inc,
                            // Preserve existing content if incoming is empty/undefined but we have content
                            content: (inc.content !== undefined && inc.content !== '') ? inc.content : existing.content,
                            // Merge tool calls
                            tool_calls: inc.tool_calls.length > 0 ? inc.tool_calls : existing.tool_calls,
                            role: inc.role // Always trust latest normalized role
                        });
                    } else if (['user', 'assistant', 'system', 'tool'].includes(inc.role)) {
                        messageMap.set(id, {
                            ...inc,
                            id,
                            content: inc.content || ''
                        });
                    }
                });

                return Array.from(messageMap.values());
            };

            // Track sending state with a ref to prevent race conditions
            if (isProcessingRef.current) return;
            isProcessingRef.current = true;

            // 1. Prepare input
            const messagePayload = {
                content: userMessage.content,
                type: 'human',
                role: 'user'
            };
            const streamInput = [messagePayload];

            const stream = (api as any).stream('/runs/stream', {
                body: {
                    thread_id: threadId,
                    input: streamInput,
                    stream_mode: ['messages', 'events', 'values']
                }
            });

            for await (const chunk of stream) {
                chunkCount++;
                lastChunkTime = Date.now();

                // Debug logging omitted for brevity but logic remains same

                // Track last chunks for debug
                if (typeof window !== 'undefined') {
                    (window as any)._lastChunks = (window as any)._lastChunks || [];
                    (window as any)._lastChunks.push(chunk);
                    if ((window as any)._lastChunks.length > 50) (window as any)._lastChunks.shift();
                }

                // Handle error chunks
                if (chunk && (chunk.status_code >= 400 || chunk.type === 'processing_error')) {
                    const errorMsg = chunk.message || chunk.details || 'Backend processing error';
                    throw new Error(`Tool execution error: ${errorMsg}`);
                }

                // Handle the actual server format
                if (chunk.event === 'start') {
                    streamStarted = true;
                    continue;
                } else if (chunk.event === 'metadata') {
                    continue;
                } else if (chunk.event === 'end') {
                    break;
                } else if (chunk.event === 'data' && Array.isArray(chunk)) {
                    // Server sends data as arrays of message objects
                    setMessages(prev => mergeMessages(prev, chunk));
                    continue;
                }

                // Legacy handling for other possible formats
                if (Array.isArray(chunk)) {
                    // Case A: Array of message snapshots
                    setMessages(prev => mergeMessages(prev, chunk));
                } else if (chunk.event === 'on_chat_model_stream' || chunk.event === 'messages/partial') {
                    // Case B: Event wrappers (deltas and signals)
                    const delta = chunk.data?.chunk?.content || chunk.data?.content;

                    // Extract tool call chunks from multiple possible locations
                    const toolCallChunks =
                        chunk.data?.chunk?.additional_kwargs?.tool_calls ||
                        chunk.data?.chunk?.tool_call_chunks ||
                        chunk.data?.chunk?.tool_calls ||
                        chunk.data?.tool_calls ||
                        chunk.tool_calls ||
                        [];

                    if (delta && typeof delta === 'string') {
                        if (!assistantMessageId) {
                            assistantMessageId = (Date.now() + 1).toString();
                            setMessages(prev => [...prev, {
                                id: assistantMessageId,
                                role: 'assistant',
                                content: delta,
                                tool_calls: []
                            }]);
                        } else {
                            setMessages(prev => prev.map(msg =>
                                msg.id === assistantMessageId ? { ...msg, content: msg.content + delta } : msg
                            ));
                        }
                    }

                    // Handle tool call chunks - accumulate instead of replace
                    if (toolCallChunks.length > 0) {
                        if (!assistantMessageId) {
                            assistantMessageId = (Date.now() + 1).toString();
                            setMessages(prev => [...prev, {
                                id: assistantMessageId,
                                role: 'assistant',
                                content: '',
                                tool_calls: toolCallChunks
                            }]);
                        } else {
                            setMessages(prev => prev.map(msg => {
                                if (msg.id === assistantMessageId) {
                                    // Merge tool calls by ID, accumulating argument chunks
                                    const existingCalls = msg.tool_calls || [];
                                    const mergedCalls = [...existingCalls];

                                    toolCallChunks.forEach((newCall: any) => {
                                        const callId = newCall.id || newCall.index;
                                        const existingIdx = mergedCalls.findIndex(
                                            (c: any) => (c.id || c.index) === callId
                                        );

                                        if (existingIdx >= 0) {
                                            // Accumulate arguments for existing tool call
                                            const existing = mergedCalls[existingIdx];
                                            const existingArgs = existing.function?.arguments || existing.args || '';
                                            const newArgs = newCall.function?.arguments || newCall.args || '';

                                            mergedCalls[existingIdx] = {
                                                ...existing,
                                                ...newCall,
                                                function: {
                                                    ...existing.function,
                                                    ...newCall.function,
                                                    arguments: existingArgs + newArgs
                                                },
                                                args: typeof existingArgs === 'string' && typeof newArgs === 'string'
                                                    ? existingArgs + newArgs
                                                    : newCall.args || existing.args
                                            };
                                        } else {
                                            mergedCalls.push(newCall);
                                        }
                                    });

                                    return { ...msg, tool_calls: mergedCalls };
                                }
                                return msg;
                            }));
                        }
                    }
                } else if (chunk.event === 'on_tool_start') {
                    const toolName = chunk.name || chunk.data?.name || chunk.data?.input?.tool || 'Retrieving data...';
                    setCurrentTool(toolName);

                    // Also extract tool call info if available
                    const toolInput = chunk.data?.input || chunk.data?.args || chunk.input;
                    if (toolInput && assistantMessageId) {
                        const toolCallFromEvent = {
                            id: chunk.run_id || chunk.data?.run_id || `tool-${Date.now()}`,
                            name: toolName,
                            args: toolInput
                        };
                        setMessages(prev => prev.map(msg => {
                            if (msg.id === assistantMessageId) {
                                const existingCalls = msg.tool_calls || [];
                                // Only add if not already present
                                if (!existingCalls.some((c: any) => c.name === toolName)) {
                                    return { ...msg, tool_calls: [...existingCalls, toolCallFromEvent] };
                                }
                            }
                            return msg;
                        }));
                    }
                } else if (chunk.event === 'on_tool_end') {
                    setCurrentTool(null);

                    // Capture tool response if available
                    const toolOutput = chunk.data?.output || chunk.output;
                    const toolRunId = chunk.run_id || chunk.data?.run_id;
                    if (toolOutput && toolRunId) {
                        setMessages(prev => {
                            // Check if we already have this tool response
                            const hasResponse = prev.some(m => m.role === 'tool' && m.tool_call_id === toolRunId);
                            if (hasResponse) return prev;

                            return [...prev, {
                                id: `tool-response-${toolRunId}`,
                                role: 'tool',
                                content: typeof toolOutput === 'string' ? toolOutput : JSON.stringify(toolOutput),
                                tool_call_id: toolRunId
                            }];
                        });
                    }
                } else if (chunk.values?.messages && Array.isArray(chunk.values.messages)) {
                    // Case C: Standard updates (values)
                    setMessages(prev => mergeMessages(prev, chunk.values.messages));
                }
            }
        } catch (err: any) {
            console.error('Failed to send message:', err);

            // Check if this was a premature stream termination
            const timeSinceStart = Date.now() - lastChunkTime;
            const isPrematureEnd = streamStarted && chunkCount < 3 && timeSinceStart < 5000;

            // Provide more specific error messages based on the error type
            let errorMessage = 'An unexpected error occurred while communicating with the AI.';

            if (isPrematureEnd) {
                errorMessage = 'Tool execution failed: The AI service encountered an error while trying to use tools. This may be due to a server-side configuration issue.';
            } else if (err.name === 'AbortError' || err.message?.includes('aborted')) {
                errorMessage = 'The request was cancelled or timed out.';
            } else if (err.message?.includes('fetch')) {
                errorMessage = 'Network error: Unable to connect to the AI service.';
            } else if (err.message?.includes('stream')) {
                errorMessage = 'Stream error: The AI service encountered an issue during processing.';
            } else if (err.message?.includes('tool') || err.message?.includes('Tool')) {
                errorMessage = 'Tool execution error: There was an issue running the requested tool.';
            } else if (err.message) {
                errorMessage = err.message;
            }

            setError(errorMessage);

            // Clean up: remove empty assistant messages
            setMessages(prev => prev.filter(msg =>
                (msg.content && msg.content !== '') ||
                (msg.tool_calls && msg.tool_calls.length > 0) ||
                msg.role !== 'assistant'
            ));
        } finally {
            setIsSending(false);
            setCurrentTool(null);
            isProcessingRef.current = false;
        }
    };

    const handleFileUpload = async (files: FileList | null) => {
        if (!files || files.length === 0 || !thread?.assistant_id) return;

        setIsUploadingFiles(true);
        setUploadError(null);

        try {
            const formData = new FormData();
            Array.from(files).forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'https://api.epsimoagents.com'}/assistants/${thread.assistant_id}/files`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                    },
                    body: formData
                }
            );

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
            }

            const result = await response.json();
            console.log('Files uploaded successfully:', result);

            // Add a system message to indicate files were uploaded
            const fileNames = Array.from(files).map(f => f.name).join(', ');
            const systemMessage: Message = {
                id: `upload-${Date.now()}`,
                role: 'system',
                content: `📎 Uploaded ${files.length} file(s): ${fileNames}. The assistant now has access to this content.`
            };
            setMessages(prev => [...prev, systemMessage]);

        } catch (err: any) {
            console.error('File upload error:', err);
            setUploadError(err.message || 'Failed to upload files');
        } finally {
            setIsUploadingFiles(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleFileButtonClick = () => {
        if (!thread?.assistant_id) {
            setUploadError('No assistant associated with this thread');
            return;
        }
        fileInputRef.current?.click();
    };

    // Group tool calls with their responses
    const toolResponseMap = new Map<string, Message>();
    const processedMessages: Message[] = [];

    messages.forEach(msg => {
        if (msg.role === 'tool' && (msg.tool_call_id || (msg as any).tool_call_id)) {
            const id = msg.tool_call_id || (msg as any).tool_call_id;
            toolResponseMap.set(id, msg);
        } else {
            processedMessages.push(msg);
        }
    });

    return (
        <div className={`${styles.chatContainer} ${className || ''}`}>
            {showHeader && (
                <div className={styles.chatHeader}>
                    {onBack && (
                        <button onClick={onBack} className={styles.backBtn}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"></path><path d="M12 19l-7-7 7-7"></path></svg>
                            Back
                        </button>
                    )}
                    <h2 className={styles.threadTitle}>{thread?.name || 'Untitled Thread'}</h2>
                </div>
            )}

            <div className={styles.messageList}>
                {processedMessages.map((message) => {
                    const isUser = message.role === 'user';
                    const isSystem = message.role === 'system';

                    if (isSystem) {
                        return (
                            <div key={message.id} className={`${styles.messageWrapper} ${styles.systemWrapper}`} style={{ alignSelf: 'center', opacity: 0.7 }}>
                                <span style={{ fontSize: '0.8rem', fontStyle: 'italic' }}>{String(message.content)}</span>
                            </div>
                        );
                    }

                    return (
                        <div key={message.id} className={`${styles.messageWrapper} ${isUser ? styles.userWrapper : styles.assistantWrapper}`}>
                            <div className={`${styles.avatar} ${isUser ? styles.userAvatar : styles.assistantAvatar}`}>
                                {isUser ? 'U' : 'AI'}
                            </div>
                            <div>
                                <div className={styles.messageBubble}>
                                    <button
                                        className={styles.copyBtn}
                                        onClick={() => copyToClipboard(typeof message.content === 'string' ? message.content : JSON.stringify(message.content))}
                                        title="Copy message"
                                    >
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                                    </button>
                                    <div className={styles.markdownContent}>
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                code({ node, inline, className, children, ...props }: any) {
                                                    const match = /language-(\w+)/.exec(className || '');
                                                    return !inline && match ? (
                                                        <SyntaxHighlighter
                                                            style={atomDark}
                                                            language={match[1]}
                                                            PreTag="div"
                                                            {...props}
                                                        >
                                                            {String(children).replace(/\n$/, '')}
                                                        </SyntaxHighlighter>
                                                    ) : (
                                                        <code className={className} {...props}>
                                                            {children}
                                                        </code>
                                                    );
                                                }
                                            }}
                                        >
                                            {typeof message.content === 'string' ? message.content : ''}
                                        </ReactMarkdown>
                                    </div>
                                </div>

                                {/* Render Tool Calls if present */}
                                {message.tool_calls && message.tool_calls.length > 0 && (
                                    <div style={{ marginTop: '8px', maxWidth: '100%' }}>
                                        <ToolUsageContainer
                                            toolCalls={message.tool_calls}
                                            toolResponses={Object.fromEntries(
                                                Array.from(toolResponseMap.entries()).map(([k, v]) => [k, v.content])
                                            )}
                                            currentTool={currentTool}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}

                {/* Loading indicator for messages */}
                {inputValue === '' && isLoading && messages.length === 0 && (
                    <div className={styles.loading}>
                        <div className={styles.spinner}></div>
                        <p>Loading conversation...</p>
                    </div>
                )}

                {/* Error Banner */}
                {error && (
                    <div className={styles.errorState}>
                        <div className={styles.errorIcon}>⚠️</div>
                        <h3>Something went wrong</h3>
                        <p>{error}</p>
                        <Button
                            className={styles.retryBtn}
                            onClick={() => window.location.reload()}
                        >
                            Refresh Page
                        </Button>
                    </div>
                )}

                {/* Show active tool execution even if no message yet */}
                {currentTool && messages.length > 0 &&
                    !messages[messages.length - 1].tool_calls?.some((tc: any) =>
                        (tc.function?.name === currentTool || tc.name === currentTool)
                    ) && (
                        <div className={styles.toolIndicator}>
                            <div className={styles.toolSpinner}></div>
                            <span className={styles.toolText}>Using {currentTool}...</span>
                        </div>
                    )}

                {/* Thinking/Typing indicator */}
                {isSending && !currentTool && (
                    <div className={`${styles.messageWrapper} ${styles.assistantWrapper}`}>
                        <div className={`${styles.avatar} ${styles.assistantAvatar}`}>AI</div>
                        <div className={styles.messageBubble + " " + styles.typingBubble}>
                            <div className={styles.typingDot}></div>
                            <div className={styles.typingDot}></div>
                            <div className={styles.typingDot}></div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <div className={styles.inputArea}>
                <div className={styles.inputContainer}>
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        style={{ display: 'none' }}
                        onChange={(e) => handleFileUpload(e.target.files)}
                        multiple
                    />
                    <Button
                        type="button"
                        onClick={handleFileButtonClick}
                        disabled={isUploadingFiles}
                        className={styles.fileBtn}
                        title="Upload files"
                    >
                        {isUploadingFiles ? (
                            <div className={styles.uploadSpinner}></div>
                        ) : (
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
                        )}
                    </Button>
                    <input
                        className={styles.chatInput}
                        placeholder={isUploadingFiles ? "Uploading files..." : "Message..."}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSendMessage();
                            }
                        }}
                        disabled={isSending || isUploadingFiles}
                    />
                    <Button
                        className={styles.sendBtn}
                        onClick={() => handleSendMessage()}
                        disabled={!inputValue.trim() || isSending || isUploadingFiles}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                    </Button>
                </div>
            </div>

            {uploadError && (
                <div style={{ position: 'absolute', bottom: '80px', left: '50%', transform: 'translateX(-50%)', width: '90%', maxWidth: '800px' }}>
                    <div className={styles.uploadError}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span>⚠️</span>
                            <span>{uploadError}</span>
                        </div>
                        <button className={styles.errorClose} onClick={() => setUploadError(null)}>×</button>
                    </div>
                </div>
            )}
        </div>
    );
}
