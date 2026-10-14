import { useEffect, useRef, useState } from "react";
import "./App.css";

function numericValue(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatMoney(value) {
  const number = numericValue(value);
  if (number === null) return "--";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(number);
}

function formatCompact(value) {
  const number = numericValue(value);
  if (number === null) return "--";
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(number);
}

function formatPercent(value) {
  const number = numericValue(value);
  if (number === null) return "--";
  return `${number > 0 ? "+" : ""}${number.toFixed(2)}%`;
}

function formatTimestamp(value) {
  if (value === null || value === undefined || value === "") return "Saved snapshot";
  const number = numericValue(value);
  const date = new Date(number === null ? value : number < 1e12 ? number * 1000 : number);
  if (Number.isNaN(date.getTime())) return "Saved snapshot";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function QuoteCard({ quote }) {
  const change = numericValue(quote.change);
  const changePercentage = numericValue(quote.changePercentage);
  const direction = (change ?? changePercentage ?? 0) >= 0 ? "positive" : "negative";

  return (
    <article className="quote-card">
      <div className="quote-card-heading">
        <div>
          <span className="symbol-label">{quote.symbol || "--"}</span>
          <p className="exchange-label">{quote.exchange || "Market quote"}</p>
        </div>
        <span className={`change-pill ${direction}`}>
          {change === null ? "" : `${change > 0 ? "+" : ""}${formatMoney(change)} / `}
          {formatPercent(quote.changePercentage)}
        </span>
      </div>

      <div className="company-price">
        <div>
          <h2>{quote.name || quote.symbol || "Saved quote"}</h2>
          <p>{formatTimestamp(quote.timestamp)}</p>
        </div>
        <strong>{formatMoney(quote.price)}</strong>
      </div>

      <dl className="quote-metrics">
        <div><dt>Open</dt><dd>{formatMoney(quote.open)}</dd></div>
        <div><dt>Previous close</dt><dd>{formatMoney(quote.previousClose)}</dd></div>
        <div><dt>Day range</dt><dd>{formatMoney(quote.dayLow)} <span>to</span> {formatMoney(quote.dayHigh)}</dd></div>
        <div><dt>52-week range</dt><dd>{formatMoney(quote.yearLow)} <span>to</span> {formatMoney(quote.yearHigh)}</dd></div>
        <div><dt>Volume</dt><dd>{formatCompact(quote.volume)}</dd></div>
        <div><dt>Market cap</dt><dd>{formatCompact(quote.marketCap)}</dd></div>
      </dl>
    </article>
  );
}

function loadGoogleIdentity() {
  if (window.google?.accounts?.id) return Promise.resolve();

  return new Promise((resolve, reject) => {
    let script = document.querySelector('script[data-google-identity="true"]');
    if (!script) {
      script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.dataset.googleIdentity = "true";
      document.head.appendChild(script);
    }

    script.addEventListener("load", () => {
      if (window.google?.accounts?.id) resolve();
      else reject(new Error("Google sign-in could not be loaded."));
    }, { once: true });
    script.addEventListener("error", () => reject(new Error("Google sign-in could not be loaded.")), { once: true });
  });
}

function SignInView({ initialError, onSignedIn }) {
  const [error, setError] = useState(initialError);
  const [submitting, setSubmitting] = useState(false);
  const [googleStatus, setGoogleStatus] = useState("loading");
  const googleButtonRef = useRef(null);
  const onSignedInRef = useRef(onSignedIn);
  onSignedInRef.current = onSignedIn;

  useEffect(() => {
    let cancelled = false;

    async function initializeGoogleSignIn() {
      try {
        const configResponse = await fetch("/auth/config", { credentials: "same-origin" });
        const config = await configResponse.json().catch(() => ({}));
        if (!configResponse.ok) throw new Error(config.detail || "Sign-in configuration is unavailable.");
        if (!config.google_client_id) {
          if (!cancelled) setGoogleStatus("unconfigured");
          return;
        }

        await loadGoogleIdentity();
        if (cancelled) return;

        window.google.accounts.id.initialize({
          client_id: config.google_client_id,
          callback: async ({ credential }) => {
            if (!credential) {
              setError("Google sign-in was cancelled.");
              return;
            }

            setError("");
            setSubmitting(true);
            try {
              const response = await fetch("/auth/google", {
                method: "POST",
                credentials: "same-origin",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ credential }),
              });
              const payload = await response.json().catch(() => ({}));
              if (!response.ok) {
                throw new Error(payload.detail || `Google sign-in failed with HTTP ${response.status}.`);
              }
              onSignedInRef.current(payload);
            } catch (googleError) {
              setError(googleError.message || "Google sign-in is not available right now.");
            } finally {
              setSubmitting(false);
            }
          },
          auto_select: false,
          cancel_on_tap_outside: true,
        });

        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: "outline",
          size: "large",
          type: "standard",
          text: "continue_with",
          shape: "rectangular",
          logo_alignment: "left",
          width: Math.min(320, Math.floor(googleButtonRef.current.clientWidth || 320)),
        });
        setGoogleStatus("ready");
      } catch (googleError) {
        if (!cancelled) {
          setError(googleError.message || "Google sign-in could not be initialized.");
          setGoogleStatus("unavailable");
        }
      }
    }

    initializeGoogleSignIn();
    return () => {
      cancelled = true;
      window.google?.accounts?.id?.cancel();
    };
  }, []);

  return (
    <main className="auth-content">
      <section className="signin-form">
        <span className="eyebrow">PRIVATE MARKET WORKSPACE</span>
        <h1>Sign in with Google</h1>
        <p className="signin-intro">Use your Google account to access your saved market snapshots.</p>

        <div className={submitting ? "google-button pending" : "google-button"} ref={googleButtonRef} />
        {googleStatus === "loading" && <p className="google-status" role="status">Preparing secure sign-in...</p>}
        {googleStatus === "unconfigured" && (
          <p className="google-status" role="status">Google sign-in is not configured for this site yet.</p>
        )}
        {googleStatus === "unavailable" && (
          <p className="google-status" role="status">Google sign-in is temporarily unavailable. Please try again later.</p>
        )}

        {error && <p className="signin-error" role="alert">{error}</p>}
        {submitting && <p className="google-status" role="status">Signing you in...</p>}
      </section>
    </main>
  );
}

