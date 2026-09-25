import { Command, List, LogOut, Settings } from "lucide-react";
import { observer } from "mobx-react-lite";
import type { ReactElement } from "react";
import { Link, NavLink, Outlet } from "react-router";

import { supabaseClient } from "../api/lib/supabaseClient";
import InstallPrompt from "../components/InstallPrompt";
import OfflineBanner from "../components/OfflineBanner";
import Toast from "../components/Toast";
import UpdateBanner from "../components/UpdateBanner";
import Popover from "../design-system/components/Popover";
import NotificationsController from "../features/notifications/controllers/NotificationsController/NotificationsController";
import { useStore } from "../stores/StoreProvider";
import { cn } from "../utils/cn";
import * as Styles from "./styles";

interface NavItemProps {
  to: string;
  label: string;
  icon: ReactElement;
}

const NAV_ITEMS: NavItemProps[] = [
  { to: "/", label: "Capture", icon: <Command size={20} /> },
  { to: "/records", label: "Records", icon: <List size={20} /> },
  { to: "/settings", label: "Settings", icon: <Settings size={20} /> },
];

const AppShell = (): ReactElement => {
  const store = useStore();
  const { id, username, email, avatarUrl } = store.auth;
  // A Google-only account has no username until slice 3 gives it a way to
  // set one (04-implementation-plan.md section 4's contract on `profiles`);
  // fall back to the email's local part rather than show nothing.
  const displayName = username ?? email?.split("@")[0] ?? "Your account";
  const avatarLetter = displayName.charAt(0).toUpperCase() || "?";
  // RequireAuth renders AppShell as soon as the session is authenticated,
  // before GetMe resolves — `id` is null for that gap.
  const isProfileLoading = id === null;

  const handleSignOut = async (close: () => void): Promise<void> => {
    close();
    // RequireAuth's onAuthStateChange listener clears store.auth and
    // redirects to /sign-in the moment the session goes null; nothing else
    // to do here.
    await supabaseClient.auth.signOut();
  };

  return (
    <div className={Styles.shellStyles}>
      <div className={Styles.railStyles}>
        <div className={Styles.brandRowStyles}>
          <div className={Styles.brandMarkStyles}>
            <svg viewBox="0 0 48 48" width="15" height="15">
              <path d="M31.5 6 L40 6 L18.5 42 L10 42 Z" fill="currentColor" />
            </svg>
          </div>
          <span className={Styles.wordmarkStyles}>
            slash<span className={Styles.wordmarkDotStyles}>.</span>it
          </span>
        </div>
        <nav className={Styles.navStyles}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(Styles.navItemStyles, isActive && Styles.navItemOnStyles)
              }
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <Popover
          placement="top-start"
          containerClassName="mt-auto"
          trigger={({ isOpen, toggle }) => (
            <button
              type="button"
              onClick={toggle}
              aria-haspopup="menu"
              aria-expanded={isOpen}
              className={Styles.railFootStyles}
            >
              {isProfileLoading ? (
                <div className={Styles.avatarSkeletonStyles} />
              ) : avatarUrl !== null ? (
                <img src={avatarUrl} alt="" className={Styles.avatarImageStyles} />
              ) : (
                <div className={Styles.avatarStyles}>{avatarLetter}</div>
              )}
              <div className="min-w-0">
                {isProfileLoading ? (
                  <>
                    <div className={Styles.accountNameSkeletonStyles} />
                    <div className={Styles.accountEmailSkeletonStyles} />
                  </>
                ) : (
                  <>
                    <div className={Styles.accountNameStyles}>{displayName}</div>
                    <div className={Styles.accountEmailStyles}>{email ?? ""}</div>
                  </>
                )}
              </div>
            </button>
          )}
        >
          {({ close }) => (
            <>
              <Link to="/settings" onClick={close} className={Styles.accountMenuItemStyles}>
                <Settings size={16} />
                <span>Settings</span>
              </Link>
              <button
                type="button"
                onClick={() => void handleSignOut(close)}
                className={Styles.accountMenuItemStyles}
              >
                <LogOut size={16} />
                <span>Sign out</span>
              </button>
            </>
          )}
        </Popover>
      </div>
      <div className={Styles.mainStyles}>
        <OfflineBanner />
        <UpdateBanner />
        <Outlet />
        <Toast toast={store.toast.current} onDismiss={store.toast.dismiss} />
      </div>
      <NotificationsController />
      <InstallPrompt />
    </div>
  );
};

export default observer(AppShell);
