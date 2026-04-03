import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../store/auth";
import { useToast } from "../components/Toast";
import Logo from "../components/Logo";

interface BrokerState {
  id: string;
  name: string;
  color: string;
  connected: boolean;
  lastSync: string | null;
  syncing: boolean;
  showForm: boolean;
  apiKey: string;
  accessToken: string;
  connecting: boolean;
}

const INITIAL_BROKERS: BrokerState[] = [
  {
    id: "zerodha",
    name: "Zerodha",
    color: "#387ed1",
    connected: false,
    lastSync: null,
    syncing: false,
    showForm: false,
    apiKey: "",
    accessToken: "",
    connecting: false,
  },
  {
    id: "angelone",
    name: "Angel One",
    color: "#e85d3a",
    connected: false,
    lastSync: null,
    syncing: false,
    showForm: false,
    apiKey: "",
    accessToken: "",
    connecting: false,
  },
];

function BrokerIcon({ name, color }: { name: string; color: string }) {
  return (
    <div
      className="w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold shrink-0"
      style={{ backgroundColor: color + "1a", color }}
      aria-hidden="true"
    >
      {name.charAt(0)}
    </div>
  );
}

export default function BrokerConnect() {
  const logout = useAuth((s) => s.logout);
  const { toast } = useToast();
  const [brokers, setBrokers] = useState<BrokerState[]>(INITIAL_BROKERS);

  useEffect(() => {
    document.title = "Connect Broker — TradeLoop";
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get("/broker/connections");
        if (cancelled) return;
        setBrokers((prev) =>
          prev.map((b) => {
            const conn = (data as { broker_id: string; last_sync: string | null }[]).find(
              (c) => c.broker_id === b.id
            );
            return conn
              ? { ...b, connected: true, lastSync: conn.last_sync }
              : b;
          })
        );
      } catch {
        // API not yet available — keep defaults
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const updateBroker = (id: string, patch: Partial<BrokerState>) => {
    setBrokers((prev) =>
      prev.map((b) => (b.id === id ? { ...b, ...patch } : b))
    );
  };

  const handleConnect = async (broker: BrokerState) => {
    if (!broker.apiKey.trim() || !broker.accessToken.trim()) {
      toast("Please fill in both fields", "error");
      return;
    }
    updateBroker(broker.id, { connecting: true });
    try {
      await api.post("/broker/connect", {
        broker_id: broker.id,
        api_key: broker.apiKey,
        access_token: broker.accessToken,
      });
      updateBroker(broker.id, {
        connected: true,
        connecting: false,
        showForm: false,
        apiKey: "",
        accessToken: "",
        lastSync: null,
      });
      toast(`${broker.name} connected successfully`, "success");
    } catch {
      updateBroker(broker.id, { connecting: false });
      toast(`Failed to connect ${broker.name}`, "error");
    }
  };

  const handleDisconnect = async (broker: BrokerState) => {
    try {
      await api.delete(`/broker/connections/${broker.id}`);
      updateBroker(broker.id, { connected: false, lastSync: null });
      toast(`${broker.name} disconnected`, "success");
    } catch {
      toast(`Failed to disconnect ${broker.name}`, "error");
    }
  };

  const handleSync = async (broker: BrokerState) => {
    updateBroker(broker.id, { syncing: true });
    try {
      await api.post(`/broker/sync/${broker.id}`);
      updateBroker(broker.id, {
        syncing: false,
        lastSync: new Date().toISOString(),
      });
      toast(`${broker.name} synced successfully`, "success");
    } catch {
      updateBroker(broker.id, { syncing: false });
      toast(`Failed to sync ${broker.name}`, "error");
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav
        className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border"
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="max-w-3xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Logo linkTo="/" size="sm" />
          <div className="flex items-center gap-3">
            <Link
              to="/dashboard"
              className="text-xs text-gray-400 hover:text-white transition-colors"
            >
              Dashboard
            </Link>
            <Link
              to="/settings"
              className="text-xs text-gray-400 hover:text-white transition-colors"
            >
              Settings
            </Link>
            <button
              onClick={logout}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main
        className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-8"
        role="main"
        aria-label="Broker connections"
      >
        <div>
          <h1 className="text-2xl font-bold text-white">Connect Broker</h1>
          <p className="text-sm text-gray-500 mt-1">
            Link your trading account to automatically import trades.
          </p>
        </div>

        <div className="space-y-4">
          {brokers.map((broker) => (
            <section
              key={broker.id}
              className="card"
              aria-label={`${broker.name} broker connection`}
            >
              <div className="flex items-start gap-4">
                <BrokerIcon name={broker.name} color={broker.color} />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <h2 className="text-base font-semibold text-white">
                      {broker.name}
                    </h2>
                    <span
                      className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${
                        broker.connected
                          ? "bg-profit/10 text-profit"
                          : "bg-gray-800 text-gray-500"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          broker.connected ? "bg-profit" : "bg-gray-600"
                        }`}
                      />
                      {broker.connected ? "Connected" : "Disconnected"}
                    </span>
                  </div>

                  {broker.connected && broker.lastSync && (
                    <p className="text-xs text-gray-500 mt-1">
                      Last synced{" "}
                      {new Date(broker.lastSync).toLocaleString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  )}

                  {broker.connected && !broker.lastSync && (
                    <p className="text-xs text-gray-500 mt-1">
                      Connected — not yet synced
                    </p>
                  )}

                  <div className="flex items-center gap-2 mt-3 flex-wrap">
                    {broker.connected ? (
                      <>
                        <button
                          onClick={() => handleSync(broker)}
                          disabled={broker.syncing}
                          className="btn-primary !px-4 !py-2 text-xs"
                        >
                          {broker.syncing ? "Syncing..." : "Sync Now"}
                        </button>
                        <button
                          onClick={() => handleDisconnect(broker)}
                          className="px-4 py-2 rounded-lg text-xs font-medium border border-loss/30 text-loss hover:bg-loss/10 transition-colors"
                        >
                          Disconnect
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() =>
                          updateBroker(broker.id, {
                            showForm: !broker.showForm,
                          })
                        }
                        className="btn-primary !px-4 !py-2 text-xs"
                      >
                        {broker.showForm ? "Cancel" : "Connect"}
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Connection form */}
              {broker.showForm && !broker.connected && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleConnect(broker);
                  }}
                  className="mt-4 pt-4 border-t border-border space-y-3"
                  aria-label={`${broker.name} credentials form`}
                >
                  <div>
                    <label
                      htmlFor={`${broker.id}-api-key`}
                      className="block text-sm text-gray-400 mb-1.5"
                    >
                      API Key
                    </label>
                    <input
                      id={`${broker.id}-api-key`}
                      type="text"
                      value={broker.apiKey}
                      onChange={(e) =>
                        updateBroker(broker.id, { apiKey: e.target.value })
                      }
                      className="input-field"
                      placeholder={`Your ${broker.name} API key`}
                      autoComplete="off"
                      required
                    />
                  </div>
                  <div>
                    <label
                      htmlFor={`${broker.id}-access-token`}
                      className="block text-sm text-gray-400 mb-1.5"
                    >
                      Access Token
                    </label>
                    <input
                      id={`${broker.id}-access-token`}
                      type="password"
                      value={broker.accessToken}
                      onChange={(e) =>
                        updateBroker(broker.id, {
                          accessToken: e.target.value,
                        })
                      }
                      className="input-field"
                      placeholder="Paste your access token"
                      autoComplete="off"
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={broker.connecting}
                    className="btn-primary text-sm"
                  >
                    {broker.connecting
                      ? "Connecting..."
                      : `Connect ${broker.name}`}
                  </button>
                </form>
              )}
            </section>
          ))}
        </div>

        {/* Auto-sync info */}
        <section className="card" aria-label="Auto-sync information">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0 mt-0.5">
              <svg
                width={16}
                height={16}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-accent"
                aria-hidden="true"
              >
                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                <path d="M3 3v5h5" />
                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                <path d="M21 21v-5h-5" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-300">
                Automatic Sync
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                Trades are automatically imported every 5 minutes once your
                broker is connected. You can also trigger a manual sync at any
                time.
              </p>
            </div>
          </div>
        </section>

        {/* CSV fallback */}
        <section
          className="text-center py-4"
          aria-label="Manual upload alternative"
        >
          <p className="text-sm text-gray-500">
            Or{" "}
            <Link
              to="/upload"
              className="text-accent hover:underline font-medium"
            >
              upload a CSV manually
            </Link>
          </p>
        </section>
      </main>
    </div>
  );
}
