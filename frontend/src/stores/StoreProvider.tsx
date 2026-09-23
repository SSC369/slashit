import { createContext, useContext, useState, type ReactNode, type ReactElement } from "react";

import { RootStore } from "./RootStore";

const StoreContext = createContext<RootStore | null>(null);

interface StoreProviderProps {
  children: ReactNode;
  /** A test hands in its own store to read back what the page wrote. */
  store?: RootStore;
}

export const StoreProvider = (props: StoreProviderProps): ReactElement => {
  const { children, store: injectedStore } = props;
  const [store] = useState(() => injectedStore ?? new RootStore());

  return <StoreContext.Provider value={store}>{children}</StoreContext.Provider>;
};

export const useStore = (): RootStore => {
  const store = useContext(StoreContext);
  if (store === null) {
    throw new Error("useStore must be used within a StoreProvider");
  }
  return store;
};
