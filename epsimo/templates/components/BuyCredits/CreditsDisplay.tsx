"use client";

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { BuyCreditsModal } from './BuyCreditsModal';

interface CreditsDisplayProps {
    className?: string;
    variant?: 'simple' | 'full';
}

export const CreditsDisplay: React.FC<CreditsDisplayProps> = ({
    className,
    variant = 'simple'
}) => {
    const { user, isLoading } = useAuth();
    const [isModalOpen, setIsModalOpen] = useState(false);

    if (isLoading || !user || user.thread_count === undefined || user.max_thread_count === undefined) {
        return null; // Or a skeleton loader
    }

    const percentage = Math.min(100, Math.max(0, (user.thread_count / user.max_thread_count) * 100));
    const isLow = user.max_thread_count - user.thread_count < 10 || percentage > 90;
    const isCritical = user.thread_count >= user.max_thread_count;

    return (
        <>
            <div
                className={className}
                style={{
                    padding: '6px 12px',
                    background: 'var(--background-surface-base)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '20px',
                    fontSize: '0.8rem',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                }}
                onClick={() => setIsModalOpen(true)}
                title="Click to buy more threads"
            >
                <div style={{ position: 'relative', width: '16px', height: '16px' }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: isCritical ? '#ef4444' : isLow ? '#f59e0b' : '#10b981' }}>
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 2v20"></path>
                        <path d="M2 12h20"></path>
                    </svg>
                </div>

                {variant === 'full' ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                            <span>Threads Used</span>
                            <span style={{ fontWeight: 600, color: isCritical ? '#ef4444' : 'inherit' }}>
                                {user.thread_count} / {user.max_thread_count}
                            </span>
                        </div>
                        <div style={{ width: '100px', height: '4px', background: 'var(--border-color)', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{
                                width: `${percentage}%`,
                                height: '100%',
                                background: isCritical ? '#ef4444' : isLow ? '#f59e0b' : '#10b981',
                                transition: 'width 0.3s ease'
                            }}></div>
                        </div>
                    </div>
                ) : (
                    <>
                        <span style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            background: isCritical ? '#ef4444' : isLow ? '#f59e0b' : '#10b981',
                            display: 'none' // Replaced by icon
                        }}></span>
                        Threads: <strong style={{ color: isCritical ? '#ef4444' : 'inherit' }}>{user.thread_count}</strong> / {user.max_thread_count}
                        <span style={{
                            marginLeft: '4px',
                            fontSize: '0.7rem',
                            background: 'var(--color-primary)',
                            color: 'white',
                            padding: '1px 6px',
                            borderRadius: '8px',
                            opacity: 0.8
                        }}>+</span>
                    </>
                )}
            </div>

            <BuyCreditsModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
            />
        </>
    );
};
