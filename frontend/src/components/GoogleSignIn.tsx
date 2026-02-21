import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

interface GoogleSignInProps {
  onError?: (error: string) => void;
  disabled?: boolean;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: { 
            client_id: string; 
            callback: (response: { credential: string }) => void;
            auto_select?: boolean;
            cancel_on_tap_outside?: boolean;
            itp_support?: boolean;
          }) => void;
          renderButton: (element: HTMLElement, config: { theme?: string; size?: string; text?: string; width?: number }) => void;
          prompt: (callback?: (notification: { isNotDisplayed: boolean; isSkippedMoment: boolean; dismissedMoment?: number; skippedMoment?: number }) => void) => void;
          disableAutoSelect: () => void;
        };
      };
    };
  }
}

export default function GoogleSignIn({ onError, disabled }: GoogleSignInProps) {
  const [loading, setLoading] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const { signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const buttonRef = useRef<HTMLDivElement>(null);
  const callbackRef = useRef<((response: { credential: string }) => Promise<void>) | null>(null);
  const initializedRef = useRef(false); // מונע קריאות כפולות

  // טעינת Google Identity Services script רק כשה-component נטען
  useEffect(() => {
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!googleClientId) {
      console.error('VITE_GOOGLE_CLIENT_ID not set in environment variables');
      if (onError) {
        onError('Google Client ID לא מוגדר. אנא הגדר VITE_GOOGLE_CLIENT_ID ב-.env');
      }
      return;
    }

    // בדיקה אם כבר אתחלנו - מונע קריאות כפולות
    if (initialized || scriptLoaded) {
      console.log('[GoogleSignIn] Already initialized/loaded, skipping script load...');
      return;
    }

    // פונקציה לאתחול Google Identity Services (מונעת קריאות כפולות)
    const initializeGoogleSignIn = () => {
      if (!window.google?.accounts?.id) {
        console.error('[GoogleSignIn] Google Identity Services API not available');
        return false;
      }
      
      // בדיקה אם כבר אתחלנו (מונע קריאות כפולות)
      if (initializedRef.current) {
        console.log('[GoogleSignIn] Already initialized (ref check), skipping...');
        return true;
      }
      
      const currentOrigin = window.location.origin;
      const currentHost = window.location.host;
      const currentProtocol = window.location.protocol;
      
      console.log('[GoogleSignIn] Initializing with:');
      console.log('  - Client ID:', googleClientId);
      console.log('  - Origin:', currentOrigin);
      console.log('  - Host:', currentHost);
      console.log('  - Protocol:', currentProtocol);
      console.log('  - Full URL:', window.location.href);
      
      try {
        // אתחול עם הגדרות נוספות שיכולות לעזור
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: async (response: { credential: string }) => {
            console.log('[GoogleSignIn] Callback called with credential');
            if (callbackRef.current) {
              await callbackRef.current(response);
            }
          },
          auto_select: false,
          cancel_on_tap_outside: true,
          itp_support: true, // תמיכה ב-Intelligent Tracking Prevention
        });
        console.log('[GoogleSignIn] ✅ Google Identity Services initialized successfully');
        initializedRef.current = true;
        setInitialized(true);
        return true;
      } catch (err) {
        console.error('[GoogleSignIn] ❌ Failed to initialize Google Identity Services:', err);
        const msg = err instanceof Error ? err.message : String(err);
        const isOriginError = /origin|not allowed|403|client id/i.test(msg);
        if (isOriginError && onError) {
          const originMsg = `ה-origin לא מורשה ב-Google. הוסף בדיוק את הכתובת הזו ב-Google Cloud Console → Credentials → ה-Client ID → Authorized JavaScript origins: ${currentOrigin}`;
          onError(originMsg);
        }
        if (err instanceof Error) {
          console.error('[GoogleSignIn] Error message:', err.message);
          console.error('[GoogleSignIn] Error stack:', err.stack);
        }
        return false;
      }
    };

    // בדיקה אם ה-script כבר נטען
    const existingScript = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
    if (existingScript) {
      // מחכים שה-script יסיים לטעון ואז מאתחלים מיד
      let checkCount = 0;
      const maxChecks = 50; // 5 שניות
      const checkInterval = setInterval(() => {
        checkCount++;
        if (window.google?.accounts?.id) {
          console.log('Google Identity Services loaded successfully');
          clearInterval(checkInterval);
          initializeGoogleSignIn();
          setScriptLoaded(true);
        } else if (checkCount >= maxChecks) {
          clearInterval(checkInterval);
          console.error('Google Identity Services failed to load after timeout');
          if (onError) {
            onError('Google Sign-In לא נטען. אנא רענן את הדף.');
          }
        }
      }, 100);
      return () => clearInterval(checkInterval);
    }

    // טעינת ה-script
    console.log('Loading Google Identity Services script...');
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      console.log('Google Identity Services script loaded');
      // מחכים קצת כדי לוודא שה-API זמין ואז מאתחלים מיד
      setTimeout(() => {
        if (window.google?.accounts?.id) {
          initializeGoogleSignIn();
          setScriptLoaded(true);
        } else {
          console.error('Google Identity Services API not available after script load');
          if (onError) {
            onError('Google Sign-In לא זמין. אנא רענן את הדף.');
          }
        }
      }, 100);
    };
    script.onerror = () => {
      console.error('Failed to load Google Identity Services script (may be 403 - origin not allowed)');
      if (onError) {
        const origin = window.location.origin;
        onError(`טעינת Google Sign-In נכשלה. הוסף את הכתובת הזו ב-Google Cloud Console → Credentials → Authorized JavaScript origins: ${origin}`);
      }
    };
    document.head.appendChild(script);

    return () => {
      // לא מוחקים את ה-script כי הוא יכול להיות בשימוש במקומות אחרים
    };
  }, [onError, initialized, scriptLoaded]);

  // הגדרת ה-callback
  useEffect(() => {
    callbackRef.current = async (response: { credential: string }) => {
      setLoading(true);
      try {
        await signInWithGoogle(response.credential);
        navigate('/', { replace: true });
      } catch (err: unknown) {
        const error = err as { code?: string; message?: string; response?: { data?: { detail?: string } } };
        if ((error.code === 'ECONNABORTED' || (error.message && error.message.includes('timeout'))) && onError) {
          onError('השרת לא מגיב בזמן. וודא שהבקאנד רץ (למשל http://127.0.0.1:8000) ושה-URL ב-frontend/.env (VITE_API_URL) נכון.');
          return;
        }
        const errorMessage = error.response?.data?.detail || error.message || 'התחברות נכשלה';
        if (onError) {
          onError(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    };
  }, [signInWithGoogle, navigate, onError]);

  // רינדור הכפתור כשה-script נטען ואתחלנו
  useEffect(() => {
    if (!scriptLoaded || !initialized || !buttonRef.current || disabled) return;

    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!googleClientId) return;

    // בדיקת ה-origin המדויק
    const currentOrigin = window.location.origin;
    console.log('Current origin:', currentOrigin);
    console.log('Google Client ID:', googleClientId);
    console.log('Rendering Google Sign-In button...');

    try {
      // רינדור הכפתור (ה-initialize כבר נקרא ב-useEffect הקודם)
      if (buttonRef.current) {
        const currentOrigin = window.location.origin;
        const currentHost = window.location.host;
        const currentProtocol = window.location.protocol;
        
        console.log('[GoogleSignIn] ========================================');
        console.log('[GoogleSignIn] 🔍 DEBUG INFO FOR BUTTON RENDERING:');
        console.log('[GoogleSignIn]   Origin:', currentOrigin);
        console.log('[GoogleSignIn]   Host:', currentHost);
        console.log('[GoogleSignIn]   Protocol:', currentProtocol);
        console.log('[GoogleSignIn]   Full URL:', window.location.href);
        console.log('[GoogleSignIn]   Client ID:', googleClientId);
        console.log('[GoogleSignIn]   Script loaded:', scriptLoaded);
        console.log('[GoogleSignIn]   Initialized:', initialized);
        console.log('[GoogleSignIn] ========================================');
        console.log('[GoogleSignIn] 📋 VERIFICATION CHECKLIST:');
        console.log('[GoogleSignIn] ✅ VERIFICATION CHECKLIST:');
        console.log('');
        console.log('[GoogleSignIn] 🔍 שלב 0: בדיקת Client ID');
        console.log(`[GoogleSignIn]    Client ID: ${googleClientId}`);
        console.log('[GoogleSignIn]    ✅ ודא שה-Client ID הזה שייך לפרויקט הנכון ב-Google Cloud Console');
        console.log('[GoogleSignIn]    ✅ ודא שה-Client ID הזה הוא מסוג "Web application" (לא iOS/Android)');
        console.log('');
        console.log('[GoogleSignIn] 📋 שלב 1: Authorized JavaScript Origins');
        console.log('[GoogleSignIn]    Go to: https://console.cloud.google.com/apis/credentials');
        console.log(`[GoogleSignIn]    Click on Client ID: ${googleClientId}`);
        console.log('[GoogleSignIn]    Under "Authorized JavaScript origins", ADD BOTH:');
        console.log(`[GoogleSignIn]    - ${currentOrigin} (with port)`);
        console.log('[GoogleSignIn]    - http://localhost (without port)');
        console.log('[GoogleSignIn]    ⚠️  חשוב: ודא שאין רווחים או תווים נוספים');
        console.log('[GoogleSignIn]    Click "Save" and wait 10-30 seconds');
        console.log('');
        console.log('[GoogleSignIn] 📋 שלב 2: OAuth Consent Screen');
        console.log('[GoogleSignIn]    Go to: https://console.cloud.google.com/apis/credentials/consent');
        console.log('[GoogleSignIn]    Check "Publishing status":');
        console.log('[GoogleSignIn]    - If "Testing" → Add your email as a test user');
        console.log('[GoogleSignIn]    - Or change to "In production" (requires verification)');
        console.log('[GoogleSignIn]    ⚠️  חשוב: אם זה "Testing", רק test users יכולים להתחבר');
        console.log('');
        console.log('[GoogleSignIn] 📋 שלב 3: בדיקת Project');
        console.log('[GoogleSignIn]    ודא שאתה בפרויקט הנכון ב-Google Cloud Console');
        console.log('[GoogleSignIn]    Project ID מ-Firebase: linkup-app-df18d');
        console.log('[GoogleSignIn]    ודא שה-OAuth Client ID שייך לאותו פרויקט');
        console.log('');
        console.log('[GoogleSignIn] 📋 שלב 4: Clear Cache & Test');
        console.log('[GoogleSignIn]    - Clear browser cache (Ctrl+Shift+Delete)');
        console.log('[GoogleSignIn]    - Try incognito/private window');
        console.log('[GoogleSignIn]    - Disable browser extensions (ad blockers)');
        console.log('[GoogleSignIn] ========================================');
        
        // ניקוי הכפתור הקודם אם יש
        buttonRef.current.innerHTML = '';
        
        try {
          console.log('[GoogleSignIn] 🎨 Attempting to render button...');
          
          // ניסיון עם GoogleOneTap במקום renderButton (אם renderButton נכשל)
          // אבל קודם ננסה renderButton
          try {
            window.google!.accounts.id.renderButton(buttonRef.current, {
              theme: 'outline',
              size: 'large',
              text: 'signin_with',
              width: 300,
            });
            console.log('[GoogleSignIn] ✅ Button rendered successfully');
          } catch (renderErr) {
            console.error('[GoogleSignIn] ❌ renderButton failed, trying alternative approach...');
            console.error('[GoogleSignIn] Error:', renderErr);
            const renderMsg = renderErr instanceof Error ? renderErr.message : String(renderErr);
            const isOriginError = /origin|not allowed|403|client id/i.test(renderMsg);
            if (isOriginError && onError) {
              const originMsg = `ה-origin לא מורשה ב-Google. הוסף בדיוק את הכתובת הזו ב-Google Cloud Console → Credentials → ה-Client ID → Authorized JavaScript origins: ${currentOrigin}`;
              onError(originMsg);
            }
            // אם renderButton נכשל, ננסה ליצור כפתור ידני עם GoogleOneTap
            if (buttonRef.current) {
              buttonRef.current.innerHTML = `
                <button 
                  id="google-signin-button" 
                  style="
                    width: 100%;
                    padding: 0.75rem 1rem;
                    font-size: 1rem;
                    font-weight: 500;
                    border: 1px solid #d1d5db;
                    border-radius: 0.5rem;
                    background-color: #fff;
                    color: #374151;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                  "
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  התחבר עם Google
                </button>
              `;
              
              const manualButton = buttonRef.current.querySelector('#google-signin-button');
              if (manualButton) {
                manualButton.addEventListener('click', () => {
                  console.log('[GoogleSignIn] Manual button clicked, trying GoogleOneTap...');
                  window.google!.accounts.id.prompt((notification) => {
                    if (notification.isNotDisplayed || notification.isSkippedMoment) {
                      console.error('[GoogleSignIn] GoogleOneTap not available:', notification);
                      if (onError) {
                        onError('Google Sign-In לא זמין. בדוק שה-origin מוגדר ב-Google Cloud Console.');
                      }
                    }
                  });
                });
              }
            }
            
            throw renderErr;
          }
        } catch (renderErr) {
          console.error('[GoogleSignIn] ❌ Button rendering error:', renderErr);
          if (renderErr instanceof Error) {
            console.error('[GoogleSignIn] Error name:', renderErr.name);
            console.error('[GoogleSignIn] Error message:', renderErr.message);
            console.error('[GoogleSignIn] Error stack:', renderErr.stack);
          }
          // לא זורקים שגיאה כאן כדי שהכפתור הידני יוכל לעבוד
        }
      }
    } catch (err) {
      console.error('[GoogleSignIn] ❌ Google Sign-In button rendering error:', err);
      const currentOrigin = window.location.origin;
      console.error('[GoogleSignIn] Current origin:', currentOrigin);
      console.error('[GoogleSignIn] Client ID:', googleClientId);
      console.error('[GoogleSignIn] Please verify in Google Cloud Console:');
      console.error('  1. Go to APIs & Services > Credentials');
      console.error('  2. Click on your OAuth Client ID');
      console.error(`  3. Under "Authorized JavaScript origins", ensure "${currentOrigin}" is listed`);
      console.error('  4. Click "Save" and wait 10-30 seconds');
      
      if (onError) {
        onError(`שגיאה ביצירת כפתור Google Sign-In. Origin: ${currentOrigin}. בדוק שה-origin מוגדר ב-Google Cloud Console.`);
      }
    }
  }, [scriptLoaded, initialized, disabled, onError]);

  if (!scriptLoaded) {
    return (
      <div
        ref={buttonRef}
        style={{
          width: '100%',
          minHeight: '40px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {loading ? 'מתחבר...' : 'טוען Google Sign-In...'}
      </div>
    );
  }

  return (
    <div
      ref={buttonRef}
      style={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        opacity: disabled ? 0.6 : 1,
        pointerEvents: disabled ? 'none' : 'auto',
      }}
    />
  );
}
