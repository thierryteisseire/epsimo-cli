"use client";

import React, { useState, useEffect } from 'react';
import styles from './ToolRenderers.module.css';

export interface ToolCall {
    id: string;
    function?: {
        name: string;
        arguments: string;
    };
    name?: string;
    type?: string;
    args?: any;
}

// Tool icon mapping for common tools
const getToolIcon = (name: string): string => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('search') || lowerName.includes('tavily') || lowerName.includes('duckduckgo')) return '🔍';
    if (lowerName.includes('weather')) return '🌤️';
    if (lowerName.includes('calculator') || lowerName.includes('math')) return '🧮';
    if (lowerName.includes('database') || lowerName.includes('sql')) return '🗄️';
    if (lowerName.includes('file') || lowerName.includes('document')) return '📄';
    if (lowerName.includes('image') || lowerName.includes('dall')) return '🎨';
    if (lowerName.includes('code') || lowerName.includes('python')) return '💻';
    if (lowerName.includes('email') || lowerName.includes('mail')) return '📧';
    if (lowerName.includes('calendar') || lowerName.includes('schedule')) return '📅';
    if (lowerName.includes('retrieval') || lowerName.includes('rag')) return '📚';
    if (lowerName.includes('api') || lowerName.includes('http')) return '🌐';
    if (lowerName.includes('user') || lowerName.includes('account')) return '👤';
    return '⚡';
};

// Format tool name for display
const formatToolName = (name: string): string => {
    return name
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/\s+/g, ' ')
        .trim()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
};

// Collapsible JSON viewer
const JsonViewer = ({ data, defaultExpanded = false }: { data: any; defaultExpanded?: boolean }) => {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    let displayData = data;
    if (typeof data === 'string') {
        try {
            displayData = JSON.parse(data);
        } catch {
            displayData = data;
        }
    }

    const formatted = typeof displayData === 'string'
        ? displayData
        : JSON.stringify(displayData, null, 2);

    const lineCount = formatted.split('\n').length;
    const isLong = lineCount > 5 || formatted.length > 200;

    if (!isLong) {
        return <pre className={styles.jsonContent}>{formatted}</pre>;
    }

    return (
        <div className={styles.jsonViewer}>
            <pre className={`${styles.jsonContent} ${!isExpanded ? styles.collapsed : ''}`}>
                {formatted}
            </pre>
            <button
                className={styles.expandButton}
                onClick={() => setIsExpanded(!isExpanded)}
            >
                {isExpanded ? 'Show less' : 'Show more'}
            </button>
        </div>
    );
};

