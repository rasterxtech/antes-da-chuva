'use client';

import { useEffect, useRef, useState } from 'react';
import Menu from 'lucide-react/dist/esm/icons/menu.mjs';
import X from 'lucide-react/dist/esm/icons/x.mjs';

export function MobileNavigation() {
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      setOpen(false);
      trigger.current?.focus();
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [open]);
  return (
    <div
      className="lg:hidden"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <button
        ref={trigger}
        className="menu-trigger"
        type="button"
        aria-label={open ? 'Fechar navegação' : 'Abrir navegação'}
        aria-expanded={open}
        aria-controls="mobile-navigation"
        onClick={() => setOpen(!open)}
      >
        {open ? (
          <X aria-hidden="true" className="size-5" />
        ) : (
          <Menu aria-hidden="true" className="size-5" />
        )}
      </button>
      {open && (
        <nav
          id="mobile-navigation"
          aria-label="Navegação móvel"
          className="mobile-navigation"
        >
          {[
            ['#conteudo-principal', 'Buscar município'],
            ['#resultado', 'Leitura municipal'],
            ['#alertas', 'Alertas oficiais'],
            ['#metodologia', 'Metodologia'],
            ['#fontes', 'Fontes'],
          ].map(([href, label]) => (
            <a
              key={href}
              href={href}
              onClick={() => {
                setOpen(false);
                const target = document.querySelector<HTMLElement>(href);
                target?.focus({ preventScroll: true });
              }}
            >
              {label}
            </a>
          ))}
        </nav>
      )}
    </div>
  );
}
