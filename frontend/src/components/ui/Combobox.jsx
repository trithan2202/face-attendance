import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, Search, X } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * Select box you can type into to filter the options.
 *
 * `options` are `{ value, label, hint }`; `hint` is shown as a smaller second
 * line and is also searched, so an employee can be found by code or by name.
 */
const Combobox = ({
  label,
  error,
  options = [],
  value,
  onChange,
  placeholder = 'Nhập để tìm kiếm...',
  emptyMessage = 'Không tìm thấy kết quả',
  className,
}) => {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  const selected = options.find(option => String(option.value) === String(value));

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return options;
    return options.filter(option =>
      `${option.label} ${option.hint || ''}`.toLowerCase().includes(term)
    );
  }, [options, query]);

  // Close when clicking anywhere outside the field.
  useEffect(() => {
    const onClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
        setQuery('');
      }
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  useEffect(() => {
    setHighlight(0);
  }, [query, open]);

  const pick = (option) => {
    onChange(option.value);
    setOpen(false);
    setQuery('');
  };

  const handleKeyDown = (event) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (!open) { setOpen(true); return; }
      const step = event.key === 'ArrowDown' ? 1 : -1;
      setHighlight(current => {
        if (!filtered.length) return 0;
        return (current + step + filtered.length) % filtered.length;
      });
    } else if (event.key === 'Enter') {
      if (open && filtered[highlight]) {
        event.preventDefault();
        pick(filtered[highlight]);
      }
    } else if (event.key === 'Escape') {
      setOpen(false);
      setQuery('');
    }
  };

  return (
    <div className={cn('flex flex-col gap-1 w-full', className)} ref={containerRef}>
      {label && <label className="text-sm font-medium text-neutral-700">{label}</label>}

      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-neutral-400" />
        </div>

        <input
          ref={inputRef}
          type="text"
          autoComplete="off"
          className={cn(
            'flex w-full rounded-md border bg-white pl-9 pr-16 py-2 text-sm placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors',
            error ? 'border-danger-500 focus:ring-danger-500' : 'border-neutral-300'
          )}
          placeholder={selected ? selected.label : placeholder}
          value={open ? query : (selected ? selected.label : '')}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
        />

        <div className="absolute inset-y-0 right-0 flex items-center gap-1 pr-2">
          {selected && (
            <button
              type="button"
              onClick={() => { onChange(''); setQuery(''); inputRef.current?.focus(); }}
              className="text-neutral-400 hover:text-neutral-600 p-0.5"
              title="Xóa lựa chọn"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          <button
            type="button"
            onClick={() => { setOpen(!open); inputRef.current?.focus(); }}
            className="text-neutral-400 hover:text-neutral-600 p-0.5"
            tabIndex={-1}
          >
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>

        {open && (
          <div className="absolute z-50 mt-1 w-full max-h-60 overflow-y-auto rounded-md border border-neutral-200 bg-white shadow-lg">
            {filtered.length === 0 ? (
              <p className="px-3 py-3 text-sm text-neutral-500 text-center">{emptyMessage}</p>
            ) : (
              filtered.map((option, index) => {
                const isSelected = String(option.value) === String(value);
                return (
                  <button
                    key={option.value}
                    type="button"
                    onMouseEnter={() => setHighlight(index)}
                    onClick={() => pick(option)}
                    className={cn(
                      'w-full text-left px-3 py-2 text-sm transition-colors',
                      index === highlight ? 'bg-primary-50' : 'bg-white',
                      isSelected && 'font-medium text-primary-700'
                    )}
                  >
                    <span className="block">{option.label}</span>
                    {option.hint && (
                      <span className="block text-xs text-neutral-500">{option.hint}</span>
                    )}
                  </button>
                );
              })
            )}
          </div>
        )}
      </div>

      {error && <span className="text-xs text-danger-500">{error}</span>}
    </div>
  );
};

export default Combobox;
