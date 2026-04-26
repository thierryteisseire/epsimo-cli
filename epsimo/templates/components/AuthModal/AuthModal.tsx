"use client";

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext'; // Assumes user has this context
import { api } from '@/lib/api-client'; // Assumes user has this client
import { Modal } from '@/components/ui/Modal/Modal';
import { Input } from '@/components/ui/Input/Input';
import { Button } from '@/components/ui/Button/Button';
import styles from './AuthModal.module.css';

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
    defaultTab?: 'login' | 'signup';
}

export const AuthModal: React.FC<AuthModalProps> = ({
    isOpen,
    onClose,
    onSuccess,
    defaultTab = 'login'
}) => {
    const [mode, setMode] = useState<'login' | 'signup'>(defaultTab);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            if (mode === 'login') {
                const response = await api.post('/auth/login', {
                    body: { email, password }
                });
                login(response.jwt_token, response.main_agent_id, response.main_thread_id);
            } else {
                const response = await api.post('/auth/signup', {
                    body: { email, password, name }
                });
                // Auto-login after signup
                if (response.jwt_token) {
                    login(response.jwt_token, response.main_agent_id, response.main_thread_id);
                }
            }

            if (onSuccess) onSuccess();
            onClose();
        } catch (err: any) {
            console.error('Auth error:', err);
            setError(err.message || `Failed to ${mode}. Please check your details.`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={mode === 'login' ? 'Welcome Back' : 'Create Account'}
            size="sm"
            footer={
                <div className={styles.footer}>
                    <p>
                        {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
                        <button
                            type="button"
                            className={styles.switchBtn}
                            onClick={() => {
                                setMode(mode === 'login' ? 'signup' : 'login');
                                setError(null);
                            }}
                        >
                            {mode === 'login' ? 'Sign up' : 'Log in'}
                        </button>
                    </p>
                </div>
            }
        >
            <form onSubmit={handleSubmit} className={styles.form}>
                {mode === 'signup' && (
                    <Input
                        label="Full Name"
                        placeholder="John Doe"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        fullWidth
                    />
                )}

                <Input
                    type="email"
                    label="Email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    fullWidth
                />

                <Input
                    type="password"
                    label="Password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    fullWidth
                    minLength={8}
                />

                {error && (
                    <div className={styles.errorAlert}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                        <span>{error}</span>
                    </div>
                )}

                <Button
                    type="submit"
                    fullWidth
                    isLoading={isLoading}
                >
                    {mode === 'login' ? 'Sign In' : 'Create Account'}
                </Button>
            </form>
        </Modal>
    );
};
