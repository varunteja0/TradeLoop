import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../store/auth";
import { useToast } from "../components/Toast";
import Logo from "../components/Logo";

const TIMEZONES = [
  { label: "UTC (±0:00)", offset: 0 },
  { label: "IST (+5:30)", offset: 330 },
  { label: "EST (−5:00)", offset: -300 },
  { label: "CST (−6:00)", offset: -360 },
  { label: "MST (−7:00)", offset: -420 },
  { label: "PST (−8:00)", offset: -480 },
  { label: "GMT (+0:00)", offset: 0 },
  { label: "CET (+1:00)", offset: 60 },
  { label: "EET (+2:00)", offset: 120 },
  { label: "JST (+9:00)", offset: 540 },
  { label: "AEST (+10:00)", offset: 600 },
  { label: "NZST (+12:00)", offset: 720 },
];

export default function Settings() {
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const updateProfile = useAuth((s) => s.updateProfile);
  const changePassword = useAuth((s) => s.changePassword);
  const { toast } = useToast();

  const [name, setName] = useState(user?.name || "");
  const [timezoneOffset, setTimezoneOffset] = useState(user?.timezone_offset ?? 0);
  const [profileSaving, setProfileSaving] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);

  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    document.title = "Settings — TradeLoop";
  }, []);

  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setTimezoneOffset(user.timezone_offset ?? 0);
    }
  }, [user]);

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSaving(true);
    try {
      await updateProfile({ name: name || undefined, timezone_offset: timezoneOffset });
      toast("Profile updated", "success");
    } catch {
      toast("Failed to update profile", "error");
    } finally {
      setProfileSaving(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      toast("New password must be at least 6 characters", "error");
      return;
    }
    setPasswordSaving(true);
    try {
      await changePassword(currentPassword, newPassword);
      toast("Password changed successfully", "success");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to change password";
      toast(msg, "error");
    } finally {
      setPasswordSaving(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const { data } = await api.get("/trades/export", { responseType: "blob" });
      const url = URL.createObjectURL(data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `tradeloop-export-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast("Trades exported successfully", "success");
    } catch {
      toast("Failed to export trades", "error");
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteAll = async () => {
    setDeleting(true);
    try {
      await api.delete("/trades");
      toast("All trades deleted", "success");
      setDeleteConfirm(false);
    } catch {
      toast("Failed to delete trades", "error");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Logo linkTo="/" size="sm" />
          <div className="flex items-center gap-3">
            <Link to="/dashboard" className="text-xs text-gray-400 hover:text-white transition-colors">
              Dashboard
            </Link>
            <button onClick={logout} className="text-xs text-gray-500 hover:text-gray-300">
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>

        {/* Account Info */}
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Account Info</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Email</span>
              <span className="text-gray-300">{user?.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Plan</span>
              <span className="text-accent capitalize">{user?.plan || "free"}</span>
            </div>
          </div>
        </section>

        {/* Profile */}
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Profile</h2>
          <form onSubmit={handleProfileSave} className="space-y-4">
            <div>
              <label htmlFor="settings-name" className="block text-sm text-gray-400 mb-1.5">
                Display Name
              </label>
              <input
                id="settings-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-field"
                placeholder="Your name"
                autoComplete="name"
              />
            </div>
            <div>
              <label htmlFor="settings-timezone" className="block text-sm text-gray-400 mb-1.5">
                Timezone
              </label>
              <select
                id="settings-timezone"
                value={timezoneOffset}
                onChange={(e) => setTimezoneOffset(Number(e.target.value))}
                className="input-field bg-bg-card"
              >
                {TIMEZONES.map((tz) => (
                  <option key={`${tz.label}-${tz.offset}`} value={tz.offset}>
                    {tz.label}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" className="btn-primary text-sm" disabled={profileSaving}>
              {profileSaving ? "Saving..." : "Save Profile"}
            </button>
          </form>
        </section>

        {/* Change Password */}
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Change Password</h2>
          <form onSubmit={handlePasswordChange} className="space-y-4">
            <div>
              <label htmlFor="current-password" className="block text-sm text-gray-400 mb-1.5">
                Current Password
              </label>
              <input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="input-field"
                required
                autoComplete="current-password"
              />
            </div>
            <div>
              <label htmlFor="new-password" className="block text-sm text-gray-400 mb-1.5">
                New Password
              </label>
              <input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input-field"
                required
                minLength={6}
                autoComplete="new-password"
              />
              <p className="text-xs text-gray-500 mt-1.5">Must be at least 6 characters.</p>
            </div>
            <button type="submit" className="btn-primary text-sm" disabled={passwordSaving}>
              {passwordSaving ? "Changing..." : "Change Password"}
            </button>
          </form>
        </section>

        {/* Data Management */}
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Data Management</h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-400 mb-2">
                Download all your trades as a CSV file.
              </p>
              <button
                onClick={handleExport}
                className="btn-secondary text-sm"
                disabled={exporting}
              >
                {exporting ? "Exporting..." : "Export All Trades"}
              </button>
            </div>

            <div className="border-t border-border pt-4">
              <h3 className="text-sm font-semibold text-loss mb-2">Danger Zone</h3>
              <p className="text-sm text-gray-400 mb-3">
                Permanently delete all your trade data. This action cannot be undone.
              </p>
              {deleteConfirm ? (
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleDeleteAll}
                    className="px-4 py-2 rounded-lg text-sm font-medium bg-loss text-white hover:bg-loss/80 transition-colors"
                    disabled={deleting}
                  >
                    {deleting ? "Deleting..." : "Yes, Delete Everything"}
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(false)}
                    className="text-sm text-gray-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setDeleteConfirm(true)}
                  className="px-4 py-2 rounded-lg text-sm font-medium border border-loss/30 text-loss hover:bg-loss/10 transition-colors"
                >
                  Delete All Trades
                </button>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
