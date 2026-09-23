import { Bell } from "lucide-react";
import type { ReactElement } from "react";

import * as Styles from "./styles";

interface NotificationBellProps {
  unreadCount: number;
  isOpen: boolean;
  onToggle: () => void;
}

/** FR-36: the unread count, wherever the user is. */
const NotificationBell = (props: NotificationBellProps): ReactElement => {
  const { unreadCount, isOpen, onToggle } = props;
  const label =
    unreadCount > 0 ? `Notifications, ${unreadCount} unread` : "Notifications, none unread";

  return (
    <button
      type="button"
      aria-label={label}
      aria-expanded={isOpen}
      className={Styles.bellButtonStyles}
      onClick={onToggle}
    >
      <Bell size={19} />
      {unreadCount > 0 && (
        <span className={Styles.bellBadgeStyles} aria-hidden="true">
          {unreadCount > 99 ? "99+" : unreadCount}
        </span>
      )}
    </button>
  );
};

export default NotificationBell;
