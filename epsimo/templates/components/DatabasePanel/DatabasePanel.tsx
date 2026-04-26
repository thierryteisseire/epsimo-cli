"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api-client';
import styles from './DatabasePanel.module.css';

interface DatabasePanelProps {
  threadId: string | null;
  refreshKey?: number; // increment to trigger refresh
}

export default function DatabasePanel({ threadId, refreshKey = 0 }: DatabasePanelProps) {
  const [dbState, setDbState] = useState<Record<string, any> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  const fetchState = useCallback(async () => {
    if (!threadId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await (api.get as any)(`/threads/${threadId}/state`);
      const values = data?.values ?? data ?? {};
      // Filter out message arrays — keep only structured DB entries
      const filtered: Record<string, any> = {};
      if (typeof values === 'object' && !Array.isArray(values)) {
        for (const [k, v] of Object.entries(values)) {
          if (k === 'messages' || Array.isArray(v)) continue;
          filtered[k] = v;
        }
      }
      setDbState(filtered);
    } catch (e: any) {
      setError(e?.message || 'Failed to load state');
    } finally {
      setIsLoading(false);
    }
  }, [threadId]);

  useEffect(() => { fetchState(); }, [fetchState, refreshKey]);

  const toggleKey = (key: string) => {
    setExpandedKeys(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  if (!threadId) {
    return (
      <div className={styles.panel}>
        <div className={styles.header}>
          <span className={styles.icon}>🗄️</span>
          <h3>Virtual Database</h3>
        </div>
        <p className={styles.empty}>Start a conversation to populate the database.</p>
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.icon}>🗄️</span>
        <h3>Virtual Database</h3>
        <button className={styles.refreshBtn} onClick={fetchState} disabled={isLoading} title="Refresh">
          ↻
        </button>
      </div>

      {isLoading && !dbState && <p className={styles.loading}>Loading…</p>}
      {error && <p className={styles.error}>{error}</p>}

      {dbState && Object.keys(dbState).length === 0 && (
        <p className={styles.empty}>DB Empty — the agent hasn't written any structured data yet.</p>
      )}

      {dbState && Object.keys(dbState).length > 0 && (
        <div className={styles.entries}>
          {Object.entries(dbState).map(([key, value]) => {
            const isObject = typeof value === 'object' && value !== null;
            const expanded = expandedKeys.has(key);
            return (
              <div key={key} className={styles.entry}>
                <button className={styles.entryHeader} onClick={() => isObject && toggleKey(key)}>
                  <span className={styles.key}>{key}</span>
                  {isObject ? (
                    <span className={styles.chevron}>{expanded ? '▾' : '▸'}</span>
                  ) : (
                    <span className={styles.value}>{String(value)}</span>
                  )}
                </button>
                {isObject && expanded && (
                  <pre className={styles.json}>{JSON.stringify(value, null, 2)}</pre>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
