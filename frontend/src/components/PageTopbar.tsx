import { observer } from "mobx-react-lite";
import type { ReactElement, ReactNode } from "react";

import NotificationBell from "../features/notifications/components/NotificationBell";
import { useStore } from "../stores/StoreProvider";
import * as Styles from "./styles";

interface PageTopbarProps {
  title: string;
  /** Page-specific actions, left of the bell. */
  actions?: ReactNode;
}

/**
 * Every page's topbar (sub-plan 4.2, decision 3): the title and the bell. An
 * observer leaf that reads the notifications store itself, since every page
 * would otherwise thread the same count through.
 */
const PageTopbar = (props: PageTopbarProps): ReactElement => {
  const { title, actions } = props;
  const store = useStore();
  const { unreadCount, isPanelOpen, setPanelOpen } = store.notifications;

  return (
    <div className={Styles.pageTopbarStyles}>
      <div className={Styles.pageTopbarTitleStyles}>{title}</div>
      <div className={Styles.pageTopbarActionsStyles}>
        {actions}
        <NotificationBell
          unreadCount={unreadCount}
          isOpen={isPanelOpen}
          onToggle={() => setPanelOpen(!isPanelOpen)}
        />
      </div>
    </div>
  );
};

export default observer(PageTopbar);
