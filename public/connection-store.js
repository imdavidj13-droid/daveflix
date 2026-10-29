/* Credentials persist only when the user opts into trusting this browser. */
(function (root) {
  function create(local, session) {
    const name = 'daveflix-connection';
    const keys = ['daveflix-server', 'daveflix-key'];
    const get = (store, key) => { try { return store.getItem(key); } catch { return null; } };
    const remove = (store, key) => { try { store.removeItem(key); } catch {} };
    return {
      read() {
        for (const [store, remembered] of [[local, true], [session, false]]) {
          try {
            const value = JSON.parse(get(store, name));
            if (value && typeof value.url === 'string' && typeof value.key === 'string' && value.url && value.key)
              return { ...value, remembered };
          } catch {}
        }
        // Keep existing connected tabs working during the upgrade.
        const url = get(session, keys[0]), key = get(session, keys[1]);
        return url && key ? { url, key, remembered: false } : null;
      },
      clear() {
        for (const store of [local, session]) {
          remove(store, name);
          for (const key of keys) remove(store, key);
        }
      },
      save(url, key, remember) {
        this.clear();
        try {
          (remember ? local : session).setItem(name, JSON.stringify({ url, key }));
          return true;
        } catch { return false; }
      }
    };
  }
  root.DaveflixConnectionStore = create;
})(globalThis);
