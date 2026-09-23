/**
 * Tells whoever listens that the WebSocket came back after a drop. Anything
 * pushed while it was down was missed, so the listener refetches what the
 * push would have updated (build plan §5: "client refetches the list and
 * count on every WebSocket reconnect").
 */
type ReconnectListener = () => void;

const listeners = new Set<ReconnectListener>();

export const onLiveReconnected = (listener: ReconnectListener): (() => void) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

export const announceLiveReconnected = (): void => {
  for (const listener of listeners) listener();
};
