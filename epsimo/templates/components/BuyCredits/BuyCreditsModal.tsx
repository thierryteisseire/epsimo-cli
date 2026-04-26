"use client";

import React, { useState } from 'react';
import { api } from '@/lib/api-client';
import { Modal } from '@/components/ui/Modal/Modal';
import { Button } from '@/components/ui/Button/Button';
import { Input } from '@/components/ui/Input/Input';
import styles from './BuyCreditsModal.module.css';

interface BuyCreditsModalProps {
    isOpen: boolean;
    onClose: () => void;
    tokenPrice?: number; // Price per token/thread
}

export const BuyCreditsModal: React.FC<BuyCreditsModalProps> = ({
    isOpen,
    onClose,
    tokenPrice = 0.10 // Default fallback price
}) => {
    const [quantity, setQuantity] = useState<number>(100);
    const [isCustom, setIsCustom] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const packages = [
        { name: 'Starter', threads: 100, price: 10, popular: false },
        { name: 'Pro', threads: 500, price: 45, popular: true },
        { name: 'Max', threads: 1000, price: 80, popular: false },
    ];

    const currentPrice = isCustom ? (quantity * tokenPrice).toFixed(2) : (packages.find(p => p.threads === quantity)?.price || (quantity * tokenPrice)).toFixed(2);

    const handleCheckout = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response: any = await api.post('/checkout/create-checkout-session', {
                body: {
                    quantity,
                    total_amount: parseFloat(currentPrice)
                }
            });

            if (response && response.url) {
                window.location.href = response.url;
            } else {
                throw new Error('Invalid checkout response');
            }
        } catch (err: any) {
            console.error('Checkout error:', err);
            setError(err.message || 'Failed to start checkout');
            setIsLoading(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Add More Threads"
            size="lg"
            footer={
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', alignItems: 'center', width: '100%' }}>
                    <div style={{ marginRight: 'auto', fontWeight: 'bold' }}>
                        Total: €{currentPrice}
                    </div>
                    <Button variant="ghost" onClick={onClose} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button onClick={handleCheckout} isLoading={isLoading}>
                        Proceed to Checkout
                    </Button>
                </div>
            }
        >
            <div className={styles.container}>
                {error && (
                    <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4 text-sm">
                        {error}
                    </div>
                )}

                <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
                    Purchase additional threads to continue your conversations.
                </p>

                <div className={styles.pricingGrid}>
                    {packages.map((pkg) => (
                        <div
                            key={pkg.name}
                            className={`${styles.pricingCard} ${quantity === pkg.threads && !isCustom ? styles.selectedCard : ''}`}
                            onClick={() => {
                                setQuantity(pkg.threads);
                                setIsCustom(false);
                            }}
                        >
                            {pkg.popular && <span className={styles.popularBadge}>Most Popular</span>}
                            <div className={styles.threads}>{pkg.threads}</div>
                            <div className={styles.price}>Threads</div>
                            <div style={{ marginTop: 'auto', fontSize: '1.25rem', fontWeight: 'bold' }}>€{pkg.price}</div>
                        </div>
                    ))}
                </div>

                <div className={styles.customInput}>
                    <Button
                        variant="ghost"
                        fullWidth
                        onClick={() => setIsCustom(!isCustom)}
                        style={{ marginBottom: isCustom ? '16px' : '0' }}
                    >
                        {isCustom ? 'Hide Custom Amount' : 'Enter Custom Amount'}
                    </Button>

                    {isCustom && (
                        <Input
                            type="number"
                            label="Number of Threads"
                            value={quantity}
                            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 0))}
                            min={1}
                            placeholder={`Approx. €${(quantity * tokenPrice).toFixed(2)}`}
                            fullWidth
                        />
                    )}
                </div>
            </div>
        </Modal>
    );
};