export default function App() {
  const [authStatus, setAuthStatus] = useState("checking");
  const [user, setUser] = useState(null);
  const [authError, setAuthError] = useState("");
  const [quotes, setQuotes] = useState([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [status, setStatus] = useState("loading");
  const [reloadKey, setReloadKey] = useState(0);
  const [error, setError] = useState("");
  const [adminMessage, setAdminMessage] = useState("");
  const [activeView, setActiveView] = useState("market");

  useEffect(() => {
    let cancelled = false;

    async function checkSession() {
      try {
        const response = await fetch("/auth/me", { credentials: "same-origin" });
        if (response.status === 401) {
          if (!cancelled) setAuthStatus("anonymous");
          return;
        }
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.detail || `Session check failed with HTTP ${response.status}.`);
        }
        if (!cancelled) {
          setUser(payload);
          setAuthStatus("authenticated");
        }
      } catch (sessionError) {
        if (!cancelled) {
          setAuthError(sessionError.message || "Could not connect to the sign-in service.");
          setAuthStatus("anonymous");
        }
      }
    }

    checkSession();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadQuotes() {
      setStatus("loading");
      setError("");
      try {
        const response = await fetch("/quotes?limit=100");
        const payload = await response.json().catch(() => null);
        if (response.status === 401) {
          if (!cancelled) {
            setUser(null);
            setAuthStatus("anonymous");
          }
          return;
        }
        if (!response.ok) {
          throw new Error(payload?.detail || `The API returned HTTP ${response.status}.`);
        }
        if (!Array.isArray(payload)) {
          throw new Error("The quotes endpoint returned an unexpected response.");
        }
        if (!cancelled) {
          setQuotes(payload);
          setActiveIndex(0);
          setStatus("ready");
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError.message || "Could not connect to the API.");
          setStatus("error");
        }
      }
    }

    if (authStatus !== "authenticated") return undefined;
    loadQuotes();
    return () => { cancelled = true; };
  }, [authStatus, reloadKey]);

  function moveQuote(direction) {
    setActiveIndex((index) => (index + direction + quotes.length) % quotes.length);
  }

  async function signOut() {
    setAuthError("");
    try {
      const response = await fetch("/auth/logout", {
        method: "POST",
        credentials: "same-origin",
      });
      if (!response.ok) {
        throw new Error(`Sign-out failed with HTTP ${response.status}.`);
      }
      setUser(null);
      setQuotes([]);
      setAuthStatus("anonymous");
    } catch (signOutError) {
      setAuthError(signOutError.message || "Could not sign out.");
    }
  }

  async function loadAdminSummary() {
    try {
      const response = await fetch("/auth/admin/summary", { credentials: "same-origin" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || `Admin access failed with HTTP ${response.status}.`);
      }
      setAdminMessage(`Admin access confirmed for ${payload.email}.`);
    } catch (adminError) {
      setAdminMessage(adminError.message || "Admin access is unavailable.");
    }
  }

  const activeQuote = quotes[activeIndex];

  return (
    <div className="app-shell">
      <header className="masthead">
        <div className="brand-lockup">
          <span className="brand-mark">HB</span>
          <span className="brand-name">REAL TIME TRADING</span>
        </div>
        <div className="masthead-meta">
          <span className="live-indicator" />
          <span>LOCAL MARKET DESK</span>
        </div>
      </header>

      {authStatus === "checking" ? (
        <main className="auth-content" role="status">Checking your session...</main>
      ) : authStatus !== "authenticated" ? (
        <SignInView
          key={authError}
          initialError={authError}
          onSignedIn={(account) => {
            setAuthError("");
            setUser(account);
            setAuthStatus("authenticated");
          }}
        />
      ) : (
        <div className="workspace">
          <aside className="sidebar">
            <div className="profile-summary">
              <div className="profile-avatar">HB</div>
              <div>
                <span className="eyebrow">PROFILE</span>
                <strong>Market desk</strong>
                <span className="profile-caption">{user?.email}</span>
              </div>
            </div>

            <nav className="side-nav" aria-label="Profile navigation">
              <button className={activeView === "market" ? "nav-item active" : "nav-item"} type="button" onClick={() => setActiveView("market")} aria-current={activeView === "market" ? "page" : undefined}>
                <span className="nav-glyph market-glyph" aria-hidden="true" />
                <span>Market updates</span>
                {activeView === "market" && <span className="nav-current" aria-hidden="true" />}
              </button>
              <button className={activeView === "account" ? "nav-item active" : "nav-item"} type="button" onClick={() => setActiveView("account")} aria-current={activeView === "account" ? "page" : undefined}>
                <span className="nav-glyph profile-glyph" aria-hidden="true" />
                <span>My account</span>
                {activeView === "account" && <span className="nav-current" aria-hidden="true" />}
              </button>
              {user?.role === "admin" && (
                <button className="nav-item" type="button" onClick={loadAdminSummary}>
                  <span className="nav-glyph profile-glyph" aria-hidden="true" />
                  <span>Admin tools</span>
                </button>
              )}
            </nav>

            {adminMessage && <div className="sidebar-note"><span>{adminMessage}</span></div>}

            <div className="sidebar-note">
              <span className="note-rule" />
              <span>Saved snapshots</span>
              <strong>MongoDB</strong>
              <button className="signout-button" type="button" onClick={signOut}>Sign out</button>
              {authError && <span className="signout-error" role="alert">{authError}</span>}
            </div>
          </aside>

          <main className="main-content">
            {activeView === "account" ? (
              <section className="account-view">
                <div className="page-heading">
                  <span className="eyebrow">ACCOUNT</span>
                  <h1>Your account</h1>
                  <p>Your sign-in identity and workspace access.</p>
                </div>
                <dl className="account-details">
                  <div><dt>Email</dt><dd>{user?.email}</dd></div>
                  <div><dt>Sign-in provider</dt><dd>Google</dd></div>
                  <div><dt>Access</dt><dd>{user?.role === "admin" ? "Administrator" : "Member"}</dd></div>
                </dl>
              </section>
            ) : <section className="market-view">
              <div className="page-heading">
                <span className="eyebrow">SAVED MARKET DATA</span>
                <h1>Your market updates</h1>
                <p>Quote snapshots already collected and stored in MongoDB.</p>
              </div>

              <div className="data-toolbar">
                <div className="collection-label">
                  <span className="collection-mark" aria-hidden="true" />
                  <span>integracao_db <b>/</b> respostas_api</span>
                </div>
                <button
                  className="refresh-button"
                  onClick={() => setReloadKey((key) => key + 1)}
                  disabled={status === "loading"}
                >
                  <span className={status === "loading" ? "refresh-glyph spinning" : "refresh-glyph"} aria-hidden="true" />
                  Refresh saved quotes
                </button>
              </div>

              {status === "loading" && (
                <div className="message-panel" role="status">
                  <span className="loading-mark" />
                  <p>Loading saved quotes...</p>
                </div>
              )}

              {status === "error" && (
                <div className="message-panel error-panel" role="alert">
                  <span className="message-kicker">CONNECTION ISSUE</span>
                  <h2>Saved quotes are unavailable</h2>
                  <p>{error} Check that MONGO_URI is set and MongoDB is reachable, then refresh.</p>
                  <button className="retry-button" onClick={() => setReloadKey((key) => key + 1)}>Try again</button>
                </div>
              )}

              {status === "ready" && quotes.length === 0 && (
                <div className="message-panel empty-panel">
                  <span className="message-kicker">NO SAVED QUOTES</span>
                  <h2>Your collection is empty</h2>
                  <p>Once your quote script saves records to MongoDB, they will appear here.</p>
                </div>
              )}

              {status === "ready" && quotes.length > 0 && (
                <>
                  <div className="carousel" aria-label="Saved quote carousel">
                    <button
                      className="carousel-arrow previous"
                      onClick={() => moveQuote(-1)}
                      disabled={quotes.length < 2}
                      aria-label="Previous quote"
                    ><span className="chevron" /></button>
                    <QuoteCard quote={activeQuote} />
                    <button
                      className="carousel-arrow next"
                      onClick={() => moveQuote(1)}
                      disabled={quotes.length < 2}
                      aria-label="Next quote"
                    ><span className="chevron" /></button>
                  </div>
                  <div className="carousel-footer">
                    <div className="carousel-progress" aria-label={`Quote ${activeIndex + 1} of ${quotes.length}`}>
                      {quotes.map((quote, index) => (
                        <button
                          key={quote._id || `${quote.symbol}-${index}`}
                          className={index === activeIndex ? "progress-mark current" : "progress-mark"}
                          onClick={() => setActiveIndex(index)}
                          aria-label={`Show ${quote.symbol || `quote ${index + 1}`}`}
                        />
                      ))}
                    </div>
                    <span className="carousel-count">{String(activeIndex + 1).padStart(2, "0")} <b>/</b> {String(quotes.length).padStart(2, "0")}</span>
                  </div>
                </>
              )}
            </section>}
          </main>
        </div>
      )}
    </div>
  );
}