// Modern Tool Card Component
export const ToolCard = ({
    toolCall,
    response,
    isExecuting = false,
    status = 'pending'
}: {
    toolCall: any;
    response?: any;
    isExecuting?: boolean;
    status?: 'pending' | 'running' | 'success' | 'error';
}) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [showArgs, setShowArgs] = useState(false);

    const name = toolCall.function?.name || toolCall.name || toolCall.tool || "Unknown Tool";
    const icon = getToolIcon(name);
    const displayName = formatToolName(name);

    // Parse arguments
    let args: any = {};
    const rawArgs = toolCall.function?.arguments || toolCall.args || toolCall.arguments || toolCall.input;
    if (rawArgs) {
        try {
            args = typeof rawArgs === 'string' ? JSON.parse(rawArgs) : rawArgs;
        } catch {
            args = { input: rawArgs };
        }
    }

    // Get a summary of the args for preview
    const argsSummary = Object.entries(args)
        .slice(0, 2)
        .map(([key, value]) => {
            const strValue = typeof value === 'string' ? value : JSON.stringify(value);
            return strValue.length > 30 ? strValue.substring(0, 30) + '...' : strValue;
        })
        .join(', ');

    const currentStatus = isExecuting ? 'running' : (response ? 'success' : status);

    return (
        <div className={`${styles.toolCard} ${styles[`status_${currentStatus}`]}`}>
            <div
                className={styles.toolHeader}
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className={styles.toolHeaderLeft}>
                    <div className={`${styles.statusIndicator} ${styles[`indicator_${currentStatus}`]}`}>
                        {currentStatus === 'running' ? (
                            <div className={styles.pulsingDot} />
                        ) : currentStatus === 'success' ? (
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                                <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                        ) : currentStatus === 'error' ? (
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        ) : (
                            <div className={styles.pendingDot} />
                        )}
                    </div>
                    <span className={styles.toolIcon}>{icon}</span>
                    <span className={styles.toolName}>{displayName}</span>
                </div>

                <div className={styles.toolHeaderRight}>
                    {argsSummary && !isExpanded && (
                        <span className={styles.argsSummary}>{argsSummary}</span>
                    )}
                    <svg
                        className={`${styles.chevron} ${isExpanded ? styles.chevronExpanded : ''}`}
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                    >
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
            </div>

            {isExpanded && (
                <div className={styles.toolBody}>
                    {/* Arguments Section */}
                    {Object.keys(args).length > 0 && (
                        <div className={styles.toolSection}>
                            <button
                                className={styles.sectionHeader}
                                onClick={(e) => { e.stopPropagation(); setShowArgs(!showArgs); }}
                            >
                                <span className={styles.sectionTitle}>Input</span>
                                <svg
                                    className={`${styles.miniChevron} ${showArgs ? styles.chevronExpanded : ''}`}
                                    width="12"
                                    height="12"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                >
                                    <polyline points="6 9 12 15 18 9"></polyline>
                                </svg>
                            </button>
                            {showArgs && (
                                <div className={styles.sectionContent}>
                                    <JsonViewer data={args} />
                                </div>
                            )}
                        </div>
                    )}

                    {/* Status/Progress Section */}
                    {currentStatus === 'running' && (
                        <div className={styles.runningStatus}>
                            <div className={styles.progressBar}>
                                <div className={styles.progressFill} />
                            </div>
                            <span className={styles.runningText}>Searching...</span>
                        </div>
                    )}

                    {/* Response Section */}
                    {response && (
                        <div className={styles.toolSection}>
                            <div className={styles.sectionHeader}>
                                <span className={styles.sectionTitle}>Output</span>
                            </div>
                            <div className={styles.sectionContent}>
                                <JsonViewer data={response} defaultExpanded={true} />
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// Legacy components for backward compatibility
export const ToolRequest = ({ toolCall }: { toolCall: any }) => {
    return <ToolCard toolCall={toolCall} status="pending" />;
};

export const ToolResponse = ({ content }: { content: string | any }) => {
    let displayContent = content;
    if (content && typeof content === 'object') {
        displayContent = content.output || content.result || content.content || content;
    }
    if (typeof displayContent !== 'string') {
        try {
            displayContent = JSON.stringify(displayContent, null, 2);
        } catch {
            displayContent = String(displayContent);
        }
    }

    return (
        <div className={styles.legacyResponse}>
            <div className={styles.responseHeader}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Result</span>
            </div>
            <div className={styles.responseContent}>
                <pre>{displayContent}</pre>
            </div>
        </div>
    );
};

export const ToolExecuting = ({ name }: { name: string }) => {
    const icon = getToolIcon(name);
    const displayName = formatToolName(name);

    return (
        <div className={styles.executingCard}>
            <div className={styles.executingHeader}>
                <div className={styles.pulsingDot} />
                <span className={styles.toolIcon}>{icon}</span>
                <span className={styles.executingName}>{displayName}</span>
            </div>
            <div className={styles.executingProgress}>
                <div className={styles.progressBar}>
                    <div className={styles.progressFill} />
                </div>
            </div>
        </div>
    );
};

// Tool Usage Container - groups tool calls together
export const ToolUsageContainer = ({
    toolCalls,
    toolResponses = {},
    currentTool = null
}: {
    toolCalls: any[];
    toolResponses?: Record<string, any>;
    currentTool?: string | null;
}) => {
    if (!toolCalls || toolCalls.length === 0) return null;

    return (
        <div className={styles.toolUsageContainer}>
            <div className={styles.toolUsageHeader}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
                </svg>
                <span>Using {toolCalls.length} tool{toolCalls.length > 1 ? 's' : ''}</span>
            </div>
            <div className={styles.toolCardList}>
                {toolCalls.map((toolCall, index) => {
                    const toolId = toolCall.id || `tool-${index}`;
                    const toolName = toolCall.function?.name || toolCall.name || '';
                    const isRunning = currentTool === toolName;
                    const response = toolResponses[toolId];

                    return (
                        <ToolCard
                            key={toolId}
                            toolCall={toolCall}
                            response={response}
                            isExecuting={isRunning}
                            status={response ? 'success' : (isRunning ? 'running' : 'pending')}
                        />
                    );
                })}
            </div>
        </div>
    );
};
