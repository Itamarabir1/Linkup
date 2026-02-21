/**
 * קומפוננטה לבדיקת הגדרות Google OAuth
 * פתח את הקונסול כדי לראות את כל המידע
 */
import { useEffect, useState } from 'react';

const CREDENTIALS_URL = 'https://console.cloud.google.com/apis/credentials';

export default function GoogleSignInDebug() {
  const [copied, setCopied] = useState(false);
  const origin = typeof window !== 'undefined' ? window.location.origin : '';

  const copyOrigin = () => {
    if (!origin) return;
    navigator.clipboard.writeText(origin).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  useEffect(() => {
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    
    console.log('========================================');
    console.log('🔍 Google OAuth Debug Information');
    console.log('========================================');
    console.log('');
    console.log('📋 Client ID Configuration:');
    console.log(`   VITE_GOOGLE_CLIENT_ID: ${googleClientId || 'NOT SET'}`);
    console.log(`   Format valid: ${googleClientId?.includes('.apps.googleusercontent.com') ? '✅' : '❌'}`);
    console.log('');
    console.log('🌐 Current Page Information:');
    console.log(`   Origin: ${window.location.origin}`);
    console.log(`   Host: ${window.location.host}`);
    console.log(`   Protocol: ${window.location.protocol}`);
    console.log(`   Full URL: ${window.location.href}`);
    console.log('');
    console.log('📋 Google Cloud Console Checklist:');
    console.log('');
    console.log('1️⃣  Project Selection:');
    console.log('   - Go to: https://console.cloud.google.com/');
    console.log('   - Select project: linkup-app-df18d (or your project)');
    console.log('   - Verify you are in the correct project');
    console.log('');
    console.log('2️⃣  OAuth Client ID Configuration:');
    console.log('   - Go to: https://console.cloud.google.com/apis/credentials');
    console.log(`   - Find Client ID: ${googleClientId}`);
    console.log('   - Click on it to edit');
    console.log('   - Verify it is type "Web application"');
    console.log('   - Under "Authorized JavaScript origins", ensure you have:');
    console.log(`     ✅ ${window.location.origin}`);
    console.log('     ✅ http://localhost');
    console.log('   - Under "Authorized redirect URIs", ensure you have:');
    console.log(`     ✅ ${window.location.origin}/`);
    console.log('     ✅ http://localhost/');
    console.log('   - Click "Save"');
    console.log('');
    console.log('3️⃣  OAuth Consent Screen:');
    console.log('   - Go to: https://console.cloud.google.com/apis/credentials/consent');
    console.log('   - Check "Publishing status":');
    console.log('     • If "Testing":');
    console.log('       - Go to "Test users" tab');
    console.log('       - Add your email address');
    console.log('       - Only test users can sign in');
    console.log('     • If "In production":');
    console.log('       - All users can sign in');
    console.log('       - May require verification for sensitive scopes');
    console.log('');
    console.log('4️⃣  Common Issues:');
    console.log('   ❌ Client ID belongs to different project');
    console.log('   ❌ OAuth Consent Screen is in "Testing" mode without test user');
    console.log('   ❌ Origin not exactly matching (trailing slash, port, etc.)');
    console.log('   ❌ Changes not saved or not propagated (wait 30 seconds)');
    console.log('   ❌ Browser cache (clear cache or use incognito)');
    console.log('   ❌ Ad blockers or browser extensions blocking requests');
    console.log('');
    console.log('5️⃣  Testing Steps:');
    console.log('   1. Clear browser cache (Ctrl+Shift+Delete)');
    console.log('   2. Try incognito/private window');
    console.log('   3. Disable all browser extensions');
    console.log('   4. Check browser console for errors');
    console.log('   5. Verify network tab shows requests to accounts.google.com');
    console.log('');
    console.log('========================================');
    
    // נסה לטעון את Google Identity Services script
    if (!window.google && googleClientId) {
      console.log('📥 Loading Google Identity Services script...');
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        console.log('✅ Google Identity Services script loaded');
        if (window.google?.accounts?.id) {
          console.log('✅ Google Identity Services API available');
          try {
            window.google.accounts.id.initialize({
              client_id: googleClientId,
              callback: (response: { credential: string }) => {
                console.log('✅ Callback received:', response.credential.substring(0, 50) + '...');
              },
            });
            console.log('✅ Google Identity Services initialized successfully');
          } catch (err) {
            console.error('❌ Failed to initialize:', err);
          }
        } else {
          console.error('❌ Google Identity Services API not available');
        }
      };
      script.onerror = () => {
        console.error('❌ Failed to load Google Identity Services script');
      };
      document.head.appendChild(script);
    } else if (window.google) {
      console.log('✅ Google Identity Services already loaded');
    }
  }, []);

  const isHttps = origin.startsWith('https://');

  return (
    <div style={{
      marginBottom: '1rem',
      padding: '0.75rem 1rem',
      background: '#fef3c7',
      border: '1px solid #d97706',
      borderRadius: '8px',
      fontSize: '0.85rem',
      direction: 'ltr',
      textAlign: 'left',
    }}>
      <strong style={{ color: '#92400e' }}>🔧 תיקון 403 – "The given origin is not allowed"</strong>
      <p style={{ margin: '0.5rem 0 0', color: '#78350f' }}>
        ה-origin שצריך להופיע ב-Google:
      </p>
      <p style={{ margin: '0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
        <code style={{ background: '#fff', padding: '0.25rem 0.5rem', borderRadius: '4px', wordBreak: 'break-all' }}>
          {origin || '—'}
        </code>
        <button
          type="button"
          onClick={copyOrigin}
          style={{
            padding: '0.25rem 0.5rem',
            fontSize: '0.8rem',
            cursor: 'pointer',
            background: '#d97706',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
          }}
        >
          {copied ? 'הועתק!' : 'העתק'}
        </button>
      </p>
      <p style={{ margin: '0.5rem 0 0', color: '#78350f' }}>
        1. פתח{' '}
        <a href={CREDENTIALS_URL} target="_blank" rel="noopener noreferrer" style={{ color: '#b45309', fontWeight: 'bold' }}>
          Google Cloud Console → Credentials
        </a>
        <br />
        2. לחץ על ה-Client ID מסוג "Web application".
        <br />
        3. ב־<strong>Authorized JavaScript origins</strong> לחץ "ADD URI" והוסף <strong>בדיוק</strong> את הכתובת שהעתקת ({origin}).
        <br />
        4. שמור (Save) והמתן כ־30 שניות לפני רענון.
      </p>
      {isHttps && (
        <p style={{ margin: '0.35rem 0 0', color: '#b45309' }}>
          ⚠️ אתה נכנס עם HTTPS – ה-origin שצריך להוסיף הוא <code>{origin}</code>.
        </p>
      )}
      <p style={{ margin: '0.35rem 0 0', color: '#64748b', fontSize: '0.8rem' }}>
        טיפ: אם לפעמים אתה נכנס מ-<code>localhost</code> ולפעמים מ-<code>127.0.0.1</code>, הוסף את שני הכתובות ב-Authorized JavaScript origins.
      </p>
    </div>
  );
}
