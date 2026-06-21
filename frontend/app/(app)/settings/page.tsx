"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { getAuditLog } from "@/lib/api/auditLog";
import { formatRelativeTime } from "@/lib/utils/formatDate";
import { ApiError } from "@/types/api";
import type { AuditLogEntry } from "@/types/auditLog";

type Tab = "account" | "activity" | "notifications" | "plan" | "api";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("account");

  return (
    <div className="w-full max-w-[800px]">
      <h1 className="font-sans text-[22px] font-semibold text-[#1A1A18] mb-6">Settings</h1>

      <div className="flex items-center border-b border-[#E3DFD8] mb-8">
        {(["account", "activity", "notifications", "plan", "api"] as Tab[]).map((tab) => {
          const labels: Record<Tab, string> = {
            account: "Account",
            activity: "Activity",
            notifications: "Notifications",
            plan: "Plan",
            api: "API Access",
          };
          const isActive = activeTab === tab;
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 font-sans text-[14px] transition-colors ${
                isActive
                  ? "font-semibold text-[#1A1A18] border-b-2 border-[#1C3558]"
                  : "text-[#7A786F] border-b-2 border-transparent hover:text-[#1A1A18]"
              }`}
            >
              {labels[tab]}
            </button>
          );
        })}
      </div>

      <div className="flex flex-col gap-8">
        {activeTab === "account" && <AccountTab />}
        {activeTab === "activity" && <ActivityTab />}
        {activeTab === "notifications" && <NotificationsTab />}
        {activeTab === "plan" && <PlanTab />}
        {activeTab === "api" && (
          <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6">
            <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-4">API ACCESS</h2>
            <p className="font-sans text-[14px] text-[#7A786F]">API access is available on the Pro plan.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AccountTab() {
  const { user, isLoading } = useAuth();
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <>
      <section className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6">
        <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-6">PROFILE</h2>
        <div className="flex flex-col md:flex-row gap-6 mb-6">
          <div className="flex-1 flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">Full Name</label>
            {isLoading ? (
              <Skeleton className="h-[44px] rounded-[6px]" />
            ) : (
              <input
                type="text"
                defaultValue={user?.full_name ?? ""}
                className="h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border border-[#E3DFD8] focus:border-[#1C3558] rounded-[6px] outline-none"
              />
            )}
          </div>
          <div className="flex-1 flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">Work Email</label>
            {isLoading ? (
              <Skeleton className="h-[44px] rounded-[6px]" />
            ) : (
              <input
                type="email"
                defaultValue={user?.email ?? ""}
                disabled
                className="h-[44px] px-3 font-sans text-[14px] text-[#7A786F] bg-[#F6F4EF] border border-[#E3DFD8] rounded-[6px] outline-none cursor-not-allowed"
              />
            )}
            <span className="font-sans text-[11px] text-[#B0ADA7] italic mt-2">
              To change your email, contact support.
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="w-[140px]">
            <Button variant="secondary" className="w-full" disabled>Save Changes</Button>
          </div>
          <span className="font-sans text-[11px] text-[#B0ADA7] italic">Profile updates not yet available.</span>
        </div>
      </section>

      <section className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6">
        <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-6">PASSWORD</h2>
        <div className="flex flex-col gap-4 mb-6 max-w-[400px]">
          <div className="flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">Current Password</label>
            <div className="relative">
              <input
                type={showCurrent ? "text" : "password"}
                className={`w-full h-[44px] pl-3 pr-12 font-sans text-[14px] text-[#1A1A18] bg-[#FFFFFF] border border-[#E3DFD8] focus:border-[#1C3558] rounded-[6px] outline-none transition-colors duration-fast ease-out ${!showCurrent ? 'tracking-widest' : ''}`}
              />
              <button 
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-3 top-1/2 -translate-y-1/2 font-sans text-[12px] text-[#1C3558] select-none hover:underline focus-visible:outline-none focus-visible:underline"
              >
                {showCurrent ? "Hide" : "Show"}
              </button>
            </div>
          </div>
          <div className="flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">New Password</label>
            <div className="relative">
              <input
                type={showNew ? "text" : "password"}
                className={`w-full h-[44px] pl-3 pr-12 font-sans text-[14px] text-[#1A1A18] bg-[#FFFFFF] border border-[#E3DFD8] focus:border-[#1C3558] rounded-[6px] outline-none transition-colors duration-fast ease-out ${!showNew ? 'tracking-widest' : ''}`}
              />
              <button 
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-3 top-1/2 -translate-y-1/2 font-sans text-[12px] text-[#1C3558] select-none hover:underline focus-visible:outline-none focus-visible:underline"
              >
                {showNew ? "Hide" : "Show"}
              </button>
            </div>
          </div>
          <div className="flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">Confirm New Password</label>
            <div className="relative">
              <input
                type={showConfirm ? "text" : "password"}
                className={`w-full h-[44px] pl-3 pr-12 font-sans text-[14px] text-[#1A1A18] bg-[#FFFFFF] border border-[#E3DFD8] focus:border-[#1C3558] rounded-[6px] outline-none transition-colors duration-fast ease-out ${!showConfirm ? 'tracking-widest' : ''}`}
              />
              <button 
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-1/2 -translate-y-1/2 font-sans text-[12px] text-[#1C3558] select-none hover:underline focus-visible:outline-none focus-visible:underline"
              >
                {showConfirm ? "Hide" : "Show"}
              </button>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <Button variant="secondary" disabled>Update Password</Button>
          <span className="font-sans text-[11px] text-[#B0ADA7] italic">Password changes not yet available.</span>
        </div>
      </section>

      <section className="bg-[#FFFFFF] border border-[#B03028] rounded-[8px] p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-2">DANGER ZONE</h2>
          <div className="font-sans text-[14px] font-semibold text-[#B03028] mb-1">Delete Account</div>
          <p className="font-sans text-[13px] text-[#7A786F] leading-[1.6]">
            Permanently delete your account and all associated data. This action cannot be reversed.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1 self-start md:self-auto">
          <button
            disabled
            className="h-[44px] px-6 font-sans text-[14px] font-semibold text-[#B0ADA7] bg-[#F6F4EF] rounded-[6px] whitespace-nowrap cursor-not-allowed"
          >
            Delete Account
          </button>
          <span className="font-sans text-[11px] text-[#B0ADA7] italic">Contact support to delete your account.</span>
        </div>
      </section>
    </>
  );
}

const ACTION_LABELS: Record<string, string> = {
  register: "Account created",
  login: "Signed in",
  logout: "Signed out",
  analysis_run: "Ran analysis",
  watchlist_add: "Added to watchlist",
  watchlist_remove: "Removed from watchlist",
};

function describeAction(entry: AuditLogEntry): string {
  const label = ACTION_LABELS[entry.action] ?? entry.action;
  const ticker = entry.detail && typeof entry.detail.ticker === "string" ? entry.detail.ticker : null;
  return ticker ? `${label} — ${ticker}` : label;
}

function ActivityTab() {
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAuditLog()
      .then((data) => { if (!cancelled) setEntries(data); })
      .catch((err) => { if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load activity."); });
    return () => { cancelled = true; };
  }, []);

  return (
    <section className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
      <div className="p-6 pb-4">
        <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-2">ACCOUNT ACTIVITY</h2>
        <p className="font-sans text-[12px] text-[#B0ADA7]">Security-relevant actions on your account, most recent first.</p>
      </div>

      {error ? (
        <div className="px-6 pb-6">
          <div className="font-sans text-[13px] text-[#B03028]">{error}</div>
        </div>
      ) : entries === null ? (
        <div className="flex flex-col">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="flex items-center px-6 h-[52px] border-t border-[#E3DFD8]">
              <Skeleton className="w-[40%] h-[14px] mr-4" />
              <Skeleton className="w-[20%] h-[14px] mr-4" />
              <Skeleton className="w-[20%] h-[14px]" />
            </div>
          ))}
        </div>
      ) : entries.length === 0 ? (
        <div className="px-6 pb-6">
          <p className="font-sans text-[13px] text-[#7A786F]">No activity recorded yet.</p>
        </div>
      ) : (
        <div className="flex flex-col divide-y divide-[#E3DFD8]">
          {entries.map((entry) => (
            <div key={entry.id} className="px-6 py-4 flex items-center justify-between gap-4">
              <div className="font-sans text-[14px] text-[#1A1A18]">{describeAction(entry)}</div>
              <div className="flex items-center gap-4 shrink-0">
                {entry.ip_address && (
                  <span className="font-mono text-[12px] text-[#B0ADA7]">{entry.ip_address}</span>
                )}
                <span className="font-sans text-[12px] text-[#7A786F]">{formatRelativeTime(entry.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function NotificationsTab() {
  const [toggles, setToggles] = useState({
    watchlist: true,
    flags: true,
    digest: false,
    analysis: true,
  });

  const toggleState = (key: keyof typeof toggles) => {
    setToggles(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <section className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden">
      <div className="p-6 pb-4">
        <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-2">ALERT PREFERENCES</h2>
        <p className="font-sans text-[12px] text-[#B0ADA7] italic">Preferences are not yet persisted — notification delivery is coming soon.</p>
      </div>
      <div className="flex flex-col divide-y divide-[#E3DFD8]">
        
        <div className="px-6 py-5 flex items-center justify-between">
          <div className="pr-4">
            <div className="font-sans text-[14px] font-semibold text-[#1A1A18] mb-1">Watchlist integrity score changes</div>
            <div className="font-sans text-[13px] text-[#7A786F]">Notify when any watched company score changes by ±10</div>
          </div>
          <Toggle isOn={toggles.watchlist} onClick={() => toggleState("watchlist")} />
        </div>

        <div className="px-6 py-5 flex items-center justify-between">
          <div className="pr-4">
            <div className="font-sans text-[14px] font-semibold text-[#1A1A18] mb-1">New red flags detected</div>
            <div className="font-sans text-[13px] text-[#7A786F]">Notify when a new governance or financial flag is added</div>
          </div>
          <Toggle isOn={toggles.flags} onClick={() => toggleState("flags")} />
        </div>

        <div className="px-6 py-5 flex items-center justify-between">
          <div className="pr-4">
            <div className="font-sans text-[14px] font-semibold text-[#1A1A18] mb-1">Weekly digest</div>
            <div className="font-sans text-[13px] text-[#7A786F]">Summary of all watchlist companies every Monday</div>
          </div>
          <Toggle isOn={toggles.digest} onClick={() => toggleState("digest")} />
        </div>

        <div className="px-6 py-5 flex items-center justify-between">
          <div className="pr-4">
            <div className="font-sans text-[14px] font-semibold text-[#1A1A18] mb-1">Analysis complete</div>
            <div className="font-sans text-[13px] text-[#7A786F]">Notify when an investigation finishes running</div>
          </div>
          <Toggle isOn={toggles.analysis} onClick={() => toggleState("analysis")} />
        </div>

      </div>
    </section>
  );
}

function Toggle({ isOn, onClick }: { isOn: boolean; onClick: () => void }) {
  return (
    <button 
      onClick={onClick}
      className={`relative w-[36px] h-[20px] rounded-[10px] transition-colors shrink-0 ${isOn ? "bg-[#1C3558]" : "bg-[#E3DFD8]"}`}
    >
      <div 
        className={`absolute top-[2px] w-[16px] h-[16px] bg-[#FFFFFF] rounded-full transition-all duration-200 ease-in-out ${isOn ? "left-[18px]" : "left-[2px]"}`} 
      />
    </button>
  );
}

function PlanTab() {
  const { user } = useAuth();
  const tierLabel = user?.tier ? user.tier.charAt(0).toUpperCase() + user.tier.slice(1) : "Free";

  return (
    <>
      <section className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6">
        <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-4">CURRENT PLAN</h2>
        <div className="font-sans text-[20px] font-semibold text-[#1A1A18] mb-1">{tierLabel}</div>
        <p className="font-sans text-[13px] text-[#7A786F] mb-6">5 company analyses per month. Watchlist limited to 10.</p>

        <div className="flex flex-col items-start gap-2">
          <Button variant="primary" disabled>Upgrade to Pro</Button>
          <span className="font-sans text-[12px] text-[#7A786F]">Unlimited analyses, full report export, API access. Coming soon.</span>
        </div>
      </section>

      <section className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-4">PRO PLAN</h2>
          <div className="flex items-baseline gap-2 mb-4">
            <span className="font-mono text-[24px] font-bold text-[#1A1A18]">$19</span>
            <span className="font-sans text-[14px] text-[#7A786F]">/month</span>
          </div>
          <ul className="flex flex-col gap-2 font-sans text-[14px] text-[#1A1A18]">
            <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span>Unlimited company analyses</li>
            <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span>Full PDF report export</li>
            <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span>API access</li>
            <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span>Priority analysis queue</li>
            <li className="flex"><span className="text-[#B0ADA7] mr-2">—</span>Historical comparison (12 months)</li>
          </ul>
        </div>
        <div className="self-start md:self-end flex flex-col items-end gap-1">
          <Button variant="primary" disabled>Upgrade to Pro</Button>
          <span className="font-sans text-[11px] text-[#B0ADA7] italic">Coming soon.</span>
        </div>
      </section>
    </>
  );
}
