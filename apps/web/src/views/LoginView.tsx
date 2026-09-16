import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { AmbientConstellation } from '../components/3d/AmbientConstellation';
import { Shield, Lock, ArrowRight, CheckCircle2 } from 'lucide-react';

export const LoginView: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('ananya.roy@delhipolice.gov.in');
  const [badgeId, setBadgeId] = useState('DL-SP-9014');

  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const success = await login(email, badgeId);
    if (!success) {
      setError("Invalid credentials. Please check your email and badge ID.");
    }
  };

  return (
    <div
      style={{
        position: 'relative',
        minHeight: '100vh',
        width: '100vw',
        backgroundColor: 'var(--cnas-bg)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Background Ambient 3D Constellation */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          opacity: 0.8,
        }}
      >
        <AmbientConstellation count={64} />
      </div>

      {/* Atmospheric Background Grid */}
      <svg
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          opacity: 0.35,
          pointerEvents: 'none',
        }}
      >
        <defs>
          <pattern id="login-grid" width="36" height="36" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="#40608a" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#login-grid)" />
      </svg>

      {/* Login Card */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          width: '100%',
          maxWidth: '440px',
          margin: '1.5rem',
          backgroundColor: 'rgba(255, 255, 255, 0.94)',
          backdropFilter: 'blur(20px)',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--cnas-border)',
          boxShadow: 'var(--shadow-lg)',
          padding: '2.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem',
        }}
      >
        {/* Header Branding */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--radius-lg)',
              background: 'linear-gradient(135deg, var(--cnas-navy) 0%, #0051d5 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: 'var(--shadow-md)',
            }}
          >
            <Shield size={22} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontWeight: 800,
                fontSize: '22px',
                color: 'var(--cnas-navy)',
                letterSpacing: '-0.02em',
                lineHeight: 1,
              }}
            >
              CNAS
            </span>
            <span
              style={{
                fontSize: '10px',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--cnas-text-muted)',
                marginTop: '3px',
              }}
            >
              Criminal Network Analysis System
            </span>
          </div>
        </div>

        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
            Investigator Sign In
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--cnas-text-secondary)', marginTop: '4px' }}>
            Authorized law enforcement & intelligence forensic portal
          </p>
        </div>

        {error && (
          <div style={{ padding: '10px', backgroundColor: '#fee2e2', color: '#b91c1c', borderRadius: '4px', fontSize: '12px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--cnas-text-secondary)', marginBottom: '4px' }}>
              Official Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{ width: '100%', height: '38px', fontSize: '13px' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--cnas-text-secondary)', marginBottom: '4px' }}>
              Security Badge / Warrant ID
            </label>
            <input
              type="text"
              required
              value={badgeId}
              onChange={(e) => setBadgeId(e.target.value)}
              style={{ width: '100%', height: '38px', fontSize: '13px' }}
            />
          </div>

          <div
            style={{
              padding: '0.65rem 0.85rem',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--cnas-surface-subtle)',
              border: '1px solid var(--cnas-border)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '11px',
              color: 'var(--cnas-text-muted)',
            }}
          >
            <Lock size={14} color="var(--cnas-verified)" />
            <span>FIPS 140-2 Encrypted Session · Section 65B Audit Logging</span>
          </div>

          <button
            type="submit"
            style={{
              height: '42px',
              backgroundColor: 'var(--cnas-navy)',
              color: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              fontWeight: 600,
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              boxShadow: 'var(--shadow-md)',
              marginTop: '0.5rem',
            }}
          >
            <span>Authenticate & Access Workstation</span>
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '11px', color: 'var(--cnas-verified)' }}>
          <CheckCircle2 size={14} />
          <span>Test credentials loaded: Insp. Ananya Roy (Special Cell)</span>
        </div>
      </div>
    </div>
  );
};
